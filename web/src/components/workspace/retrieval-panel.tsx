"use client";

import { Search, Telescope } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { Surface } from "@/components/ui/surface";
import type { WorkspaceActions, WorkspaceSnapshot } from "@/hooks/use-documind-workspace";
import { getRelevanceTone } from "@/lib/grounding";

export function RetrievalPanel({
  state,
  searchDocuments,
  isSearching
}: Pick<WorkspaceActions, "searchDocuments" | "isSearching"> & { state: WorkspaceSnapshot }) {
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);

  const onSearch = async () => {
    const trimmed = query.trim();
    if (!trimmed) return;
    await searchDocuments(trimmed, topK);
  };

  return (
    <Surface className="rounded-[30px] p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Retrieval layer</p>
          <h3 className="mt-2 font-[var(--font-display)] text-xl font-semibold text-slate-100">Search preview</h3>
        </div>
        <Telescope className="h-5 w-5 text-accent" />
      </div>

      <div className="rounded-[22px] border border-white/[0.08] bg-white/[0.03] p-4">
        <label className="mb-2 block text-sm font-medium text-slate-300">Search query</label>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Find names, dates, conditions, or clauses..."
              className="w-full rounded-full border border-white/[0.08] bg-[#111114] px-11 py-3 text-sm text-slate-100 outline-none placeholder:text-slate-500 focus:border-accent/[0.35]"
            />
          </div>
          <select
            value={topK}
            onChange={(event) => setTopK(Number(event.target.value))}
            className="rounded-full border border-white/[0.08] bg-[#111114] px-3 py-3 text-sm text-slate-100 outline-none"
          >
            {[3, 4, 5, 6, 8].map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </div>
        <Button
          variant="secondary"
          className="mt-3 w-full"
          onClick={onSearch}
          disabled={isSearching || state.indexedChunkCount === 0 || query.trim().length === 0}
        >
          {isSearching ? "Searching..." : "Preview matches"}
        </Button>
      </div>

      <div className="mt-4 space-y-3">
        {isSearching ? (
          <>
            <LoadingSkeleton className="h-28 rounded-[22px]" />
            <LoadingSkeleton className="h-28 rounded-[22px]" />
          </>
        ) : state.searchResults.length === 0 ? (
          <div className="rounded-[24px] border border-white/[0.08] bg-white/[0.03] p-5 text-sm leading-7 text-slate-300">
            {state.documents.length === 0
              ? "Upload source documents to unlock retrieval preview."
              : "Run a retrieval query to inspect which chunks the backend thinks are most relevant."}
          </div>
        ) : (
          state.searchResults.map((match) => {
            const relevance = getRelevanceTone(match.score);

            return (
              <div key={match.chunk_id} className="rounded-[24px] border border-white/[0.08] bg-[#111114] p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="font-medium text-slate-100">{match.filename}</p>
                    <p className="mt-1 text-xs uppercase tracking-[0.2em] text-slate-500">
                      {`chunk ${match.chunk_index}${match.page_number !== null ? ` • page ${match.page_number}` : ""}`}
                    </p>
                  </div>
                  <StatusBadge label={relevance.label} tone={relevance.tone} />
                </div>
                <p className="mt-3 text-sm leading-7 text-slate-200">{match.text}</p>
                <p className="mt-3 text-xs text-slate-500">Document id {match.document_id}</p>
              </div>
            );
          })
        )}
      </div>
    </Surface>
  );
}
