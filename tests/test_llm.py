import json as jsonlib

import httpx
import pytest

from app.services.generator import GroundedAnswerPayload
from app.services.llm import LLMGenerationError, OllamaLLMClient


def test_ollama_client_parses_structured_json(monkeypatch) -> None:
    client = OllamaLLMClient(base_url="http://localhost:11434", model="qwen2.5:7b-instruct")

    def fake_post(url, json, timeout):
        assert url == "http://localhost:11434/api/chat"
        assert json["model"] == "qwen2.5:7b-instruct"
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "message": {
                    "content": jsonlib.dumps(
                        {
                            "answer": "Grounded answer",
                            "cited_chunk_ids": ["doc-1-chunk-0000"],
                            "insufficient_context": False,
                        }
                    )
                }
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    result = client.chat_json(
        system_prompt="system",
        user_prompt="user",
        response_model=GroundedAnswerPayload,
    )

    assert result.answer == "Grounded answer"
    assert result.cited_chunk_ids == ["doc-1-chunk-0000"]


def test_ollama_client_raises_clear_error_on_http_failure(monkeypatch) -> None:
    client = OllamaLLMClient(base_url="http://localhost:11434", model="qwen2.5:7b-instruct")

    def fake_post(url, json, timeout):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(LLMGenerationError):
        client.chat_json(system_prompt="system", user_prompt="user", response_model=GroundedAnswerPayload)
