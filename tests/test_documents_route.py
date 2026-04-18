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
