from __future__ import annotations

from typing import Any
from uuid import uuid4


DEFAULT_STATE: dict[str, Any] = {
    "backend_url": "http://127.0.0.1:8000",
    "session_id": "",
    "uploaded_documents": [],
    "last_index_result": None,
    "search_results": [],
    "chat_history": [],
    "status_message": None,
}


def initialize_state(session_state: Any) -> None:
    for key, value in DEFAULT_STATE.items():
        if key not in session_state:
            session_state[key] = list(value) if isinstance(value, list) else value
    if not session_state["session_id"]:
        session_state["session_id"] = uuid4().hex


def reset_conversation(session_state: Any) -> str:
    session_state["session_id"] = uuid4().hex
    session_state["chat_history"] = []
    session_state["search_results"] = []
    session_state["status_message"] = None
    return session_state["session_id"]


def record_uploaded_documents(session_state: Any, documents: list[dict[str, Any]]) -> None:
    existing_ids = {item["document_id"] for item in session_state["uploaded_documents"]}
    for document in documents:
        if document["document_id"] in existing_ids:
            continue
        session_state["uploaded_documents"].append(document)
        existing_ids.add(document["document_id"])


def append_chat_turn(
    session_state: Any,
    *,
    question: str,
    response: dict[str, Any],
) -> None:
    session_state["chat_history"].append(
        {
            "question": question,
            "answer": response["answer"],
            "confidence_score": response["confidence_score"],
            "citations": response["citations"],
            "retrieved_chunks": response["retrieved_chunks"],
        }
    )
