from app.services.documents import DocumentChunk, DocumentRecord, DocumentRegistry, DocumentSection
from app.services.embeddings import HashEmbeddingProvider
from app.services.reranker import NoOpReranker
from app.services.retrieval import ChunkRetrievalService
from app.services.vector_store import FaissVectorStore, IndexNotReadyError, VectorSearchMatch


def test_vector_index_creation_and_search(tmp_path) -> None:
    registry = DocumentRegistry()
    record = _build_document_record(
        document_id="doc-1",
        filename="plan.txt",
        chunk_texts=["cats like naps", "dogs like parks"],
    )
    registry.add(record)

    service = ChunkRetrievalService(
        registry=registry,
        embedding_provider=HashEmbeddingProvider(dimensions=32),
        vector_store=FaissVectorStore(tmp_path),
        reranker=NoOpReranker(),
    )

    indexed_chunks = service.index_documents()
    matches = service.retrieve("cats", top_k=1)

    assert len(indexed_chunks) == 2
    assert matches[0].chunk.text == "cats like naps"
    assert (tmp_path / "chunks.faiss").exists()
    assert (tmp_path / "chunks.json").exists()


def test_indexing_chunks_returns_all_selected_documents(tmp_path) -> None:
    registry = DocumentRegistry()
    registry.add(_build_document_record("doc-1", "one.txt", ["alpha"]))
    registry.add(_build_document_record("doc-2", "two.txt", ["beta", "gamma"]))

    service = ChunkRetrievalService(
        registry=registry,
        embedding_provider=HashEmbeddingProvider(dimensions=32),
        vector_store=FaissVectorStore(tmp_path),
        reranker=NoOpReranker(),
    )

    indexed_chunks = service.index_documents(["doc-2"])

    assert [chunk.document_id for chunk in indexed_chunks] == ["doc-2", "doc-2"]


def test_empty_index_behavior_raises_clear_error(tmp_path) -> None:
    service = ChunkRetrievalService(
        registry=DocumentRegistry(),
        embedding_provider=HashEmbeddingProvider(dimensions=32),
        vector_store=FaissVectorStore(tmp_path),
        reranker=NoOpReranker(),
    )

    try:
        service.retrieve("anything", top_k=1)
    except IndexNotReadyError as exc:
        assert "Vector index is not ready" in str(exc)
    else:
        raise AssertionError("Expected IndexNotReadyError")


def test_hybrid_reranking_recovers_exact_keyword_match(tmp_path) -> None:
    registry = DocumentRegistry()
    registry.add(
        _build_document_record(
            "doc-1",
            "guide.txt",
            [
                "This section describes general onboarding guidance.",
                "The appeal review timeline is seven business days.",
                "This section covers office etiquette and formatting.",
            ],
        )
    )

    service = ChunkRetrievalService(
        registry=registry,
        embedding_provider=ConstantEmbeddingProvider(),
        vector_store=FaissVectorStore(tmp_path),
        reranker=NoOpReranker(),
    )

    service.index_documents()
    matches = service.retrieve("appeal review timeline", top_k=1)

    assert matches[0].chunk.text == "The appeal review timeline is seven business days."
    assert matches[0].score > 0


def test_retrieval_service_uses_second_stage_reranker(tmp_path) -> None:
    registry = DocumentRegistry()
    registry.add(_build_document_record("doc-1", "guide.txt", ["alpha clause", "beta clause"]))

    service = ChunkRetrievalService(
        registry=registry,
        embedding_provider=ConstantEmbeddingProvider(),
        vector_store=FaissVectorStore(tmp_path),
        reranker=ReverseOrderReranker(),
    )

    service.index_documents()
    matches = service.retrieve("alpha", top_k=1)

    assert matches[0].chunk.text == "beta clause"


def _build_document_record(document_id: str, filename: str, chunk_texts: list[str]) -> DocumentRecord:
    chunks = [
        DocumentChunk(
            chunk_id=f"{document_id}-chunk-{index:04d}",
            document_id=document_id,
            filename=filename,
            file_type="txt",
            upload_timestamp="2026-04-18T00:00:00+00:00",
            chunk_index=index,
            text=text,
            page_number=None,
            preview=text,
        )
        for index, text in enumerate(chunk_texts)
    ]
    return DocumentRecord(
        document_id=document_id,
        filename=filename,
        file_type="txt",
        upload_timestamp="2026-04-18T00:00:00+00:00",
        sections=[DocumentSection(text="\n\n".join(chunk_texts), page_number=None)],
        chunks=chunks,
        status="ingested",
        stored_path=None,
    )


class ConstantEmbeddingProvider:
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0, 0.0, 0.0] for _ in texts]


class ReverseOrderReranker:
    def rerank(self, *, query: str, matches: list[VectorSearchMatch], top_k: int) -> list[VectorSearchMatch]:
        del query
        return list(reversed(matches))[:top_k]
