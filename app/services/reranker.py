from __future__ import annotations

from dataclasses import dataclass
from math import exp
from typing import Protocol

from app.services.vector_store import VectorSearchMatch
from app.utils.config import Settings
from app.utils.logging import get_logger


class Reranker(Protocol):
    def rerank(self, *, query: str, matches: list[VectorSearchMatch], top_k: int) -> list[VectorSearchMatch]:
        """Return reranked matches for the query."""


class NoOpReranker:
    def rerank(self, *, query: str, matches: list[VectorSearchMatch], top_k: int) -> list[VectorSearchMatch]:
        del query
        return matches[:top_k]


@dataclass
class SentenceTransformerReranker:
    model_name: str
    fallback_reranker: Reranker | None = None

    def __post_init__(self) -> None:
        self._model = None
        self._fallback_reranker = self.fallback_reranker or NoOpReranker()
        self._logger = get_logger(component="reranker", provider="cross-encoder", model_name=self.model_name)
        self._fallback_active = False

    def rerank(self, *, query: str, matches: list[VectorSearchMatch], top_k: int) -> list[VectorSearchMatch]:
        if not matches:
            return []
        if self._fallback_active:
            return self._fallback_reranker.rerank(query=query, matches=matches, top_k=top_k)

        try:
            model = self._get_model()
            pairs = [[query, match.chunk.text] for match in matches]
            raw_scores = model.predict(pairs)
            rescored = [
                VectorSearchMatch(chunk=match.chunk, score=_sigmoid(float(score)))
                for match, score in zip(matches, raw_scores)
            ]
            rescored.sort(key=lambda item: item.score, reverse=True)
            return rescored[:top_k]
        except Exception as exc:
            self._fallback_active = True
            self._logger.warning(
                "reranker_provider_fallback",
                reason=str(exc),
                fallback_provider="noop",
            )
            return self._fallback_reranker.rerank(query=query, matches=matches, top_k=top_k)

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name)
        return self._model


def build_reranker(settings: Settings) -> Reranker:
    if settings.reranker_provider == "none":
        return NoOpReranker()
    if settings.reranker_provider == "sentence-transformers":
        return SentenceTransformerReranker(settings.reranker_model)
    raise ValueError(f"Unsupported reranker provider: {settings.reranker_provider}")


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + exp(-value))
