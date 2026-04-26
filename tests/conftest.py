from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.utils.config import get_settings


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    data_dir = tmp_path / "data"
    monkeypatch.setenv("DATA_DIR", str(data_dir))
    monkeypatch.setenv("UPLOAD_DIR", str(data_dir / "uploads"))
    monkeypatch.setenv("VECTOR_INDEX_DIR", str(data_dir / "vector_index"))
    monkeypatch.setenv("EVAL_LOG_PATH", str(data_dir / "logs" / "evaluations.jsonl"))
    monkeypatch.setenv("LLM_PROVIDER", "extractive")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "hash")
    monkeypatch.setenv("RERANKER_PROVIDER", "none")
    get_settings.cache_clear()

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client

    get_settings.cache_clear()
