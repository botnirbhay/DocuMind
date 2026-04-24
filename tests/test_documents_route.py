def test_upload_endpoint_ingests_supported_document(client) -> None:
    response = client.post(
        "/api/v1/documents/upload",
        files=[("files", ("notes.txt", b"Alpha paragraph.\n\nBeta paragraph.", "text/plain"))],
    )

    assert response.status_code == 201
    payload = response.json()
    assert len(payload["documents"]) == 1
    assert payload["documents"][0]["filename"] == "notes.txt"
    assert payload["documents"][0]["file_type"] == "txt"
    assert payload["documents"][0]["status"] == "ingested"
    assert payload["documents"][0]["chunks_extracted"] >= 1


def test_upload_endpoint_rejects_invalid_file_type(client) -> None:
    response = client.post(
        "/api/v1/documents/upload",
        files=[("files", ("notes.csv", b"alpha,beta", "text/csv"))],
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_endpoint_accepts_multiple_files(client) -> None:
    response = client.post(
        "/api/v1/documents/upload",
        files=[
            ("files", ("notes.txt", b"Alpha paragraph.\n\nBeta paragraph.", "text/plain")),
            ("files", ("guide.txt", b"Gamma paragraph.\n\nDelta paragraph.", "text/plain")),
        ],
    )

    assert response.status_code == 201
    payload = response.json()
    assert len(payload["documents"]) == 2
    assert {document["filename"] for document in payload["documents"]} == {"notes.txt", "guide.txt"}


def test_remove_document_endpoint_removes_one_document_and_reindexes(client) -> None:
    upload = client.post(
        "/api/v1/documents/upload",
        files=[
            ("files", ("notes.txt", b"Alpha paragraph.\n\nBeta paragraph.", "text/plain")),
            ("files", ("guide.txt", b"Gamma paragraph.\n\nDelta paragraph.", "text/plain")),
        ],
    )
    uploaded = upload.json()["documents"]
    target_document_id = uploaded[0]["document_id"]

    response = client.delete(f"/api/v1/documents/{target_document_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "removed"
    assert payload["document_id"] == target_document_id
    assert payload["documents_remaining"] == 1
    assert payload["total_chunks_indexed"] >= 1


def test_remove_document_endpoint_returns_404_for_unknown_document(client) -> None:
    response = client.delete("/api/v1/documents/missing-doc")

    assert response.status_code == 404
    assert "was not found" in response.json()["detail"]
