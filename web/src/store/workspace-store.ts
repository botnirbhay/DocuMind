"use client";

import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import type { ChatMessage, RetrievalMatchResponse, UploadedDocumentResponse, WorkspaceSummary } from "@/lib/types";
import { createSessionId } from "@/lib/utils";

type WorkspaceStore = {
  sessionId: string;
  hasHydrated: boolean;
  documents: UploadedDocumentResponse[];
  indexedChunkCount: number;
  searchResults: RetrievalMatchResponse[];
  messages: ChatMessage[];
  summary: WorkspaceSummary | null;
  setHasHydrated: (value: boolean) => void;
  ensureSessionId: () => void;
  setDocuments: (documents: UploadedDocumentResponse[]) => void;
  setIndexedChunkCount: (count: number) => void;
  setSearchResults: (results: RetrievalMatchResponse[]) => void;
  setSummary: (summary: WorkspaceSummary | null) => void;
  appendMessage: (message: ChatMessage) => void;
  resetSession: (nextSessionId: string) => void;
  clearWorkspace: () => void;
};

export const useWorkspaceStore = create<WorkspaceStore>()(
  persist(
    (set) => ({
      sessionId: "",
      hasHydrated: false,
      documents: [],
      indexedChunkCount: 0,
      searchResults: [],
      messages: [],
      summary: null,
      setHasHydrated: (hasHydrated) => set({ hasHydrated }),
      ensureSessionId: () =>
        set((state) => ({
          sessionId: state.sessionId || createSessionId()
        })),
      setDocuments: (documents) => set({ documents }),
      setIndexedChunkCount: (indexedChunkCount) => set({ indexedChunkCount }),
      setSearchResults: (searchResults) => set({ searchResults }),
      setSummary: (summary) => set({ summary }),
      appendMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
      resetSession: (nextSessionId) =>
        set({
          sessionId: nextSessionId,
          messages: [],
          searchResults: []
        }),
      clearWorkspace: () =>
        set({
          sessionId: createSessionId(),
          documents: [],
          indexedChunkCount: 0,
          searchResults: [],
          messages: [],
          summary: null
        })
    }),
    {
      name: "documind-web-workspace",
      storage: createJSONStorage(() => sessionStorage),
      skipHydration: true,
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
        state?.ensureSessionId();
      },
      partialize: (state) => ({
        sessionId: state.sessionId,
        documents: state.documents,
        indexedChunkCount: state.indexedChunkCount,
        searchResults: state.searchResults,
        messages: state.messages,
        summary: state.summary
      })
    }
  )
);
