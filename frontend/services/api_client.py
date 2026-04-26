from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx


class DocuMindApiError(Exception):
    pass


@dataclass(slots=True)
class UploadPayload:
    path: Path
    content: bytes


class DocuMindApiClient:
    def __init__(self, base_url: str, timeout: float = 30.0, client: httpx.Client | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client = client or httpx.Client(
            base_url=self._base_url,
            timeout=self._timeout,
            trust_env=False,
        )

    def close(self) -> None:
        self._client.close()

    @property
    def base_url(self) -> str:
        return self._base_url

    def get_system_status(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/system/status")

    def upload_documents(
        self,
        *,
        files: list[UploadPayload],
        chunking_strategy: str,
        chunk_size: int | None,
        chunk_overlap: int | None,
    ) -> dict[str, Any]:
        multipart_files = [
            ("files", (payload.path.name, payload.content, _guess_mime_type(payload.path.suffix.lower())))
            for payload in files
        ]
        data: dict[str, Any] = {"chunking_strategy": chunking_strategy}
        if chunk_size is not None:
            data["chunk_size"] = str(chunk_size)
        if chunk_overlap is not None:
            data["chunk_overlap"] = str(chunk_overlap)
        return self._request("POST", "/api/v1/documents/upload", files=multipart_files, data=data)

    def index_documents(self, document_ids: list[str] | None = None) -> dict[str, Any]:
        return self._request("POST", "/api/v1/documents/index", json={"document_ids": document_ids})

    def search_documents(self, *, query: str, top_k: int) -> dict[str, Any]:
        return self._request("POST", "/api/v1/documents/search", json={"query": query, "top_k": top_k})

    def query_chat(self, *, session_id: str, user_query: str, top_k: int) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/v1/chat/query",
            json={"session_id": session_id, "user_query": user_query, "top_k": top_k},
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise DocuMindApiError(
                f"DocuMind backend is unavailable at {self._base_url}. Verify the API is running."
            ) from exc

        if response.is_error:
            detail = _extract_error_message(response)
            raise DocuMindApiError(f"{detail} Backend URL: {self._base_url}")
        return response.json()


def _extract_error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return f"Backend request failed with status {response.status_code}."

    if isinstance(payload, dict) and "detail" in payload:
        detail = payload["detail"]
        if isinstance(detail, str):
            return detail
    return f"Backend request failed with status {response.status_code}."


def _guess_mime_type(extension: str) -> str:
    return {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain",
    }.get(extension, "application/octet-stream")
