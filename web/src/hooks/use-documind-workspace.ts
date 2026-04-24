"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect } from "react";

import {
  abortPendingDocuMindRequests,
  fetchDocumentSummaryRequest,
  fetchSystemStatus,
  indexDocumentsRequest,
  isAbortError,
  removeDocumentRequest,
  resetWorkspaceRequest,
  searchDocumentsRequest,
  sendChatQueryRequest,
  uploadDocumentsRequest
} from "@/lib/api";
import type {
  ChatMessage,
  RetrievalMatchResponse,
  SystemStatusResponse,
  UploadedDocumentResponse,
  WorkspaceSummary
} from "@/lib/types";
import { createMessageId, createSessionId } from "@/lib/utils";
import { useWorkspaceStore } from "@/store/workspace-store";

export type WorkspaceSnapshot = {
  sessionId: string;
  hasHydrated: boolean;
  documents: UploadedDocumentResponse[];
  indexedChunkCount: number;
  searchResults: RetrievalMatchResponse[];
  messages: ChatMessage[];
  summary: WorkspaceSummary | null;
};

export type WorkspaceActions = {
  uploadDocuments: (params: {
    files: File[];
    chunkingStrategy: "recursive" | "fixed";
    chunkSize: number;
    chunkOverlap: number;
  }) => Promise<void>;
  indexDocuments: (documentIds?: string[]) => Promise<void>;
  searchDocuments: (query: string, topK: number) => Promise<void>;
  sendChatQuery: (query: string, topK: number) => Promise<void>;
  generateSummary: () => Promise<void>;
  removeDocument: (documentId: string) => Promise<void>;
  resetSession: () => void;
  clearWorkspace: () => Promise<void>;
  isUploading: boolean;
  isIndexing: boolean;
  isSearching: boolean;
  isChatting: boolean;
  isSummarizing: boolean;
  isRemovingDocument: boolean;
  isResetting: boolean;
  systemStatus?: SystemStatusResponse;
  statusSummary: string;
};

export function useWorkspaceState(): WorkspaceSnapshot {
  const hasHydrated = useWorkspaceStore((state) => state.hasHydrated);
  const sessionId = useWorkspaceStore((state) => state.sessionId);
  const documents = useWorkspaceStore((state) => state.documents);
  const indexedChunkCount = useWorkspaceStore((state) => state.indexedChunkCount);
  const searchResults = useWorkspaceStore((state) => state.searchResults);
  const messages = useWorkspaceStore((state) => state.messages);
  const summary = useWorkspaceStore((state) => state.summary);

  return {
    hasHydrated,
    sessionId,
    documents,
    indexedChunkCount,
    searchResults,
    messages,
    summary
  };
}

export function useWorkspaceActions(): WorkspaceActions {
  const hasHydrated = useWorkspaceStore((state) => state.hasHydrated);
  const ensureSessionId = useWorkspaceStore((state) => state.ensureSessionId);
  const documents = useWorkspaceStore((state) => state.documents);
  const indexedChunkCount = useWorkspaceStore((state) => state.indexedChunkCount);
  const setIndexedChunkCount = useWorkspaceStore((state) => state.setIndexedChunkCount);
  const setSearchResults = useWorkspaceStore((state) => state.setSearchResults);
  const setSummary = useWorkspaceStore((state) => state.setSummary);
  const appendMessage = useWorkspaceStore((state) => state.appendMessage);
  const resetSession = useWorkspaceStore((state) => state.resetSession);
  const clearWorkspace = useWorkspaceStore((state) => state.clearWorkspace);

  useEffect(() => {
    useWorkspaceStore.persist.rehydrate();
  }, []);

  useEffect(() => {
    if (hasHydrated) {
      ensureSessionId();
    }
  }, [ensureSessionId, hasHydrated]);

  const systemStatusQuery = useQuery({
    queryKey: ["system-status"],
    queryFn: fetchSystemStatus
  });

  const uploadMutation = useMutation({
    mutationFn: async ({
      files,
      chunkingStrategy,
      chunkSize,
      chunkOverlap
    }: {
      files: File[];
      chunkingStrategy: "recursive" | "fixed";
      chunkSize: number;
      chunkOverlap: number;
    }) => {
      const uploadResult = await uploadDocumentsRequest({
        files,
        chunkingStrategy,
        chunkSize,
        chunkOverlap
      });
      const documentIds = uploadResult.documents.map((document) => document.document_id);
      const indexResult = await indexDocumentsRequest(documentIds);
      return { uploadResult, indexResult };
    },
    onSuccess: ({ uploadResult, indexResult }) => {
      useWorkspaceStore.setState((state) => ({
        documents: [...state.documents, ...uploadResult.documents],
        indexedChunkCount: indexResult.total_chunks_indexed,
        summary: null
      }));
    }
  });

  const indexMutation = useMutation({
    mutationFn: indexDocumentsRequest,
    onSuccess: (result) => {
      setIndexedChunkCount(result.total_chunks_indexed);
    }
  });

  const searchMutation = useMutation({
    mutationFn: ({ query, topK }: { query: string; topK: number }) => searchDocumentsRequest(query, topK),
    onSuccess: (result) => {
      setSearchResults(result.matches);
    }
  });

  const chatMutation = useMutation({
    mutationFn: ({ query, topK }: { query: string; topK: number }) =>
      sendChatQueryRequest(useWorkspaceStore.getState().sessionId, query, topK),
    onMutate: async ({ query }) => {
      appendMessage({
        id: createMessageId(),
        role: "user",
        content: query,
        answer: "",
        citations: [],
        retrievedChunks: [],
        confidenceScore: 0
      });
    },
    onSuccess: (result) => {
      appendMessage({
        id: createMessageId(),
        role: "assistant",
        content: "",
        answer: result.answer,
        citations: result.citations,
        retrievedChunks: result.retrieved_chunks,
        confidenceScore: result.confidence_score
      });
      setSearchResults(result.retrieved_chunks);
    },
    onError: (error) => {
      if (isAbortError(error)) {
        return;
      }
    }
  });

  const resetWorkspaceMutation = useMutation({
    mutationFn: resetWorkspaceRequest,
    onError: (error) => {
      if (isAbortError(error)) {
        return;
      }
    }
  });

  const summaryMutation = useMutation({
    mutationFn: async () => fetchDocumentSummaryRequest(useWorkspaceStore.getState().documents.map((document) => document.document_id)),
    onSuccess: (result) => {
      setSummary({
        answer: result.answer,
        confidenceScore: result.confidence_score,
        citations: result.citations,
        retrievedChunks: result.retrieved_chunks,
        suggestedQuestions: result.suggested_questions
      });
    },
    onError: (error) => {
      if (isAbortError(error)) {
        return;
      }
    }
  });

  const removeDocumentMutation = useMutation({
    mutationFn: removeDocumentRequest,
    onSuccess: (result, documentId) => {
      useWorkspaceStore.setState((state) => ({
        sessionId: createSessionId(),
        documents: state.documents.filter((document) => document.document_id !== documentId),
        indexedChunkCount: result.total_chunks_indexed,
        searchResults: [],
        messages: [],
        summary: null
      }));
    },
    onError: (error) => {
      if (isAbortError(error)) {
        return;
      }
    }
  });

  const statusSummary =
    documents.length === 0
      ? "No source documents yet"
      : indexedChunkCount > 0
        ? "Workspace indexed and ready"
        : uploadMutation.isPending
          ? "Uploading and indexing documents"
          : "Preparing documents";

  return {
    uploadDocuments: async ({ files, chunkingStrategy, chunkSize, chunkOverlap }) => {
      await uploadMutation.mutateAsync({ files, chunkingStrategy, chunkSize, chunkOverlap });
    },
    indexDocuments: async (documentIds) => {
      await indexMutation.mutateAsync(documentIds);
    },
    searchDocuments: async (query, topK) => {
      await searchMutation.mutateAsync({ query, topK });
    },
    sendChatQuery: async (query, topK) => {
      await chatMutation.mutateAsync({ query, topK });
    },
    generateSummary: async () => {
      await summaryMutation.mutateAsync();
    },
    removeDocument: async (documentId) => {
      abortPendingDocuMindRequests();
      chatMutation.reset();
      searchMutation.reset();
      summaryMutation.reset();
      await removeDocumentMutation.mutateAsync(documentId);
    },
    resetSession: () => {
      abortPendingDocuMindRequests();
      chatMutation.reset();
      searchMutation.reset();
      summaryMutation.reset();
      resetSession(createSessionId());
    },
    clearWorkspace: async () => {
      abortPendingDocuMindRequests();
      chatMutation.reset();
      searchMutation.reset();
      summaryMutation.reset();
      indexMutation.reset();
      uploadMutation.reset();
      clearWorkspace();
      try {
        await resetWorkspaceMutation.mutateAsync();
      } catch (error) {
        if (!isAbortError(error)) {
          throw error;
        }
      }
    },
    isUploading: uploadMutation.isPending,
    isIndexing: indexMutation.isPending,
    isSearching: searchMutation.isPending,
    isChatting: chatMutation.isPending,
    isSummarizing: summaryMutation.isPending,
    isRemovingDocument: removeDocumentMutation.isPending,
    isResetting: resetWorkspaceMutation.isPending,
    systemStatus: systemStatusQuery.data,
    statusSummary
  };
}
