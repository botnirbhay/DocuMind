from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from app.services.vector_store import VectorSearchMatch

FALLBACK_RESPONSE = "I dont have enough information from the provided documents."
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


@dataclass(slots=True)
class GeneratedAnswer:
    answer: str
    cited_chunk_ids: list[str]
    used_fallback: bool = False


class AnswerGenerator(Protocol):
    def generate(
        self,
        *,
        question: str,
        context: list[VectorSearchMatch],
        chat_history: list[dict[str, str]],
    ) -> GeneratedAnswer:
        """Return a grounded answer built only from retrieved context."""


class ExtractiveAnswerGenerator:
    def __init__(self, max_sentences: int = 2) -> None:
        self._max_sentences = max_sentences

    def generate(
        self,
        *,
        question: str,
        context: list[VectorSearchMatch],
        chat_history: list[dict[str, str]],
    ) -> GeneratedAnswer:
        del chat_history
        question_terms = _tokenize(question)
        if not question_terms or not context:
            return GeneratedAnswer(answer=FALLBACK_RESPONSE, cited_chunk_ids=[], used_fallback=True)

        ranked_sentences: list[tuple[float, str, str]] = []
        for match in context:
            for sentence in _split_sentences(match.chunk.text):
                sentence_terms = _tokenize(sentence)
                if not sentence_terms:
                    continue
                overlap = len(question_terms & sentence_terms) / len(question_terms)
                score = (overlap * 0.7) + (max(match.score, 0.0) * 0.3)
                if overlap == 0:
                    continue
                ranked_sentences.append((score, sentence, match.chunk.chunk_id))

        if not ranked_sentences:
            return GeneratedAnswer(answer=FALLBACK_RESPONSE, cited_chunk_ids=[], used_fallback=True)

        ranked_sentences.sort(key=lambda item: item[0], reverse=True)
        selected_sentences: list[str] = []
        cited_chunk_ids: list[str] = []
        seen_sentences: set[str] = set()

        for _, sentence, chunk_id in ranked_sentences:
            if sentence in seen_sentences:
                continue
            selected_sentences.append(sentence)
            seen_sentences.add(sentence)
            if chunk_id not in cited_chunk_ids:
                cited_chunk_ids.append(chunk_id)
            if len(selected_sentences) >= self._max_sentences:
                break

        if not selected_sentences:
            return GeneratedAnswer(answer=FALLBACK_RESPONSE, cited_chunk_ids=[], used_fallback=True)

        return GeneratedAnswer(answer=" ".join(selected_sentences), cited_chunk_ids=cited_chunk_ids)


def build_answer_generator() -> AnswerGenerator:
    return ExtractiveAnswerGenerator()


def _split_sentences(text: str) -> list[str]:
    parts = SENTENCE_SPLIT_PATTERN.split(text.strip())
    return [part.strip() for part in parts if part.strip()]


def _tokenize(text: str) -> set[str]:
    return set(TOKEN_PATTERN.findall(text.lower()))
