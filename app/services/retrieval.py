from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.services.documents import DocumentChunk, DocumentRegistry
from app.services.embeddings import EmbeddingProvider
from app.services.vector_store import IndexNotReadyError, VectorSearchMatch, VectorStore
from app.utils.logging import get_logger


class RetrievalService(Protocol):
    def index_documents(self, document_ids: list[str] | None = None) -> list[DocumentChunk]:
        """Index chunks for the selected documents."""

    def retrieve(self, query: str, top_k: int) -> list[VectorSearchMatch]:
        """Return ranked chunk candidates for the given query."""


@dataclass
class ChunkRetrievalService:
    registry: DocumentRegistry
    embedding_provider: EmbeddingProvider
    vector_store: VectorStore

    def __post_init__(self) -> None:
        self._logger = get_logger(component="retrieval")

    def index_documents(self, document_ids: list[str] | None = None) -> list[DocumentChunk]:
        documents = self.registry.list()
        if document_ids is not None:
            allowed = set(document_ids)
            documents = [document for document in documents if document.document_id in allowed]

        chunks = [chunk for document in documents for chunk in document.chunks]
        if not chunks:
            raise ValueError("No document chunks available for indexing.")

        vectors = self.embedding_provider.embed([chunk.text for chunk in chunks])
        self.vector_store.index(chunks, vectors)
        self._logger.info(
            "chunks_indexed",
            document_count=len(documents),
            chunk_count=len(chunks),
            filtered=bool(document_ids),
        )
        return chunks

    def retrieve(self, query: str, top_k: int) -> list[VectorSearchMatch]:
        if not self.vector_store.is_ready():
            raise IndexNotReadyError("Vector index is not ready. Index documents before searching.")

        query_vector = self.embedding_provider.embed([query])[0]
        matches = self.vector_store.search(query_vector, top_k)
        self._logger.info(
            "retrieval_completed",
            query=query,
            top_k=top_k,
            match_count=len(matches),
            top_score=round(matches[0].score, 4) if matches else None,
        )
        return matches
