from __future__ import annotations

import re
from dataclasses import dataclass, field
from statistics import mean
from time import perf_counter
from uuid import uuid4

from app.services.generator import AnswerGenerator, FALLBACK_RESPONSE
from app.services.retrieval import RetrievalService
from app.services.vector_store import VectorSearchMatch
from app.utils.logging import get_logger

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
MEMORY_HINT_TERMS = {"it", "they", "them", "that", "this", "those", "these", "he", "she", "there", "then"}


@dataclass(slots=True)
class ConversationTurn:
    user_query: str
    answer: str
    citations: list[str]


@dataclass
class ConversationStore:
    _sessions: dict[str, list[ConversationTurn]] = field(default_factory=dict)

    def get_history(self, session_id: str) -> list[ConversationTurn]:
        return list(self._sessions.get(session_id, []))

    def append_turn(self, session_id: str, turn: ConversationTurn) -> None:
        self._sessions.setdefault(session_id, []).append(turn)

    def reset_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


@dataclass(slots=True)
class ChatResult:
    session_id: str
    answer: str
    confidence_score: float
    citations: list[VectorSearchMatch]
    retrieved_chunks: list[VectorSearchMatch]


@dataclass
class ChatService:
    retrieval_service: RetrievalService
    answer_generator: AnswerGenerator
    conversation_store: ConversationStore
    default_top_k: int
    minimum_grounding_score: float = 0.2
    minimum_overlap_ratio: float = 0.1

    def __post_init__(self) -> None:
        self._logger = get_logger(component="chat")

    def query(self, *, session_id: str | None, user_query: str, top_k: int | None = None) -> ChatResult:
        start = perf_counter()
        resolved_session_id = session_id or uuid4().hex
        history = self.conversation_store.get_history(resolved_session_id)
        retrieval_query = self._build_retrieval_query(user_query, history)
        matches = self.retrieval_service.retrieve(retrieval_query, top_k or self.default_top_k)
        confidence = self._calculate_confidence(matches)

        if not self._has_sufficient_context(retrieval_query, matches):
            answer = FALLBACK_RESPONSE
            citations: list[VectorSearchMatch] = []
            confidence = min(confidence, self.minimum_grounding_score)
            used_fallback = True
        else:
            generated = self.answer_generator.generate(
                question=retrieval_query,
                context=matches,
                chat_history=[{"user_query": turn.user_query, "answer": turn.answer} for turn in history],
            )
            if generated.used_fallback or not generated.answer.strip():
                answer = FALLBACK_RESPONSE
                citations = []
                confidence = min(confidence, self.minimum_grounding_score)
                used_fallback = True
            else:
                answer = generated.answer
                cited_ids = set(generated.cited_chunk_ids)
                citations = [match for match in matches if match.chunk.chunk_id in cited_ids] or matches[:1]
                used_fallback = False

        self.conversation_store.append_turn(
            resolved_session_id,
            ConversationTurn(
                user_query=user_query,
                answer=answer,
                citations=[match.chunk.chunk_id for match in citations],
            ),
        )
        self._logger.info(
            "chat_query_completed",
            session_id=resolved_session_id,
            user_query=user_query,
            retrieval_query=retrieval_query,
            history_turns=len(history),
            retrieved_chunks=len(matches),
            citations=len(citations),
            confidence_score=round(confidence, 3),
            used_fallback=used_fallback,
            duration_ms=round((perf_counter() - start) * 1000, 2),
        )

        return ChatResult(
            session_id=resolved_session_id,
            answer=answer,
            confidence_score=round(confidence, 3),
            citations=citations,
            retrieved_chunks=matches,
        )

    def _build_retrieval_query(self, user_query: str, history: list[ConversationTurn]) -> str:
        if not history:
            return user_query
        if not self._needs_memory(user_query):
            return user_query
        previous_query = history[-1].user_query
        return f"{previous_query} {user_query}".strip()

    def _needs_memory(self, user_query: str) -> bool:
        terms = _tokenize(user_query)
        if len(terms) <= 4:
            return True
        return any(term in MEMORY_HINT_TERMS for term in terms)

    def _has_sufficient_context(self, query: str, matches: list[VectorSearchMatch]) -> bool:
        if not matches:
            return False
        top_score = max(matches[0].score, 0.0)
        overlap = max(self._overlap_ratio(query, match.chunk.text) for match in matches)
        if top_score >= self.minimum_grounding_score and overlap >= self.minimum_overlap_ratio:
            return True
        return overlap >= max(0.25, self.minimum_overlap_ratio * 2)

    def _calculate_confidence(self, matches: list[VectorSearchMatch]) -> float:
        if not matches:
            return 0.0
        positive_scores = [max(match.score, 0.0) for match in matches]
        top_score = positive_scores[0]
        average_score = mean(positive_scores)
        return min(1.0, (top_score * 0.65) + (average_score * 0.35))

    def _overlap_ratio(self, query: str, text: str) -> float:
        query_terms = _tokenize(query)
        text_terms = _tokenize(text)
        if not query_terms or not text_terms:
            return 0.0
        return len(query_terms & text_terms) / len(query_terms)


def _tokenize(text: str) -> set[str]:
    return set(TOKEN_PATTERN.findall(text.lower()))
