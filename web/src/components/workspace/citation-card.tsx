"use client";

import { FileText, Hash, Layers } from "lucide-react";

import type { CitationResponse } from "@/lib/types";

export function CitationCard({ citation }: { citation: CitationResponse }) {
  return (
    <div className="rounded-[20px] border border-white/[0.08] bg-[#101013] p-4">
      <div className="flex flex-wrap items-center gap-2 text-xs uppercase tracking-[0.18em] text-slate-500">
        <span className="flex items-center gap-1.5">
          <FileText className="h-3.5 w-3.5 text-accent" />
          {citation.filename}
        </span>
        <span className="flex items-center gap-1.5">
          <Hash className="h-3.5 w-3.5" />
          chunk {citation.chunk_index}
        </span>
        {citation.page_number !== null ? (
          <span className="flex items-center gap-1.5">
            <Layers className="h-3.5 w-3.5" />
            page {citation.page_number}
          </span>
        ) : null}
      </div>
      <p className="mt-3 text-sm leading-7 text-slate-200">{citation.snippet}</p>
      <p className="mt-3 text-xs text-slate-500">{`Score ${citation.score.toFixed(2)} • ${citation.document_id}`}</p>
    </div>
  );
}
