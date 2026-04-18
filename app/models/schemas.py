from pydantic import AliasChoices, BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["ok"])
    service: str = Field(..., examples=["documind-api"])


class ServiceStatus(BaseModel):
    name: str
    configured: bool
    provider: str | None = None


class SystemStatusResponse(BaseModel):
    app_name: str
    environment: str
    llm_provider: str
    embedding_provider: str
    vector_store_provider: str
    services: list[ServiceStatus]


class PlaceholderResponse(BaseModel):
    detail: str


class UploadedDocumentResponse(BaseModel):
    document_id: str
    filename: str
    file_type: str
    chunks_extracted: int
    status: str


class DocumentUploadResponse(BaseModel):
    documents: list[UploadedDocumentResponse]


class DocumentIndexRequest(BaseModel):
    document_ids: list[str] | None = None


class IndexedDocumentResponse(BaseModel):
    document_id: str
    filename: str
    chunks_indexed: int


class DocumentIndexResponse(BaseModel):
    status: str
    indexed_documents: list[IndexedDocumentResponse]
    total_chunks_indexed: int


class RetrievalSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=25)


class RetrievalMatchResponse(BaseModel):
    chunk_id: str
    chunk_index: int
    document_id: str
    filename: str
    page_number: int | None = None
    score: float
    text: str
    preview: str


class RetrievalSearchResponse(BaseModel):
    query: str
    top_k: int
    matches: list[RetrievalMatchResponse]


class CitationResponse(BaseModel):
    chunk_id: str
    chunk_index: int
    document_id: str
    filename: str
    page_number: int | None = None
    snippet: str
    score: float


class ChatQueryRequest(BaseModel):
    session_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("session_id", "conversation_id"),
    )
    user_query: str = Field(..., min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=25)


class ChatQueryResponse(BaseModel):
    session_id: str
    answer: str
    confidence_score: float
    citations: list[CitationResponse]
    retrieved_chunks: list[RetrievalMatchResponse]
