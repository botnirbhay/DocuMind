import pytest

from app.utils.config import Settings


def test_settings_reject_invalid_embedding_provider() -> None:
    with pytest.raises(ValueError):
        Settings(EMBEDDING_PROVIDER="unknown-provider")


def test_settings_defaults_are_sensible() -> None:
    settings = Settings()

    assert settings.llm_provider == "ollama"
    assert settings.ollama_model == "qwen2.5:7b-instruct"
    assert settings.embedding_provider == "sentence-transformers"
    assert settings.default_top_k == 5
    assert settings.request_log_enabled is True
