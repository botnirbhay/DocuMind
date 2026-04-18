export type UploadedDocumentResponse = {
  document_id: string;
  filename: string;
  file_type: string;
  chunks_extracted: number;
  status: string;
};

export type DocumentUploadResponse = {
  documents: UploadedDocumentResponse[];
};

export type IndexedDocumentResponse = {
  document_id: string;
  filename: string;
  chunks_indexed: number;
};

export type DocumentIndexResponse = {
  status: string;
  indexed_documents: IndexedDocumentResponse[];
  total_chunks_indexed: number;
};

export type ResetWorkspaceResponse = {
  status: string;
  detail: string;
  documents_cleared: number;
  sessions_cleared: number;
  uploaded_files_removed: number;
};

export type RetrievalMatchResponse = {
  chunk_id: string;
  chunk_index: number;
  document_id: string;
  filename: string;
  page_number: number | null;
  score: number;
  text: string;
  preview: string;
};

export type RetrievalSearchResponse = {
  query: string;
  top_k: number;
  matches: RetrievalMatchResponse[];
};

export type CitationResponse = {
  chunk_id: string;
  chunk_index: number;
  document_id: string;
  filename: string;
  page_number: number | null;
  snippet: string;
  score: number;
};

export type ChatQueryResponse = {
  session_id: string;
  answer: string;
  confidence_score: number;
  citations: CitationResponse[];
  retrieved_chunks: RetrievalMatchResponse[];
};

export type WorkspaceSummary = {
  answer: string;
  confidenceScore: number;
  citations: CitationResponse[];
  retrievedChunks: RetrievalMatchResponse[];
  suggestedQuestions: string[];
};

export type DocumentSummaryResponse = {
  answer: string;
  confidence_score: number;
  citations: CitationResponse[];
  retrieved_chunks: RetrievalMatchResponse[];
  suggested_questions: string[];
};

export type ServiceStatus = {
  name: string;
  configured: boolean;
  provider?: string | null;
};

export type SystemStatusResponse = {
  app_name: string;
  environment: string;
  llm_provider: string;
  embedding_provider: string;
  vector_store_provider: string;
  services: ServiceStatus[];
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  answer: string;
  citations: CitationResponse[];
  retrievedChunks: RetrievalMatchResponse[];
  confidenceScore: number;
};
