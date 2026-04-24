from dataclasses import dataclass
from pathlib import Path

from app.models.schemas import ServiceStatus
from app.services.chat import ChatService, ConversationStore
from app.services.documents import DocumentRegistry
from app.services.embeddings import EmbeddingProvider, build_embedding_provider
from app.services.generator import AnswerGenerator, SummaryGenerator, build_answer_generator, build_summary_generator
from app.services.ingestion import LocalDocumentIngestionService
from app.services.reranker import Reranker, build_reranker
from app.services.retrieval import ChunkRetrievalService
from app.services.vector_store import FaissVectorStore
from app.utils.config import Settings


@dataclass
class AppState:
    settings: Settings
    document_registry: DocumentRegistry
    ingestion_service: LocalDocumentIngestionService
    embedding_provider: EmbeddingProvider
    reranker: Reranker
    retrieval_service: ChunkRetrievalService
    vector_store: FaissVectorStore
    answer_generator: AnswerGenerator
    summary_generator: SummaryGenerator
    conversation_store: ConversationStore
    chat_service: ChatService

    @classmethod
    def initialize(cls, settings: Settings) -> "AppState":
        document_registry = DocumentRegistry()
        ingestion_service = LocalDocumentIngestionService(document_registry, settings.upload_dir)
        embedding_provider = build_embedding_provider(settings)
        reranker = build_reranker(settings)
        vector_store = FaissVectorStore(settings.vector_index_dir)
        retrieval_service = ChunkRetrievalService(document_registry, embedding_provider, vector_store, reranker)
        answer_generator = build_answer_generator(settings)
        summary_generator = build_summary_generator(settings)
        conversation_store = ConversationStore()
        chat_service = ChatService(
            document_registry=document_registry,
            retrieval_service=retrieval_service,
            answer_generator=answer_generator,
            summary_generator=summary_generator,
            conversation_store=conversation_store,
            default_top_k=settings.default_top_k,
            minimum_grounding_score=settings.minimum_grounding_score,
        )
        return cls(
            settings=settings,
            document_registry=document_registry,
            ingestion_service=ingestion_service,
            embedding_provider=embedding_provider,
            reranker=reranker,
            retrieval_service=retrieval_service,
            vector_store=vector_store,
            answer_generator=answer_generator,
            summary_generator=summary_generator,
            conversation_store=conversation_store,
            chat_service=chat_service,
        )

    def describe_services(self) -> list[ServiceStatus]:
        llm_provider = self.settings.llm_provider
        llm_configured = True
        if llm_provider == "ollama":
            llm_configured = bool(self.settings.ollama_base_url and self.settings.ollama_model)
            llm_provider = f"ollama:{self.settings.ollama_model}"
        return [
            ServiceStatus(name="llm", configured=llm_configured, provider=llm_provider),
            ServiceStatus(name="embeddings", configured=True, provider=self.settings.embedding_provider),
            ServiceStatus(name="reranker", configured=True, provider=self.settings.reranker_provider),
            ServiceStatus(name="vector_store", configured=True, provider=self.settings.vector_store_provider),
            ServiceStatus(name="document_registry", configured=True, provider="in-memory"),
            ServiceStatus(name="ingestion", configured=True, provider="local"),
            ServiceStatus(name="evaluation_logging", configured=True, provider="jsonl"),
        ]

    def reset_runtime_state(self) -> dict[str, int]:
        document_count = self.document_registry.clear()
        conversation_count = self.conversation_store.clear()
        self.vector_store.reset()
        upload_file_count = _clear_directory(self.settings.upload_dir)
        return {
            "documents_cleared": document_count,
            "sessions_cleared": conversation_count,
            "uploaded_files_removed": upload_file_count,
        }

    def remove_document(self, document_id: str) -> dict[str, int | str]:
        document = self.document_registry.remove(document_id)
        if document is None:
            raise ValueError(f"Document '{document_id}' was not found.")

        conversation_count = self.conversation_store.clear()
        removed_file = _remove_file(document.stored_path)

        remaining_documents = self.document_registry.list()
        if remaining_documents:
            indexed_chunks = len(self.retrieval_service.index_documents())
        else:
            self.vector_store.reset()
            indexed_chunks = 0

        return {
            "document_id": document_id,
            "documents_remaining": len(remaining_documents),
            "total_chunks_indexed": indexed_chunks,
            "sessions_cleared": conversation_count,
            "uploaded_files_removed": removed_file,
        }


def _clear_directory(directory: Path) -> int:
    if not directory.exists():
        return 0
    removed = 0
    for path in directory.iterdir():
        if path.is_file():
            path.unlink()
            removed += 1
    return removed


def _remove_file(path_value: str | None) -> int:
    if not path_value:
        return 0

    path = Path(path_value)
    if path.exists() and path.is_file():
        path.unlink()
        return 1
    return 0
