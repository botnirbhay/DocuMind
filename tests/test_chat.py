from app.services.chat import ChatService, ConversationStore
from app.services.documents import DocumentRecord, DocumentRegistry
from app.services.embeddings import HashEmbeddingProvider
from app.services.generator import ExtractiveAnswerGenerator, FALLBACK_RESPONSE, HeuristicSummaryGenerator
from app.services.reranker import NoOpReranker
from app.services.retrieval import ChunkRetrievalService
from app.services.vector_store import FaissVectorStore
from app.services.vector_store import IndexNotReadyError
from tests.test_retrieval import _build_document_record


def test_grounded_answer_generation_returns_supported_sentence(tmp_path) -> None:
    service = _build_chat_service(
        tmp_path=tmp_path,
        chunk_texts=["DocuMind supports PDF, DOCX, and TXT uploads."],
    )
    service.retrieval_service.index_documents()

    result = service.query(session_id="session-1", user_query="What uploads does DocuMind support?", top_k=1)

    assert "PDF, DOCX, and TXT" in result.answer
    assert len(result.citations) == 1
    assert result.citations[0].chunk.filename == "doc.txt"
    assert result.confidence_score > 0


def test_fallback_behavior_when_context_is_insufficient(tmp_path) -> None:
    service = _build_chat_service(
        tmp_path=tmp_path,
        chunk_texts=["DocuMind supports PDF uploads."],
    )
    service.retrieval_service.index_documents()

    result = service.query(session_id="session-1", user_query="What is the company revenue?", top_k=1)

    assert result.answer == FALLBACK_RESPONSE
    assert result.citations == []
    assert result.retrieved_chunks == []
    assert result.confidence_score <= service.minimum_grounding_score


def test_chat_service_requires_index_before_query(tmp_path) -> None:
    service = _build_chat_service(
        tmp_path=tmp_path,
        chunk_texts=["DocuMind supports PDF uploads."],
    )

    try:
        service.query(session_id="session-1", user_query="What uploads are supported?", top_k=1)
    except IndexNotReadyError as exc:
        assert "Vector index is not ready" in str(exc)
    else:
        raise AssertionError("Expected IndexNotReadyError")


def _build_chat_service(tmp_path, chunk_texts: list[str]) -> ChatService:
    registry_record = _build_document_record("doc-1", "doc.txt", chunk_texts)
    registry = _single_record_registry(registry_record)
    retrieval_service = ChunkRetrievalService(
        registry=registry,
        embedding_provider=HashEmbeddingProvider(dimensions=32),
        vector_store=FaissVectorStore(tmp_path),
        reranker=NoOpReranker(),
    )
    return ChatService(
        document_registry=registry,
        retrieval_service=retrieval_service,
        answer_generator=ExtractiveAnswerGenerator(),
        summary_generator=HeuristicSummaryGenerator(),
        conversation_store=ConversationStore(),
        default_top_k=5,
        minimum_grounding_score=0.2,
    )


def _single_record_registry(record: DocumentRecord) -> DocumentRegistry:
    registry = DocumentRegistry()
    registry.add(record)
    return registry
