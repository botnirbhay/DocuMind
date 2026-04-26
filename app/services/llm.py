from __future__ import annotations

import json
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel

from app.utils.logging import get_logger

ResponseModelT = TypeVar("ResponseModelT", bound=BaseModel)


class LLMGenerationError(Exception):
    pass


@dataclass(slots=True)
class OllamaLLMClient:
    base_url: str
    model: str
    timeout_seconds: float = 60.0
    temperature: float = 0.0
    keep_alive: str = "10m"
    _chat_url: str = field(init=False, repr=False)
    _logger: Any = field(init=False, repr=False)

    def __post_init__(self) -> None:
        resolved_base_url = self.base_url.rstrip("/")
        self._chat_url = f"{resolved_base_url}/api/chat"
        self._logger = get_logger(component="llm", provider="ollama", model_name=self.model)

    def chat_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ResponseModelT],
    ) -> ResponseModelT:
        payload = {
            "model": self.model,
            "stream": False,
            "format": response_model.model_json_schema(),
            "options": {
                "temperature": self.temperature,
            },
            "keep_alive": self.keep_alive,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        start = perf_counter()
        try:
            response = httpx.post(
                self._chat_url,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            self._logger.warning(
                "ollama_request_failed",
                error=str(exc),
                duration_ms=round((perf_counter() - start) * 1000, 2),
            )
            raise LLMGenerationError("Ollama request failed.") from exc

        try:
            raw_payload = response.json()
            content = raw_payload["message"]["content"]
            parsed = response_model.model_validate_json(content)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self._logger.warning(
                "ollama_response_parse_failed",
                error=str(exc),
                duration_ms=round((perf_counter() - start) * 1000, 2),
            )
            raise LLMGenerationError("Ollama returned an invalid structured response.") from exc

        self._logger.info(
            "ollama_request_completed",
            duration_ms=round((perf_counter() - start) * 1000, 2),
            prompt_chars=len(system_prompt) + len(user_prompt),
        )
        return parsed
