from app.services.generator import FALLBACK_RESPONSE


def test_upload_index_search_integration_flow(client) -> None:
    upload = client.post(
        "/api/v1/documents/upload",
        files=[
            ("files", ("claims.txt", b"Claims must be filed within 30 days.", "text/plain")),
            ("files", ("policy.txt", b"Appeals are reviewed within 7 business days.", "text/plain")),
        ],
    )
    assert upload.status_code == 201
    payload = upload.json()
    assert len(payload["documents"]) == 2

    index = client.post("/api/v1/documents/index", json={})
    assert index.status_code == 200
    assert index.json()["total_chunks_indexed"] >= 2

    search = client.post("/api/v1/documents/search", json={"query": "How quickly are appeals reviewed?", "top_k": 2})
    assert search.status_code == 200
    search_payload = search.json()
    assert len(search_payload["matches"]) >= 1
    assert search_payload["matches"][0]["filename"] == "policy.txt"
    assert "7 business days" in search_payload["matches"][0]["text"]


def test_upload_index_chat_integration_flow(client) -> None:
    upload = client.post(
        "/api/v1/documents/upload",
        files=[
            (
                "files",
                (
                    "manual.txt",
                    b"DocuMind indexes chunks with embeddings.\n\nDocuMind answers questions with citations.",
                    "text/plain",
                ),
            )
        ],
    )
    assert upload.status_code == 201

    index = client.post("/api/v1/documents/index", json={})
    assert index.status_code == 200

    chat = client.post(
        "/api/v1/chat/query",
        json={"session_id": "integration-1", "user_query": "How does DocuMind answer questions?", "top_k": 2},
    )
    assert chat.status_code == 200
    chat_payload = chat.json()
    assert "citations" in chat_payload["answer"]
    assert len(chat_payload["citations"]) >= 1
    assert chat_payload["retrieved_chunks"][0]["filename"] == "manual.txt"


def test_weak_context_fallback_integration_flow(client) -> None:
    upload = client.post(
        "/api/v1/documents/upload",
        files=[("files", ("product.txt", b"DocuMind supports TXT uploads.", "text/plain"))],
    )
    assert upload.status_code == 201

    index = client.post("/api/v1/documents/index", json={})
    assert index.status_code == 200

    chat = client.post(
        "/api/v1/chat/query",
        json={"session_id": "integration-fallback", "user_query": "What was last quarter revenue?", "top_k": 2},
    )
    assert chat.status_code == 200
    chat_payload = chat.json()
    assert chat_payload["answer"] == FALLBACK_RESPONSE
    assert chat_payload["citations"] == []
