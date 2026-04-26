from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="DocuMind", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    api_v1_prefix: str = "/api/v1"
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    llm_provider: str = Field(default="ollama", alias="LLM_PROVIDER")
    ollama_base_url: str = Field(default="http://127.0.0.1:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="qwen2.5:7b-instruct", alias="OLLAMA_MODEL")
    ollama_timeout_seconds: float = Field(default=60.0, alias="OLLAMA_TIMEOUT_SECONDS")
    ollama_temperature: float = Field(default=0.0, alias="OLLAMA_TEMPERATURE")
    ollama_keep_alive: str = Field(default="10m", alias="OLLAMA_KEEP_ALIVE")

    embedding_provider: str = Field(default="sentence-transformers", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL",
    )
    reranker_provider: str = Field(default="none", alias="RERANKER_PROVIDER")
    reranker_model: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        alias="RERANKER_MODEL",
    )
    vector_store_provider: str = Field(default="faiss", alias="VECTOR_STORE_PROVIDER")

    data_dir: Path = Field(default=Path("./data"), alias="DATA_DIR")
    upload_dir: Path = Field(default=Path("./data/uploads"), alias="UPLOAD_DIR")
    vector_index_dir: Path = Field(default=Path("./data/vector_index"), alias="VECTOR_INDEX_DIR")
    eval_log_path: Path = Field(default=Path("./data/logs/evaluations.jsonl"), alias="EVAL_LOG_PATH")

    max_upload_size_mb: int = Field(default=25, alias="MAX_UPLOAD_SIZE_MB")
    default_top_k: int = Field(default=5, alias="DEFAULT_TOP_K")
    default_chunk_size: int = Field(default=800, alias="DEFAULT_CHUNK_SIZE")
    default_chunk_overlap: int = Field(default=120, alias="DEFAULT_CHUNK_OVERLAP")
    minimum_grounding_score: float = Field(default=0.2, alias="MINIMUM_GROUNDING_SCORE")
    request_log_enabled: bool = Field(default=True, alias="REQUEST_LOG_ENABLED")
    frontend_backend_url: str = Field(default="http://127.0.0.1:8000", alias="DOCUMIND_API_URL")

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, value: str) -> str:
        allowed = {"extractive", "ollama"}
        if value not in allowed:
            raise ValueError(f"Unsupported LLM_PROVIDER '{value}'. Supported values: {sorted(allowed)}.")
        return value

    @field_validator("embedding_provider")
    @classmethod
    def validate_embedding_provider(cls, value: str) -> str:
        allowed = {"sentence-transformers", "hash"}
        if value not in allowed:
            raise ValueError(f"Unsupported EMBEDDING_PROVIDER '{value}'. Supported values: {sorted(allowed)}.")
        return value

    @field_validator("reranker_provider")
    @classmethod
    def validate_reranker_provider(cls, value: str) -> str:
        allowed = {"sentence-transformers", "none"}
        if value not in allowed:
            raise ValueError(f"Unsupported RERANKER_PROVIDER '{value}'. Supported values: {sorted(allowed)}.")
        return value

    @field_validator("vector_store_provider")
    @classmethod
    def validate_vector_store_provider(cls, value: str) -> str:
        allowed = {"faiss"}
        if value not in allowed:
            raise ValueError(f"Unsupported VECTOR_STORE_PROVIDER '{value}'. Supported values: {sorted(allowed)}.")
        return value


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.vector_index_dir.mkdir(parents=True, exist_ok=True)
    settings.eval_log_path.parent.mkdir(parents=True, exist_ok=True)
    return settings
