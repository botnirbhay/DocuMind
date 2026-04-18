from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel, Field

from app.services.documents import DocumentChunk, DocumentRecord
from app.services.llm import LLMGenerationError, OllamaLLMClient
from app.services.vector_store import VectorSearchMatch
from app.utils.config import Settings

FALLBACK_RESPONSE = "Sorry, I couldn't find that in the provided documents."
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
LINE_SPLIT_PATTERN = re.compile(r"[\r\n]+")
WHITESPACE_PATTERN = re.compile(r"\s+")
JOB_TITLE_PATTERN = re.compile(
    r"\b(engineer|developer|manager|analyst|consultant|designer|architect|lead|specialist|intern|scientist)\b",
    re.IGNORECASE,
)
RESUME_SECTION_HINTS = {
    "experience",
    "skills",
    "education",
    "projects",
    "certifications",
    "summary",
    "employment",
    "technical",
}
GENERAL_TOPIC_QUESTIONS = (
    "What are the main points covered in these documents?",
    "What important dates, deadlines, or milestones are mentioned?",
    "What rules, requirements, or responsibilities are described?",
)
RESUME_TOPIC_QUESTIONS = (
    "What are the candidate's strongest skills?",
    "Summarize the candidate's professional experience.",
    "Which projects or achievements stand out in this resume?",
)
MAX_CONTEXT_CHARS = 12000
MAX_SUMMARY_CHUNKS = 10


@dataclass(slots=True)
class GeneratedAnswer:
    answer: str
    cited_chunk_ids: list[str]
    used_fallback: bool = False


@dataclass(slots=True)
class GeneratedSummary:
    answer: str
    cited_chunk_ids: list[str]
    suggested_questions: list[str]
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


class SummaryGenerator(Protocol):
    def summarize(self, *, documents: list[DocumentRecord]) -> GeneratedSummary:
        """Return a concise document-grounded summary."""


class GroundedAnswerPayload(BaseModel):
    answer: str
    cited_chunk_ids: list[str] = Field(default_factory=list)
    insufficient_context: bool = False


class GroundedSummaryPayload(BaseModel):
    answer: str
    cited_chunk_ids: list[str] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    insufficient_context: bool = False


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


class HeuristicSummaryGenerator:
    def __init__(self, max_sentences: int = 4) -> None:
        self._max_sentences = max_sentences

    def summarize(self, *, documents: list[DocumentRecord]) -> GeneratedSummary:
        if not documents:
            return GeneratedSummary(
                answer=FALLBACK_RESPONSE,
                cited_chunk_ids=[],
                suggested_questions=[],
                used_fallback=True,
            )

        chunks = [chunk for document in documents for chunk in document.chunks]
        if not chunks:
            return GeneratedSummary(
                answer=FALLBACK_RESPONSE,
                cited_chunk_ids=[],
                suggested_questions=[],
                used_fallback=True,
            )

        if _looks_like_resume(documents, chunks):
            answer, cited_chunk_ids = self._summarize_resume(chunks)
            suggested_questions = list(RESUME_TOPIC_QUESTIONS)
        else:
            answer, cited_chunk_ids = self._summarize_general(chunks)
            suggested_questions = self._build_general_questions(documents, chunks)

        if not answer.strip():
            return GeneratedSummary(
                answer=FALLBACK_RESPONSE,
                cited_chunk_ids=[],
                suggested_questions=[],
                used_fallback=True,
            )

        return GeneratedSummary(
            answer=answer,
            cited_chunk_ids=cited_chunk_ids,
            suggested_questions=suggested_questions,
        )

    def _summarize_resume(self, chunks: list[DocumentChunk]) -> tuple[str, list[str]]:
        lines = _collect_chunk_lines(chunks, max_chunks=6)
        if not lines:
            return "", []

        name = _extract_resume_name(lines)
        headline = _extract_headline(lines)
        skill_line = _select_line(lines, {"skills", "stack", "technologies", "tools", "languages"})
        achievement_lines = _select_distinct_lines(
            lines,
            preferred_terms={"built", "developed", "designed", "implemented", "led", "managed", "created", "improved"},
            limit=2,
        )
        education_line = _select_line(lines, {"university", "college", "bachelor", "master", "degree", "education"})

        sentences: list[str] = []
        cited_chunk_ids: list[str] = []

        if headline:
            headline_text, headline_chunk_id = headline
            prefix = f"{name} is a {headline_text}" if name else f"The document profiles a {headline_text}"
            sentences.append(prefix.rstrip(".") + ".")
            cited_chunk_ids.append(headline_chunk_id)
        elif name:
            sentences.append(f"This resume belongs to {name}.")

        if skill_line:
            text, chunk_id = skill_line
            skills = _clip_detail(_strip_label(text), 18)
            sentences.append(f"Key skills include {skills}.")
            cited_chunk_ids.append(chunk_id)

        if achievement_lines:
            achievement_text = "; ".join(_clip_detail(_strip_bullet(line_text), 18) for line_text, _ in achievement_lines)
            sentences.append(f"Highlighted experience includes {achievement_text}.")
            cited_chunk_ids.extend(chunk_id for _, chunk_id in achievement_lines)

        if education_line:
            text, chunk_id = education_line
            sentences.append(f"Education or credentials mention {_clip_detail(_strip_bullet(text), 18)}.")
            cited_chunk_ids.append(chunk_id)

        if not sentences:
            fallback_lines = [line for line, _ in lines[: self._max_sentences]]
            fallback_ids = [chunk_id for _, chunk_id in lines[: self._max_sentences]]
            return " ".join(_strip_bullet(line) for line in fallback_lines), _dedupe_preserve_order(fallback_ids)

        return " ".join(sentences[: self._max_sentences]), _dedupe_preserve_order(cited_chunk_ids)

    def _summarize_general(self, chunks: list[DocumentChunk]) -> tuple[str, list[str]]:
        candidates: list[tuple[float, str, str]] = []

        for chunk in chunks[:12]:
            for unit in _extract_summary_units(chunk.text):
                score = _score_summary_unit(unit, chunk.chunk_index)
                if score <= 0:
                    continue
                candidates.append((score, unit, chunk.chunk_id))

        if not candidates:
            return "", []

        candidates.sort(key=lambda item: item[0], reverse=True)
        selected_units: list[str] = []
        cited_chunk_ids: list[str] = []

        for _, unit, chunk_id in candidates:
            if any(_is_near_duplicate(unit, existing) for existing in selected_units):
                continue
            selected_units.append(unit)
            cited_chunk_ids.append(chunk_id)
            if len(selected_units) >= self._max_sentences:
                break

        summary = " ".join(selected_units)
        return summary, _dedupe_preserve_order(cited_chunk_ids)

    def _build_general_questions(
        self,
        documents: list[DocumentRecord],
        chunks: list[DocumentChunk],
    ) -> list[str]:
        lowered_filenames = " ".join(document.filename.lower() for document in documents)
        text = " ".join(chunk.text.lower() for chunk in chunks[:6])

        questions: list[str] = [GENERAL_TOPIC_QUESTIONS[0]]
        if any(term in lowered_filenames or term in text for term in {"date", "deadline", "timeline", "launch", "review"}):
            questions.append("What dates, deadlines, or timelines are mentioned?")
        if any(term in lowered_filenames or term in text for term in {"policy", "rule", "requirement", "eligibility", "scope"}):
            questions.append("What policies, requirements, or exceptions are described?")
        if any(term in lowered_filenames or term in text for term in {"project", "program", "initiative"}):
            questions.append("Which projects, programs, or named initiatives are mentioned?")

        while len(questions) < 3:
            questions.append(GENERAL_TOPIC_QUESTIONS[len(questions)])

        return questions[:3]


class OllamaGroundedAnswerGenerator:
    def __init__(self, client: OllamaLLMClient) -> None:
        self._client = client

    def generate(
        self,
        *,
        question: str,
        context: list[VectorSearchMatch],
        chat_history: list[dict[str, str]],
    ) -> GeneratedAnswer:
        if not context:
            return GeneratedAnswer(answer=FALLBACK_RESPONSE, cited_chunk_ids=[], used_fallback=True)

        allowed_chunk_ids = [match.chunk.chunk_id for match in context]
        system_prompt = (
            "You are DocuMind, a document-grounded assistant. "
            "Answer using only the supplied document chunks. "
            "If the context is insufficient, set insufficient_context to true and use the exact fallback message. "
            "Keep the answer concise and factual. "
            "Only cite chunk ids from the provided list."
        )
        user_prompt = "\n\n".join(
            [
                _format_chat_history(chat_history),
                f"Question:\n{question}",
                f"Allowed citation chunk ids:\n{', '.join(allowed_chunk_ids)}",
                f"Retrieved context:\n{_format_context(context)}",
                (
                    "Return JSON with keys: answer, cited_chunk_ids, insufficient_context. "
                    f'If you cannot answer, use this exact answer: "{FALLBACK_RESPONSE}"'
                ),
            ]
        )

        payload = self._client.chat_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=GroundedAnswerPayload,
        )
        return _build_generated_answer(payload, allowed_chunk_ids)


class OllamaGroundedSummaryGenerator:
    def __init__(self, client: OllamaLLMClient) -> None:
        self._client = client

    def summarize(self, *, documents: list[DocumentRecord]) -> GeneratedSummary:
        if not documents:
            return GeneratedSummary(
                answer=FALLBACK_RESPONSE,
                cited_chunk_ids=[],
                suggested_questions=[],
                used_fallback=True,
            )

        selected_chunks = _select_summary_chunks(documents)
        if not selected_chunks:
            return GeneratedSummary(
                answer=FALLBACK_RESPONSE,
                cited_chunk_ids=[],
                suggested_questions=[],
                used_fallback=True,
            )

        allowed_chunk_ids = [chunk.chunk_id for chunk in selected_chunks]
        system_prompt = (
            "You are DocuMind, an AI assistant that summarizes uploaded documents. "
            "Use only the supplied chunks. "
            "Write a concise executive summary that reflects the actual document set. "
            "If the context is insufficient, set insufficient_context to true and use the exact fallback message. "
            "Also produce 3 grounded follow-up questions a user could ask next."
        )
        user_prompt = "\n\n".join(
            [
                "Document set:\n" + "\n".join(f"- {document.filename}" for document in documents),
                f"Allowed citation chunk ids:\n{', '.join(allowed_chunk_ids)}",
                "Representative chunks:\n" + _format_chunk_records(selected_chunks),
                (
                    "Return JSON with keys: answer, cited_chunk_ids, suggested_questions, insufficient_context. "
                    f'If you cannot summarize, use this exact answer: "{FALLBACK_RESPONSE}"'
                ),
            ]
        )
        payload = self._client.chat_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=GroundedSummaryPayload,
        )
        return _build_generated_summary(payload, allowed_chunk_ids)


class ResilientAnswerGenerator:
    def __init__(self, primary: AnswerGenerator, fallback: AnswerGenerator) -> None:
        self._primary = primary
        self._fallback = fallback

    def generate(
        self,
        *,
        question: str,
        context: list[VectorSearchMatch],
        chat_history: list[dict[str, str]],
    ) -> GeneratedAnswer:
        try:
            return self._primary.generate(question=question, context=context, chat_history=chat_history)
        except LLMGenerationError:
            return self._fallback.generate(question=question, context=context, chat_history=chat_history)


class ResilientSummaryGenerator:
    def __init__(self, primary: SummaryGenerator, fallback: SummaryGenerator) -> None:
        self._primary = primary
        self._fallback = fallback

    def summarize(self, *, documents: list[DocumentRecord]) -> GeneratedSummary:
        try:
            return self._primary.summarize(documents=documents)
        except LLMGenerationError:
            return self._fallback.summarize(documents=documents)


def build_answer_generator(settings: Settings) -> AnswerGenerator:
    fallback = ExtractiveAnswerGenerator()
    if settings.llm_provider == "extractive":
        return fallback
    if settings.llm_provider == "ollama":
        client = OllamaLLMClient(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            timeout_seconds=settings.ollama_timeout_seconds,
            temperature=settings.ollama_temperature,
            keep_alive=settings.ollama_keep_alive,
        )
        return ResilientAnswerGenerator(OllamaGroundedAnswerGenerator(client), fallback)
    raise ValueError(f"Unsupported llm provider: {settings.llm_provider}")


def build_summary_generator(settings: Settings) -> SummaryGenerator:
    fallback = HeuristicSummaryGenerator()
    if settings.llm_provider == "extractive":
        return fallback
    if settings.llm_provider == "ollama":
        client = OllamaLLMClient(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            timeout_seconds=settings.ollama_timeout_seconds,
            temperature=settings.ollama_temperature,
            keep_alive=settings.ollama_keep_alive,
        )
        return ResilientSummaryGenerator(OllamaGroundedSummaryGenerator(client), fallback)
    raise ValueError(f"Unsupported llm provider: {settings.llm_provider}")


def _split_sentences(text: str) -> list[str]:
    parts = SENTENCE_SPLIT_PATTERN.split(text.strip())
    return [part.strip() for part in parts if part.strip()]


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


def _looks_like_resume(documents: list[DocumentRecord], chunks: list[DocumentChunk]) -> bool:
    filenames = " ".join(document.filename.lower() for document in documents)
    if any(term in filenames for term in {"resume", "cv", "curriculum"}):
        return True

    combined_text = " ".join(chunk.text[:500].lower() for chunk in chunks[:4])
    hint_count = sum(1 for term in RESUME_SECTION_HINTS if term in combined_text)
    return hint_count >= 2


def _collect_chunk_lines(chunks: list[DocumentChunk], max_chunks: int) -> list[tuple[str, str]]:
    lines: list[tuple[str, str]] = []
    for chunk in chunks[:max_chunks]:
        for raw_line in LINE_SPLIT_PATTERN.split(chunk.text):
            normalized = WHITESPACE_PATTERN.sub(" ", raw_line).strip(" -\t")
            if len(normalized) < 3:
                continue
            lines.append((normalized, chunk.chunk_id))
    return lines


def _extract_resume_name(lines: list[tuple[str, str]]) -> str | None:
    for line, _ in lines[:6]:
        if any(char.isdigit() for char in line):
            continue
        if "@" in line or "http" in line.lower():
            continue
        words = line.split()
        if 2 <= len(words) <= 4 and all(word[:1].isupper() for word in words if word.isalpha() or word[:1].isupper()):
            return line
    return None


def _extract_headline(lines: list[tuple[str, str]]) -> tuple[str, str] | None:
    for line, chunk_id in lines[:12]:
        if JOB_TITLE_PATTERN.search(line):
            return (_strip_bullet(line), chunk_id)
    return None


def _select_line(lines: list[tuple[str, str]], preferred_terms: set[str]) -> tuple[str, str] | None:
    for line, chunk_id in lines:
        lowered = line.lower()
        if any(term in lowered for term in preferred_terms):
            return (line, chunk_id)
    return None


def _select_distinct_lines(
    lines: list[tuple[str, str]],
    preferred_terms: set[str],
    limit: int,
) -> list[tuple[str, str]]:
    selected: list[tuple[str, str]] = []
    for line, chunk_id in lines:
        lowered = line.lower()
        if not any(term in lowered for term in preferred_terms):
            continue
        if any(_is_near_duplicate(line, existing_line) for existing_line, _ in selected):
            continue
        selected.append((line, chunk_id))
        if len(selected) >= limit:
            break
    return selected


def _extract_summary_units(text: str) -> list[str]:
    units: list[str] = []
    for paragraph in text.split("\n\n"):
        paragraph = WHITESPACE_PATTERN.sub(" ", paragraph).strip()
        if not paragraph:
            continue
        if len(paragraph.split()) <= 28:
            units.append(paragraph)
            continue
        units.extend(_split_sentences(paragraph))
    return [unit.strip() for unit in units if unit.strip()]


def _score_summary_unit(unit: str, chunk_index: int) -> float:
    tokens = _tokenize(unit)
    token_count = len(tokens)
    if token_count < 4:
        return 0.0

    lowered = unit.lower()
    score = 0.4
    if 5 <= token_count <= 24:
        score += 0.25
    if any(char.isdigit() for char in unit):
        score += 0.12
    if any(term in lowered for term in {"must", "should", "includes", "supports", "requires", "experience", "skills", "project"}):
        score += 0.12
    if lowered.endswith(":"):
        score -= 0.2
    if len(unit) > 240:
        score -= 0.15
    score += max(0.0, 0.2 - (chunk_index * 0.02))
    return score


def _is_near_duplicate(candidate: str, existing: str) -> bool:
    candidate_terms = _tokenize(candidate)
    existing_terms = _tokenize(existing)
    if not candidate_terms or not existing_terms:
        return False
    overlap = len(candidate_terms & existing_terms) / min(len(candidate_terms), len(existing_terms))
    return overlap >= 0.8


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _strip_bullet(text: str) -> str:
    return re.sub(r"^[\-\u2022\*]+\s*", "", text).strip()


def _strip_label(text: str) -> str:
    return re.sub(r"^[A-Za-z\s/&]+:\s*", "", text).strip()


def _clip_detail(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text.rstrip(".")
    return " ".join(words[:max_words]).rstrip(".,;:") + "..."


def _format_chat_history(chat_history: list[dict[str, str]]) -> str:
    if not chat_history:
        return "Conversation history:\n(none)"
    recent_turns = chat_history[-4:]
    rendered = []
    for turn in recent_turns:
        rendered.append(f"User: {turn['user_query']}\nAssistant: {turn['answer']}")
    return "Conversation history:\n" + "\n\n".join(rendered)


def _format_context(context: list[VectorSearchMatch]) -> str:
    remaining = MAX_CONTEXT_CHARS
    lines: list[str] = []
    for match in context:
        block = (
            f"[chunk_id={match.chunk.chunk_id} | filename={match.chunk.filename} | "
            f"page={match.chunk.page_number if match.chunk.page_number is not None else 'n/a'} | "
            f"score={match.score:.3f}]\n{match.chunk.text}"
        )
        if remaining <= 0:
            break
        if len(block) > remaining:
            block = block[:remaining].rstrip() + "..."
        lines.append(block)
        remaining -= len(block)
    return "\n\n".join(lines)


def _format_chunk_records(chunks: list[DocumentChunk]) -> str:
    return "\n\n".join(
        (
            f"[chunk_id={chunk.chunk_id} | filename={chunk.filename} | "
            f"page={chunk.page_number if chunk.page_number is not None else 'n/a'}]\n{chunk.text}"
        )
        for chunk in chunks
    )


def _select_summary_chunks(documents: list[DocumentRecord]) -> list[DocumentChunk]:
    selected: list[DocumentChunk] = []
    total_chars = 0
    for document in documents:
        for chunk in document.chunks:
            if len(selected) >= MAX_SUMMARY_CHUNKS or total_chars >= MAX_CONTEXT_CHARS:
                return selected
            selected.append(chunk)
            total_chars += len(chunk.text)
    return selected


def _build_generated_answer(payload: GroundedAnswerPayload, allowed_chunk_ids: list[str]) -> GeneratedAnswer:
    cited_chunk_ids = [chunk_id for chunk_id in payload.cited_chunk_ids if chunk_id in allowed_chunk_ids]
    answer = payload.answer.strip() or FALLBACK_RESPONSE
    used_fallback = payload.insufficient_context or answer == FALLBACK_RESPONSE
    if not cited_chunk_ids and not used_fallback and allowed_chunk_ids:
        cited_chunk_ids = [allowed_chunk_ids[0]]
    if used_fallback:
        return GeneratedAnswer(answer=FALLBACK_RESPONSE, cited_chunk_ids=[], used_fallback=True)
    return GeneratedAnswer(answer=answer, cited_chunk_ids=cited_chunk_ids)


def _build_generated_summary(payload: GroundedSummaryPayload, allowed_chunk_ids: list[str]) -> GeneratedSummary:
    cited_chunk_ids = [chunk_id for chunk_id in payload.cited_chunk_ids if chunk_id in allowed_chunk_ids]
    answer = payload.answer.strip() or FALLBACK_RESPONSE
    suggested_questions = [question.strip() for question in payload.suggested_questions if question.strip()][:3]
    used_fallback = payload.insufficient_context or answer == FALLBACK_RESPONSE
    if not cited_chunk_ids and not used_fallback and allowed_chunk_ids:
        cited_chunk_ids = [allowed_chunk_ids[0]]
    if used_fallback:
        return GeneratedSummary(
            answer=FALLBACK_RESPONSE,
            cited_chunk_ids=[],
            suggested_questions=[],
            used_fallback=True,
        )
    if len(suggested_questions) < 3:
        suggested_questions.extend(
            question for question in GENERAL_TOPIC_QUESTIONS if question not in suggested_questions
        )
    return GeneratedSummary(
        answer=answer,
        cited_chunk_ids=cited_chunk_ids,
        suggested_questions=suggested_questions[:3],
    )
