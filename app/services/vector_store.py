from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Protocol

import faiss
import numpy as np

from app.services.documents import DocumentChunk
from app.utils.logging import get_logger


@dataclass(slots=True)
class VectorSearchMatch:
    chunk: DocumentChunk
    score: float


class VectorStore(Protocol):
    def index(self, chunks: list[DocumentChunk], vectors: list[list[float]]) -> int:
        """Create or replace the vector index for the provided chunks."""

    def search(self, vector: list[float], top_k: int) -> list[VectorSearchMatch]:
        """Return ranked vector matches."""

    def is_ready(self) -> bool:
        """Return whether the vector index contains searchable entries."""


class IndexNotReadyError(Exception):
    pass


class FaissVectorStore:
    def __init__(self, index_dir: Path) -> None:
        self._index_dir = index_dir
        self._index_path = index_dir / "chunks.faiss"
        self._metadata_path = index_dir / "chunks.json"
        self._index: faiss.IndexFlatIP | None = None
        self._chunks: list[DocumentChunk] = []
        self._logger = get_logger(component="vector_store", provider="faiss")

    def index(self, chunks: list[DocumentChunk], vectors: list[list[float]]) -> int:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")
        if not chunks:
            raise ValueError("No chunks available for indexing.")

        start = perf_counter()
        matrix = np.asarray(vectors, dtype="float32")
        if matrix.ndim != 2:
            raise ValueError("Embedding matrix must be two-dimensional.")

        self._index = faiss.IndexFlatIP(matrix.shape[1])
        self._index.add(matrix)
        self._chunks = list(chunks)
        self._persist()
        self._logger.info(
            "vector_index_updated",
            chunk_count=len(chunks),
            dimensions=matrix.shape[1],
            duration_ms=round((perf_counter() - start) * 1000, 2),
        )
        return len(chunks)

    def search(self, vector: list[float], top_k: int) -> list[VectorSearchMatch]:
        if not self.is_ready():
            raise IndexNotReadyError("Vector index has not been built yet.")

        start = perf_counter()
        query = np.asarray([vector], dtype="float32")
        scores, indices = self._index.search(query, top_k)
        matches: list[VectorSearchMatch] = []

        for score, index in zip(scores[0], indices[0]):
            if index < 0:
                continue
            matches.append(VectorSearchMatch(chunk=self._chunks[index], score=float(score)))

        self._logger.info(
            "vector_search_completed",
            top_k=top_k,
            match_count=len(matches),
            duration_ms=round((perf_counter() - start) * 1000, 2),
        )
        return matches

    def is_ready(self) -> bool:
        return self._index is not None and self._index.ntotal > 0

    def _persist(self) -> None:
        self._index_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(self._index_path))
        self._metadata_path.write_text(
            json.dumps([asdict(chunk) for chunk in self._chunks], indent=2),
            encoding="utf-8",
        )
