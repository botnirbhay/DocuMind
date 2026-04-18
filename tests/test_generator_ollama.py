from dataclasses import dataclass

from app.services.generator import (
    ExtractiveAnswerGenerator,
    FALLBACK_RESPONSE,
    GeneratedSummary,
    GroundedAnswerPayload,
    GroundedSummaryPayload,
    HeuristicSummaryGenerator,
    OllamaGroundedAnswerGenerator,
    OllamaGroundedSummaryGenerator,
    ResilientAnswerGenerator,
    ResilientSummaryGenerator,
)
from app.services.llm import LLMGenerationError
from app.services.vector_store import VectorSearchMatch
from tests.test_retrieval import _build_document_record


@dataclass
class FakeLLMClient:
    response: object | None = None
    error: Exception | None = None

    def chat_json(self, *, system_prompt: str, user_prompt: str, response_model):
        assert system_prompt
        assert user_prompt
        if self.error is not None:
            raise self.error
        return self.response


def test_ollama_answer_generator_returns_structured_grounded_answer() -> None:
    match = _build_match("doc-1", "manual.txt", "DocuMind supports PDF, DOCX, and TXT uploads.")
    generator = OllamaGroundedAnswerGenerator(
        FakeLLMClient(
            response=GroundedAnswerPayload(
                answer="DocuMind supports PDF, DOCX, and TXT uploads.",
                cited_chunk_ids=[match.chunk.chunk_id],
                insufficient_context=False,
            )
        )
    )

    result = generator.generate(question="What uploads are supported?", context=[match], chat_history=[])

    assert result.answer == "DocuMind supports PDF, DOCX, and TXT uploads."
    assert result.cited_chunk_ids == [match.chunk.chunk_id]
    assert result.used_fallback is False


def test_resilient_answer_generator_falls_back_when_ollama_is_unavailable() -> None:
    match = _build_match("doc-1", "manual.txt", "DocuMind supports PDF uploads.")
    primary = OllamaGroundedAnswerGenerator(FakeLLMClient(error=LLMGenerationError("offline")))
    fallback = ExtractiveAnswerGenerator()
    generator = ResilientAnswerGenerator(primary, fallback)

    result = generator.generate(question="What uploads does DocuMind support?", context=[match], chat_history=[])

    assert "PDF uploads" in result.answer
    assert result.cited_chunk_ids == [match.chunk.chunk_id]


def test_ollama_summary_generator_returns_grounded_summary_and_questions() -> None:
    document = _build_document_record(
        "doc-1",
        "resume.txt",
        [
            "Avery Stone\nSenior Software Engineer\nSkills: Python, FastAPI, React\nBuilt AI document workflows."
        ],
    )
    generator = OllamaGroundedSummaryGenerator(
        FakeLLMClient(
            response=GroundedSummaryPayload(
                answer="Avery Stone is a Senior Software Engineer with experience building AI document workflows.",
                cited_chunk_ids=[document.chunks[0].chunk_id],
                suggested_questions=[
                    "What are the candidate's core skills?",
                    "Which projects stand out?",
                    "Summarize the candidate's experience.",
                ],
                insufficient_context=False,
            )
        )
    )

    result = generator.summarize(documents=[document])

    assert "Senior Software Engineer" in result.answer
    assert result.cited_chunk_ids == [document.chunks[0].chunk_id]
    assert len(result.suggested_questions) == 3


def test_resilient_summary_generator_falls_back_to_heuristics() -> None:
    document = _build_document_record(
        "doc-1",
        "resume.txt",
        [
            "Avery Stone\nSenior Software Engineer\nSkills: Python, FastAPI, React\nBuilt AI document workflows."
        ],
    )
    primary = OllamaGroundedSummaryGenerator(FakeLLMClient(error=LLMGenerationError("offline")))
    fallback = HeuristicSummaryGenerator()
    generator = ResilientSummaryGenerator(primary, fallback)

    result = generator.summarize(documents=[document])

    assert result.answer != FALLBACK_RESPONSE
    assert result.suggested_questions


def _build_match(document_id: str, filename: str, text: str) -> VectorSearchMatch:
    record = _build_document_record(document_id, filename, [text])
    return VectorSearchMatch(chunk=record.chunks[0], score=0.91)
