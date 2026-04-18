from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status

from app.models.schemas import (
    DocumentIndexRequest,
    DocumentIndexResponse,
    DocumentUploadResponse,
    IndexedDocumentResponse,
    ResetWorkspaceResponse,
    RetrievalMatchResponse,
    RetrievalSearchRequest,
    RetrievalSearchResponse,
    UploadedDocumentResponse,
)
from app.services.chunking import ChunkingStrategy
from app.services.ingestion import (
    DocumentReadError,
    EmptyDocumentError,
    IngestionError,
    UnsupportedFileTypeError,
)
from app.services.vector_store import IndexNotReadyError
from app.utils.logging import get_logger

router = APIRouter(prefix="/documents", tags=["documents"])
logger = get_logger(component="documents_route")


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_documents(
    request: Request,
    files: list[UploadFile] | None = File(default=None),
    chunking_strategy: ChunkingStrategy = Form(default=ChunkingStrategy.RECURSIVE),
    chunk_size: int | None = Form(default=None),
    chunk_overlap: int | None = Form(default=None),
) -> DocumentUploadResponse:
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one file must be uploaded.")

    container = request.app.state.container
    resolved_chunk_size = chunk_size if chunk_size is not None else container.settings.default_chunk_size
    resolved_chunk_overlap = chunk_overlap if chunk_overlap is not None else container.settings.default_chunk_overlap

    documents: list[UploadedDocumentResponse] = []
    logger.info(
        "upload_request_received",
        file_count=len(files),
        chunking_strategy=str(chunking_strategy),
        chunk_size=resolved_chunk_size,
        chunk_overlap=resolved_chunk_overlap,
    )
    for upload in files:
        if not upload.filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is missing a filename.")

        content = await upload.read()
        try:
            record = container.ingestion_service.ingest(
                filename=upload.filename,
                content=content,
                strategy=chunking_strategy,
                chunk_size=resolved_chunk_size,
                chunk_overlap=resolved_chunk_overlap,
            )
        except UnsupportedFileTypeError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        except (DocumentReadError, EmptyDocumentError, ValueError) as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        except IngestionError as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

        documents.append(
            UploadedDocumentResponse(
                document_id=record.document_id,
                filename=record.filename,
                file_type=record.file_type,
                chunks_extracted=len(record.chunks),
                status=record.status,
            )
        )

    return DocumentUploadResponse(documents=documents)


@router.post("/reset", response_model=ResetWorkspaceResponse)
async def reset_documents(request: Request) -> ResetWorkspaceResponse:
    container = request.app.state.container
    result = container.reset_runtime_state()
    logger.info("workspace_reset_completed", **result)
    return ResetWorkspaceResponse(
        status="reset",
        detail="Document registry, vector index, and conversation state were cleared.",
        documents_cleared=result["documents_cleared"],
        sessions_cleared=result["sessions_cleared"],
        uploaded_files_removed=result["uploaded_files_removed"],
    )


@router.post("/index", response_model=DocumentIndexResponse)
async def index_documents(request: Request, payload: DocumentIndexRequest) -> DocumentIndexResponse:
    container = request.app.state.container
    logger.info("index_request_received", document_ids=payload.document_ids)
    try:
        chunks = container.retrieval_service.index_documents(payload.document_ids)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    indexed_documents: dict[str, IndexedDocumentResponse] = {}
    for chunk in chunks:
        if chunk.document_id not in indexed_documents:
            indexed_documents[chunk.document_id] = IndexedDocumentResponse(
                document_id=chunk.document_id,
                filename=chunk.filename,
                chunks_indexed=0,
            )
        indexed_documents[chunk.document_id].chunks_indexed += 1

    return DocumentIndexResponse(
        status="indexed",
        indexed_documents=list(indexed_documents.values()),
        total_chunks_indexed=len(chunks),
    )


@router.post("/search", response_model=RetrievalSearchResponse)
async def search_documents(request: Request, payload: RetrievalSearchRequest) -> RetrievalSearchResponse:
    container = request.app.state.container
    logger.info("search_request_received", query=payload.query, top_k=payload.top_k)
    try:
        matches = container.retrieval_service.retrieve(payload.query, payload.top_k)
    except IndexNotReadyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return RetrievalSearchResponse(
        query=payload.query,
        top_k=payload.top_k,
        matches=[
            RetrievalMatchResponse(
                chunk_id=match.chunk.chunk_id,
                chunk_index=match.chunk.chunk_index,
                document_id=match.chunk.document_id,
                filename=match.chunk.filename,
                page_number=match.chunk.page_number,
                score=match.score,
                text=match.chunk.text,
                preview=match.chunk.preview,
            )
            for match in matches
        ],
    )
