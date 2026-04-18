from __future__ import annotations

import re
from dataclasses import dataclass, field
from statistics import mean
from time import perf_counter
from uuid import uuid4

from app.services.documents import DocumentChunk, DocumentRegistry
from app.services.generator import AnswerGenerator, FALLBACK_RESPONSE
from app.services.generator import GeneratedSummary, SummaryGenerator
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

    def clear(self) -> int:
        count = len(self._sessions)
        self._sessions.clear()
        return count


@dataclass(slots=True)
class ChatResult:
    session_id: str
    answer: str
    confidence_score: float
    citations: list[VectorSearchMatch]
    retrieved_chunks: list[VectorSearchMatch]


@dataclass(slots=True)
class SummaryResult:
    answer: str
    confidence_score: float
    citations: list[VectorSearchMatch]
    retrieved_chunks: list[VectorSearchMatch]
    suggested_questions: list[str]


@dataclass
class ChatService:
    document_registry: DocumentRegistry
    retrieval_service: RetrievalService
    answer_generator: AnswerGenerator
    summary_generator: SummaryGenerator
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

        if not self._has_sufficient_context(user_query, matches):
            answer = FALLBACK_RESPONSE
            citations: list[VectorSearchMatch] = []
            returned_chunks: list[VectorSearchMatch] = []
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
                returned_chunks = []
                confidence = min(confidence, self.minimum_grounding_score)
                used_fallback = True
            else:
                answer = generated.answer
                cited_ids = set(generated.cited_chunk_ids)
                citations = [match for match in matches if match.chunk.chunk_id in cited_ids] or matches[:1]
                returned_chunks = matches
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
            retrieved_chunks=returned_chunks,
        )

    def summarize_documents(self, *, document_ids: list[str] | None = None) -> SummaryResult:
        start = perf_counter()
        documents = self.document_registry.list()
        if document_ids is not None:
            allowed = set(document_ids)
            documents = [document for document in documents if document.document_id in allowed]

        if not documents:
            return SummaryResult(
                answer=FALLBACK_RESPONSE,
                confidence_score=0.0,
                citations=[],
                retrieved_chunks=[],
                suggested_questions=[],
            )

        generated = self.summary_generator.summarize(documents=documents)
        if generated.used_fallback or not generated.answer.strip():
            result = SummaryResult(
                answer=FALLBACK_RESPONSE,
                confidence_score=0.0,
                citations=[],
                retrieved_chunks=[],
                suggested_questions=[],
            )
        else:
            chunk_lookup = {
                chunk.chunk_id: chunk
                for document in documents
                for chunk in document.chunks
            }
            cited_matches = self._build_summary_matches(generated, chunk_lookup)
            result = SummaryResult(
                answer=generated.answer,
                confidence_score=round(self._calculate_summary_confidence(cited_matches), 3),
                citations=cited_matches,
                retrieved_chunks=cited_matches,
                suggested_questions=generated.suggested_questions,
            )

        self._logger.info(
            "document_summary_completed",
            document_count=len(documents),
            citations=len(result.citations),
            confidence_score=result.confidence_score,
            duration_ms=round((perf_counter() - start) * 1000, 2),
        )
        return result

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
        query_terms = _tokenize(query)
        if not query_terms:
            return False

        top_score = max(matches[0].score, 0.0)
        best_overlap = 0.0
        best_term_hits = 0

        for match in matches:
            text_terms = _tokenize(match.chunk.text)
            if not text_terms:
                continue
            term_hits = len(query_terms & text_terms)
            best_term_hits = max(best_term_hits, term_hits)
            best_overlap = max(best_overlap, term_hits / len(query_terms))

        minimum_term_hits = 1 if len(query_terms) <= 4 else 2
        if self._needs_memory(query) and best_overlap >= 0.25 and best_term_hits >= 1:
            return True

        if best_overlap >= 0.3 and best_term_hits >= minimum_term_hits:
            return True

        return (
            top_score >= self.minimum_grounding_score
            and best_overlap >= max(self.minimum_overlap_ratio, 0.12)
            and best_term_hits >= minimum_term_hits
        )

    def _calculate_confidence(self, matches: list[VectorSearchMatch]) -> float:
        if not matches:
            return 0.0
        positive_scores = [max(match.score, 0.0) for match in matches]
        top_score = positive_scores[0]
        average_score = mean(positive_scores)
        return min(1.0, (top_score * 0.65) + (average_score * 0.35))

    def _calculate_summary_confidence(self, matches: list[VectorSearchMatch]) -> float:
        if not matches:
            return 0.0
        return min(1.0, 0.45 + (len(matches) * 0.12))

    def _build_summary_matches(
        self,
        generated: GeneratedSummary,
        chunk_lookup: dict[str, DocumentChunk],
    ) -> list[VectorSearchMatch]:
        matches: list[VectorSearchMatch] = []
        for rank, chunk_id in enumerate(generated.cited_chunk_ids):
            chunk = chunk_lookup.get(chunk_id)
            if chunk is None:
                continue
            score = max(0.0, 0.95 - (rank * 0.1))
            matches.append(VectorSearchMatch(chunk=chunk, score=score))
        return matches

    def _overlap_ratio(self, query: str, text: str) -> float:
        query_terms = _tokenize(query)
        text_terms = _tokenize(text)
        if not query_terms or not text_terms:
            return 0.0
        return len(query_terms & text_terms) / len(query_terms)


def _tokenize(text: str) -> set[str]:
    return {_normalize_token(token) for token in TOKEN_PATTERN.findall(text.lower())}


def _normalize_token(token: str) -> str:
    if len(token) > 5 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 4 and token.endswith("ed"):
        return token[:-2]
    if len(token) > 4 and token.endswith("es"):
        return token[:-2]
    if len(token) > 4 and token.endswith("s"):
        return token[:-1]
    return token
