from dataclasses import dataclass

from app.models.schemas import ServiceStatus
from app.services.chat import ChatService, ConversationStore
from app.services.documents import DocumentRegistry
from app.services.embeddings import EmbeddingProvider, build_embedding_provider
from app.services.generator import AnswerGenerator, build_answer_generator
from app.services.ingestion import LocalDocumentIngestionService
from app.services.retrieval import ChunkRetrievalService
from app.services.vector_store import FaissVectorStore
from app.utils.config import Settings


@dataclass
class AppState:
    settings: Settings
    document_registry: DocumentRegistry
    ingestion_service: LocalDocumentIngestionService
    embedding_provider: EmbeddingProvider
    retrieval_service: ChunkRetrievalService
    vector_store: FaissVectorStore
    answer_generator: AnswerGenerator
    conversation_store: ConversationStore
    chat_service: ChatService

    @classmethod
    def initialize(cls, settings: Settings) -> "AppState":
        document_registry = DocumentRegistry()
        ingestion_service = LocalDocumentIngestionService(document_registry, settings.upload_dir)
        embedding_provider = build_embedding_provider(settings)
        vector_store = FaissVectorStore(settings.vector_index_dir)
        retrieval_service = ChunkRetrievalService(document_registry, embedding_provider, vector_store)
        answer_generator = build_answer_generator()
        conversation_store = ConversationStore()
        chat_service = ChatService(
            retrieval_service=retrieval_service,
            answer_generator=answer_generator,
            conversation_store=conversation_store,
            default_top_k=settings.default_top_k,
            minimum_grounding_score=settings.minimum_grounding_score,
        )
        return cls(
            settings=settings,
            document_registry=document_registry,
            ingestion_service=ingestion_service,
            embedding_provider=embedding_provider,
            retrieval_service=retrieval_service,
            vector_store=vector_store,
            answer_generator=answer_generator,
            conversation_store=conversation_store,
            chat_service=chat_service,
        )

    def describe_services(self) -> list[ServiceStatus]:
        return [
            ServiceStatus(name="llm", configured=bool(self.settings.openai_api_key), provider=self.settings.llm_provider),
            ServiceStatus(name="embeddings", configured=True, provider=self.settings.embedding_provider),
            ServiceStatus(name="vector_store", configured=True, provider=self.settings.vector_store_provider),
            ServiceStatus(name="document_registry", configured=True, provider="in-memory"),
            ServiceStatus(name="ingestion", configured=True, provider="local"),
            ServiceStatus(name="evaluation_logging", configured=True, provider="jsonl"),
        ]
