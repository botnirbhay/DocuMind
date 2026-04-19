from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Protocol

from app.services.documents import DocumentChunk, DocumentRegistry
from app.services.embeddings import EmbeddingProvider
from app.services.vector_store import IndexNotReadyError, VectorSearchMatch, VectorStore
from app.utils.logging import get_logger

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


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
    candidate_multiplier: int = 4
    vector_weight: float = 0.7
    lexical_weight: float = 0.3

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
        dense_limit = max(top_k, top_k * self.candidate_multiplier)
        dense_matches = self.vector_store.search(query_vector, dense_limit)
        matches = self._rerank_matches(query, dense_matches, top_k)
        self._logger.info(
            "retrieval_completed",
            query=query,
            top_k=top_k,
            dense_candidates=len(dense_matches),
            match_count=len(matches),
            top_score=round(matches[0].score, 4) if matches else None,
            vector_weight=self.vector_weight,
            lexical_weight=self.lexical_weight,
        )
        return matches

    def _rerank_matches(
        self,
        query: str,
        dense_matches: list[VectorSearchMatch],
        top_k: int,
    ) -> list[VectorSearchMatch]:
        all_chunks = self.registry.get_chunks()
        if not dense_matches and not all_chunks:
            return []

        query_terms = _tokenize(query)
        max_dense_score = max(max(match.score, 0.0) for match in dense_matches) or 1.0
        dense_lookup = {match.chunk.chunk_id: match for match in dense_matches}
        lexical_candidates = sorted(
            all_chunks,
            key=lambda chunk: _lexical_score(query, query_terms, chunk),
            reverse=True,
        )[: max(top_k, top_k * self.candidate_multiplier)]
        candidate_chunks = {chunk.chunk_id: chunk for chunk in lexical_candidates}
        candidate_chunks.update({match.chunk.chunk_id: match.chunk for match in dense_matches})
        rescored: list[VectorSearchMatch] = []

        for chunk in candidate_chunks.values():
            dense_match = dense_lookup.get(chunk.chunk_id)
            dense_score = 0.0 if dense_match is None else max(dense_match.score, 0.0) / max_dense_score
            lexical_score = _lexical_score(query, query_terms, chunk)
            blended_score = (dense_score * self.vector_weight) + (lexical_score * self.lexical_weight)
            rescored.append(VectorSearchMatch(chunk=chunk, score=blended_score))

        rescored.sort(
            key=lambda item: (
                item.score,
                _lexical_score(query, query_terms, item.chunk),
                -item.chunk.chunk_index,
            ),
            reverse=True,
        )
        return rescored[:top_k]


def _lexical_score(query: str, query_terms: set[str], chunk: DocumentChunk) -> float:
    if not query_terms:
        return 0.0

    chunk_terms = _tokenize(chunk.text)
    if not chunk_terms:
        return 0.0

    overlap = len(query_terms & chunk_terms) / len(query_terms)
    normalized_chunk = " ".join(TOKEN_PATTERN.findall(chunk.text.lower()))
    normalized_query = " ".join(TOKEN_PATTERN.findall(query.lower()))
    exact_phrase_bonus = 0.12 if normalized_query and normalized_query in normalized_chunk else 0.0
    preview_terms = _tokenize(chunk.preview)
    preview_bonus = 0.08 if len(query_terms & preview_terms) == len(query_terms) else 0.0
    return min(1.0, overlap + exact_phrase_bonus + preview_bonus)


def _tokenize(text: str) -> set[str]:
    return {token for token in TOKEN_PATTERN.findall(text.lower()) if token}
