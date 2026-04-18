"use client";

import { motion } from "framer-motion";
import { Bot, FileSearch, ScrollText, User, X } from "lucide-react";
import { useState } from "react";

import type { ChatMessage } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { CitationCard } from "./citation-card";

export function MessageBubble({ message }: { message: ChatMessage }) {
  const [isEvidenceOpen, setIsEvidenceOpen] = useState(false);

  if (message.role === "user") {
    return (
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -12 }}
        className="flex justify-end"
      >
        <div className="max-w-[80%] rounded-[26px] border border-white/[0.08] bg-white/[0.05] px-5 py-4">
          <div className="mb-2 flex items-center justify-end gap-2 text-xs uppercase tracking-[0.24em] text-slate-500">
            <span>You</span>
            <User className="h-3.5 w-3.5" />
          </div>
          <p className="text-sm leading-7 text-slate-100">{message.content}</p>
        </div>
      </motion.div>
    );
  }

  const hasEvidence = message.citations.length > 0 || message.retrievedChunks.length > 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      className="space-y-3"
    >
      <div className="max-w-[90%] rounded-[28px] border border-accent/[0.14] bg-[linear-gradient(180deg,rgba(103,212,255,0.12),rgba(114,107,255,0.06))] px-5 py-5 shadow-[0_10px_35px_rgba(72,130,255,0.10)]">
        <div className="mb-3 flex items-center gap-2 text-xs uppercase tracking-[0.24em] text-accent">
          <Bot className="h-3.5 w-3.5" />
          <span>DocuMind</span>
        </div>
        <p className="text-sm leading-8 text-slate-100">{message.answer}</p>
      </div>

      {hasEvidence ? (
        <div className="ml-1 rounded-[22px] border border-white/[0.08] bg-white/[0.03] p-4">
          <div className="flex items-center justify-between gap-3">
            <span className="flex items-center gap-2 text-sm font-medium text-white">
              <FileSearch className="h-4 w-4 text-accent" />
              Sources and evidence
            </span>
            {isEvidenceOpen ? (
              <Button variant="ghost" size="sm" className="gap-2" onClick={() => setIsEvidenceOpen(false)}>
                <X className="h-4 w-4" />
                Close
              </Button>
            ) : (
              <Button variant="ghost" size="sm" onClick={() => setIsEvidenceOpen(true)}>
                Show
              </Button>
            )}
          </div>

          {isEvidenceOpen ? (
            <div className="mt-4 space-y-4">
              {message.citations.length > 0 ? (
                <div>
                  <p className="text-[11px] uppercase tracking-[0.22em] text-slate-500">Citations</p>
                  <div className="mt-3 space-y-3">
                    {message.citations.map((citation) => (
                      <CitationCard key={citation.chunk_id} citation={citation} />
                    ))}
                  </div>
                </div>
              ) : null}

              {message.retrievedChunks.length > 0 ? (
                <div className={message.citations.length > 0 ? "border-t border-white/[0.08] pt-4" : ""}>
                  <p className="flex items-center gap-2 text-[11px] uppercase tracking-[0.22em] text-slate-500">
                    <ScrollText className="h-3.5 w-3.5" />
                    Supporting chunks
                  </p>
                  <div className="mt-3 space-y-3">
                    {message.retrievedChunks.slice(0, 3).map((chunk) => (
                      <div key={chunk.chunk_id} className="rounded-[20px] border border-white/[0.08] bg-[#101013] p-4">
                        <div className="flex flex-wrap items-center gap-2 text-xs uppercase tracking-[0.18em] text-slate-500">
                          <span>{chunk.filename}</span>
                          <span>{`chunk ${chunk.chunk_index}`}</span>
                          {chunk.page_number !== null ? <span>{`page ${chunk.page_number}`}</span> : null}
                        </div>
                        <p className="mt-3 text-sm leading-7 text-slate-200">{chunk.preview || chunk.text}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      ) : null}
    </motion.div>
  );
}
