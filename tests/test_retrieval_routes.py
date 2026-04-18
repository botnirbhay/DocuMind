def test_retrieval_route_success_path(client) -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files=[("files", ("animals.txt", b"cats are calm\n\ndogs are playful", "text/plain"))],
    )
    assert upload_response.status_code == 201

    index_response = client.post("/api/v1/documents/index", json={})
    assert index_response.status_code == 200
    assert index_response.json()["total_chunks_indexed"] >= 1

    search_response = client.post(
        "/api/v1/documents/search",
        json={"query": "cats", "top_k": 1},
    )

    assert search_response.status_code == 200
    payload = search_response.json()
    assert payload["query"] == "cats"
    assert len(payload["matches"]) == 1
    assert payload["matches"][0]["filename"] == "animals.txt"
    assert "cats" in payload["matches"][0]["text"]


def test_retrieval_route_fails_when_index_missing(client) -> None:
    response = client.post("/api/v1/documents/search", json={"query": "cats", "top_k": 1})

    assert response.status_code == 400
    assert "Vector index is not ready" in response.json()["detail"]
