import httpx

from frontend.services.api_client import DocuMindApiClient, DocuMindApiError, UploadPayload


def test_api_client_gets_system_status() -> None:
    client = DocuMindApiClient(
        base_url="http://testserver",
        client=httpx.Client(transport=httpx.MockTransport(_status_handler), base_url="http://testserver"),
    )

    payload = client.get_system_status()

    assert payload["app_name"] == "DocuMind"
    client.close()


def test_api_client_raises_clean_error_message() -> None:
    client = DocuMindApiClient(
        base_url="http://testserver",
        client=httpx.Client(transport=httpx.MockTransport(_error_handler), base_url="http://testserver"),
    )

    try:
        client.search_documents(query="cats", top_k=3)
    except DocuMindApiError as exc:
        assert str(exc) == "Vector index is not ready."
    else:
        raise AssertionError("Expected DocuMindApiError")
    finally:
        client.close()


def test_api_client_upload_documents_posts_multipart_data() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["content_type"] = request.headers["content-type"]
        return httpx.Response(201, json={"documents": []})

    client = DocuMindApiClient(
        base_url="http://testserver",
        client=httpx.Client(transport=httpx.MockTransport(handler), base_url="http://testserver"),
    )

    client.upload_documents(
        files=[UploadPayload(path=__import__("pathlib").Path("notes.txt"), content=b"alpha")],
        chunking_strategy="recursive",
        chunk_size=800,
        chunk_overlap=120,
    )

    assert captured["method"] == "POST"
    assert captured["path"] == "/api/v1/documents/upload"
    assert "multipart/form-data" in captured["content_type"]
    client.close()


def _status_handler(request: httpx.Request) -> httpx.Response:
    assert request.url.path == "/api/v1/system/status"
    return httpx.Response(200, json={"app_name": "DocuMind"})


def _error_handler(request: httpx.Request) -> httpx.Response:
    assert request.url.path == "/api/v1/documents/search"
    return httpx.Response(400, json={"detail": "Vector index is not ready."})
