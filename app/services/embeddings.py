from __future__ import annotations

from collections import Counter
from hashlib import sha256
from math import sqrt
from typing import Protocol

from app.utils.config import Settings
from app.utils.logging import get_logger


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return vector representations for a list of texts."""


class SentenceTransformerEmbeddingProvider:
    def __init__(self, model_name: str, fallback_provider: EmbeddingProvider | None = None) -> None:
        self._model_name = model_name
        self._model = None
        self._fallback_provider = fallback_provider or HashEmbeddingProvider()
        self._logger = get_logger(component="embeddings", provider="sentence-transformers", model_name=model_name)
        self._fallback_active = False

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self._fallback_active:
            return self._fallback_provider.embed(texts)
        try:
            model = self._get_model()
            vectors = model.encode(texts, normalize_embeddings=True)
            return [list(map(float, vector)) for vector in vectors]
        except Exception as exc:
            self._fallback_active = True
            self._logger.warning(
                "embedding_provider_fallback",
                reason=str(exc),
                fallback_provider="hash",
            )
            return self._fallback_provider.embed(texts)

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name)
        return self._model


class HashEmbeddingProvider:
    def __init__(self, dimensions: int = 64) -> None:
        self._dimensions = dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_text(text) for text in texts]

    def _embed_text(self, text: str) -> list[float]:
        counts = Counter(token for token in text.lower().split() if token)
        vector = [0.0] * self._dimensions

        for token, count in counts.items():
            bucket = int.from_bytes(sha256(token.encode("utf-8")).digest()[:4], "big") % self._dimensions
            vector[bucket] += float(count)

        norm = sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    if settings.embedding_provider == "sentence-transformers":
        return SentenceTransformerEmbeddingProvider(
            settings.embedding_model,
            fallback_provider=HashEmbeddingProvider(),
        )
    if settings.embedding_provider == "hash":
        return HashEmbeddingProvider()
    raise ValueError(f"Unsupported embedding provider: {settings.embedding_provider}")
