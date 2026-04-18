from app.services.chat import ChatService, ConversationStore
from app.services.documents import DocumentRecord, DocumentRegistry
from app.services.embeddings import HashEmbeddingProvider
from app.services.generator import ExtractiveAnswerGenerator, FALLBACK_RESPONSE, HeuristicSummaryGenerator
from app.services.retrieval import ChunkRetrievalService
from app.services.vector_store import FaissVectorStore
from tests.test_retrieval import _build_document_record


def test_resume_summary_returns_resume_relevant_content(tmp_path) -> None:
    service = _build_summary_service(
        tmp_path,
        "candidate-resume.txt",
        [
            "\n".join(
                [
                    "Avery Stone",
                    "Senior Software Engineer",
                    "Skills: Python, FastAPI, React, AWS, PostgreSQL",
                    "Developed AI document workflows for enterprise onboarding.",
                    "Led platform reliability improvements across backend services.",
                    "Education: Bachelor of Technology in Computer Science",
                ]
            )
        ],
    )

    result = service.summarize_documents()

    assert "Senior Software Engineer" in result.answer
    assert "Python, FastAPI, React" in result.answer
    assert result.citations
    assert result.suggested_questions[0] == "What are the candidate's strongest skills?"


def test_summary_falls_back_without_documents(tmp_path) -> None:
    registry = DocumentRegistry()
    retrieval_service = ChunkRetrievalService(
        registry=registry,
        embedding_provider=HashEmbeddingProvider(dimensions=32),
        vector_store=FaissVectorStore(tmp_path),
    )
    service = ChatService(
        document_registry=registry,
        retrieval_service=retrieval_service,
        answer_generator=ExtractiveAnswerGenerator(),
        summary_generator=HeuristicSummaryGenerator(),
        conversation_store=ConversationStore(),
        default_top_k=5,
    )

    result = service.summarize_documents()

    assert result.answer == FALLBACK_RESPONSE
    assert result.citations == []
    assert result.suggested_questions == []


def _build_summary_service(tmp_path, filename: str, chunk_texts: list[str]) -> ChatService:
    registry_record = _build_document_record("doc-1", filename, chunk_texts)
    registry = _single_record_registry(registry_record)
    retrieval_service = ChunkRetrievalService(
        registry=registry,
        embedding_provider=HashEmbeddingProvider(dimensions=32),
        vector_store=FaissVectorStore(tmp_path),
    )
    return ChatService(
        document_registry=registry,
        retrieval_service=retrieval_service,
        answer_generator=ExtractiveAnswerGenerator(),
        summary_generator=HeuristicSummaryGenerator(),
        conversation_store=ConversationStore(),
        default_top_k=5,
    )


def _single_record_registry(record: DocumentRecord) -> DocumentRegistry:
    registry = DocumentRegistry()
    registry.add(record)
    return registry
