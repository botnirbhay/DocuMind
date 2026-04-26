from app.services.generator import FALLBACK_RESPONSE


class UnexpectedGenerator:
    def generate(self, *, question, context, chat_history):
        raise AssertionError("Generator should not be called for weak context.")


def test_chat_query_success_path_returns_answer_and_citations(client) -> None:
    _upload_and_index(
        client,
        b"DocuMind supports PDF, DOCX, and TXT uploads.\n\nIt uses retrieval for grounded answers.",
        "documind.txt",
    )

    response = client.post(
        "/api/v1/chat/query",
        json={"session_id": "chat-1", "user_query": "What uploads does DocuMind support?", "top_k": 2},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"] == "chat-1"
    assert "PDF, DOCX, and TXT" in payload["answer"]
    assert payload["confidence_score"] > 0
    assert len(payload["citations"]) >= 1
    assert payload["citations"][0]["filename"] == "documind.txt"
    assert len(payload["retrieved_chunks"]) >= 1


def test_chat_query_rejects_empty_input(client) -> None:
    response = client.post("/api/v1/chat/query", json={"session_id": "chat-1", "user_query": ""})

    assert response.status_code == 422


def test_session_memory_persists_across_turns(client) -> None:
    _upload_and_index(
        client,
        b"Project Atlas launched in 2024.\n\nProject Atlas helps banks process claims.",
        "atlas.txt",
    )

    first = client.post(
        "/api/v1/chat/query",
        json={"session_id": "memory-1", "user_query": "What is Project Atlas?", "top_k": 2},
    )
    assert first.status_code == 200

    second = client.post(
        "/api/v1/chat/query",
        json={"session_id": "memory-1", "user_query": "When did it launch?", "top_k": 2},
    )

    assert second.status_code == 200
    payload = second.json()
    assert "2024" in payload["answer"]
    history = client.app.state.container.conversation_store.get_history("memory-1")
    assert len(history) == 2


def test_citations_included_in_chat_response(client) -> None:
    _upload_and_index(client, b"Claims are reviewed within 7 business days.", "policy.txt")

    response = client.post(
        "/api/v1/chat/query",
        json={"session_id": "citations-1", "user_query": "How long are claims reviewed?", "top_k": 1},
    )

    assert response.status_code == 200
    citation = response.json()["citations"][0]
    assert citation["document_id"]
    assert citation["chunk_id"]
    assert citation["snippet"]


def test_non_hallucination_behavior_in_low_context_case(client) -> None:
    _upload_and_index(client, b"DocuMind supports PDF uploads.", "product.txt")
    client.app.state.container.chat_service.answer_generator = UnexpectedGenerator()

    response = client.post(
        "/api/v1/chat/query",
        json={"session_id": "low-context-1", "user_query": "What is the annual revenue?", "top_k": 1},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == FALLBACK_RESPONSE
    assert payload["citations"] == []
    assert payload["retrieved_chunks"] == []


def test_summary_route_returns_document_aware_summary_and_questions(client) -> None:
    _upload_and_index(
        client,
        "\n".join(
            [
                "Avery Stone",
                "Senior Software Engineer",
                "Skills: Python, FastAPI, React, AWS",
                "Built document intelligence workflows for enterprise clients.",
            ]
        ).encode("utf-8"),
        "resume.txt",
    )

    response = client.post("/api/v1/chat/summary", json={})

    assert response.status_code == 200
    payload = response.json()
    assert "Senior Software Engineer" in payload["answer"]
    assert payload["citations"]
    assert payload["suggested_questions"][0] == "What are the candidate's strongest skills?"


def _upload_and_index(client, content: bytes, filename: str) -> None:
    upload = client.post(
        "/api/v1/documents/upload",
        files=[("files", (filename, content, "text/plain"))],
    )
    assert upload.status_code == 201

    index = client.post("/api/v1/documents/index", json={})
    assert index.status_code == 200
