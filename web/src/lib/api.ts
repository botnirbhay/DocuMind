import type {
  ChatQueryResponse,
  DocumentSummaryResponse,
  DocumentIndexResponse,
  DocumentUploadResponse,
  RemoveDocumentResponse,
  ResetWorkspaceResponse,
  RetrievalSearchResponse,
  SystemStatusResponse
} from "./types";

const API_PREFIX = "/api/v1";
const activeControllers = new Set<AbortController>();

export function resolveApiBaseUrl(url = process.env.NEXT_PUBLIC_DOCUMIND_API_URL) {
  return url ? url.replace(/\/+$/, "") : "";
}

export function abortPendingDocuMindRequests() {
  for (const controller of activeControllers) {
    controller.abort();
  }
  activeControllers.clear();
}

export function isAbortError(error: unknown) {
  return error instanceof DOMException && error.name === "AbortError";
}

export async function fetchSystemStatus() {
  return request<SystemStatusResponse>(`${API_PREFIX}/system/status`, {
    method: "GET"
  });
}

export async function uploadDocumentsRequest({
  files,
  chunkingStrategy,
  chunkSize,
  chunkOverlap
}: {
  files: File[];
  chunkingStrategy: "recursive" | "fixed";
  chunkSize: number;
  chunkOverlap: number;
}) {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  formData.append("chunking_strategy", chunkingStrategy);
  formData.append("chunk_size", String(chunkSize));
  formData.append("chunk_overlap", String(chunkOverlap));

  return request<DocumentUploadResponse>(`${API_PREFIX}/documents/upload`, {
    method: "POST",
    body: formData,
    abortable: true
  });
}

export async function indexDocumentsRequest(documentIds?: string[]) {
  return request<DocumentIndexResponse>(`${API_PREFIX}/documents/index`, {
    method: "POST",
    body: JSON.stringify({ document_ids: documentIds && documentIds.length > 0 ? documentIds : null }),
    headers: {
      "Content-Type": "application/json"
    },
    abortable: true
  });
}

export async function resetWorkspaceRequest() {
  return request<ResetWorkspaceResponse>(`${API_PREFIX}/documents/reset`, {
    method: "POST"
  });
}

export async function removeDocumentRequest(documentId: string) {
  return request<RemoveDocumentResponse>(`${API_PREFIX}/documents/${documentId}`, {
    method: "DELETE",
    abortable: true
  });
}

export async function searchDocumentsRequest(query: string, topK: number) {
  return request<RetrievalSearchResponse>(`${API_PREFIX}/documents/search`, {
    method: "POST",
    body: JSON.stringify({ query, top_k: topK }),
    headers: {
      "Content-Type": "application/json"
    },
    abortable: true
  });
}

export async function sendChatQueryRequest(sessionId: string, userQuery: string, topK: number) {
  return request<ChatQueryResponse>(`${API_PREFIX}/chat/query`, {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, user_query: userQuery, top_k: topK }),
    headers: {
      "Content-Type": "application/json"
    },
    abortable: true
  });
}

export async function fetchDocumentSummaryRequest(documentIds?: string[]) {
  return request<DocumentSummaryResponse>(`${API_PREFIX}/chat/summary`, {
    method: "POST",
    body: JSON.stringify({ document_ids: documentIds && documentIds.length > 0 ? documentIds : null }),
    headers: {
      "Content-Type": "application/json"
    },
    abortable: true
  });
}

async function request<T>(path: string, init: RequestInit & { abortable?: boolean }): Promise<T> {
  const controller = init.abortable ? new AbortController() : null;
  if (controller) {
    activeControllers.add(controller);
  }

  try {
    const response = await fetch(`${resolveApiBaseUrl()}${path}`, {
      ...init,
      cache: "no-store",
      signal: controller?.signal ?? init.signal
    });

    if (!response.ok) {
      throw new Error(await extractApiError(response));
    }

    return (await response.json()) as T;
  } finally {
    if (controller) {
      activeControllers.delete(controller);
    }
  }
}

export async function extractApiError(response: Response) {
  try {
    const payload = await response.json();
    if (payload && typeof payload.detail === "string") {
      return payload.detail;
    }
  } catch {
    return `Request failed with status ${response.status}.`;
  }

  return `Request failed with status ${response.status}.`;
}
