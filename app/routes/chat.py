from fastapi import APIRouter, HTTPException, Request, status

from app.models.schemas import (
    ChatQueryRequest,
    ChatQueryResponse,
    CitationResponse,
    DocumentSummaryRequest,
    DocumentSummaryResponse,
    RetrievalMatchResponse,
)
from app.services.vector_store import IndexNotReadyError
from app.utils.logging import get_logger

router = APIRouter(prefix="/chat", tags=["chat"])
logger = get_logger(component="chat_route")


@router.post("/query", response_model=ChatQueryResponse, status_code=status.HTTP_200_OK)
async def query_documents(request: Request, payload: ChatQueryRequest) -> ChatQueryResponse:
    container = request.app.state.container
    logger.info("chat_request_received", session_id=payload.session_id, top_k=payload.top_k)
    try:
        result = container.chat_service.query(
            session_id=payload.session_id,
            user_query=payload.user_query,
            top_k=payload.top_k,
        )
    except IndexNotReadyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ChatQueryResponse(
        session_id=result.session_id,
        answer=result.answer,
        confidence_score=result.confidence_score,
        citations=[
            CitationResponse(
                chunk_id=match.chunk.chunk_id,
                chunk_index=match.chunk.chunk_index,
                document_id=match.chunk.document_id,
                filename=match.chunk.filename,
                page_number=match.chunk.page_number,
                snippet=match.chunk.preview,
                score=match.score,
            )
            for match in result.citations
        ],
        retrieved_chunks=[
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
            for match in result.retrieved_chunks
        ],
    )


@router.post("/summary", response_model=DocumentSummaryResponse, status_code=status.HTTP_200_OK)
async def summarize_documents(request: Request, payload: DocumentSummaryRequest) -> DocumentSummaryResponse:
    container = request.app.state.container
    logger.info("summary_request_received", document_ids=payload.document_ids)
    result = container.chat_service.summarize_documents(document_ids=payload.document_ids)

    return DocumentSummaryResponse(
        answer=result.answer,
        confidence_score=result.confidence_score,
        citations=[
            CitationResponse(
                chunk_id=match.chunk.chunk_id,
                chunk_index=match.chunk.chunk_index,
                document_id=match.chunk.document_id,
                filename=match.chunk.filename,
                page_number=match.chunk.page_number,
                snippet=match.chunk.preview,
                score=match.score,
            )
            for match in result.citations
        ],
        retrieved_chunks=[
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
            for match in result.retrieved_chunks
        ],
        suggested_questions=result.suggested_questions,
    )
