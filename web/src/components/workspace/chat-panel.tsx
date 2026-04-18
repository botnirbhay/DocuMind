"use client";

import { AnimatePresence, motion } from "framer-motion";
import { CircleHelp, CornerDownLeft, Orbit, ScrollText, Sparkles, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { Surface } from "@/components/ui/surface";
import type { WorkspaceActions, WorkspaceSnapshot } from "@/hooks/use-documind-workspace";
import { getGroundingMeta } from "@/lib/grounding";
import { buildSuggestedQuestions } from "@/lib/suggestions";
import { CitationCard } from "./citation-card";
import { MessageBubble } from "./message-bubble";

export function ChatPanel({
  state,
  sendChatQuery,
  generateSummary,
  isChatting,
  isSummarizing
}: Pick<WorkspaceActions, "sendChatQuery" | "generateSummary" | "isChatting" | "isSummarizing"> & {
  state: WorkspaceSnapshot;
}) {
  const [prompt, setPrompt] = useState("");
  const [topK, setTopK] = useState(4);
  const [isSummaryEvidenceOpen, setIsSummaryEvidenceOpen] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const lastAutoSummaryKeyRef = useRef<string>("");

  const autoSummaryKey = `${state.documents.map((document) => document.document_id).join("|")}::${state.indexedChunkCount}`;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [isChatting, state.messages.length]);

  useEffect(() => {
    if (state.indexedChunkCount === 0) {
      lastAutoSummaryKeyRef.current = "";
      return;
    }

    if (
      state.indexedChunkCount > 0 &&
      !state.summary &&
      !isSummarizing &&
      lastAutoSummaryKeyRef.current !== autoSummaryKey
    ) {
      lastAutoSummaryKeyRef.current = autoSummaryKey;
      void generateSummary();
    }
  }, [autoSummaryKey, generateSummary, isSummarizing, state.indexedChunkCount, state.summary]);

  const onSubmit = async () => {
    const trimmed = prompt.trim();
    if (!trimmed) return;
    await sendChatQuery(trimmed, topK);
    setPrompt("");
  };

  const latestAssistant = [...state.messages].reverse().find((message) => message.role === "assistant");
  const grounding = latestAssistant ? getGroundingMeta(latestAssistant.confidenceScore, latestAssistant.answer) : null;
  const summaryGrounding = state.summary
    ? getGroundingMeta(state.summary.confidenceScore, state.summary.answer)
    : null;
  const suggestedQuestions = buildSuggestedQuestions(state.documents, state.summary);
  const isEmpty = state.messages.length === 0;
  const hasSummaryEvidence = Boolean(state.summary && (state.summary.citations.length > 0 || state.summary.retrievedChunks.length > 0));

  return (
    <Surface className="relative overflow-hidden rounded-[34px] p-5 md:p-6">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(103,212,255,0.08),transparent_34%)]" />

      <div className="relative mb-5 flex flex-col gap-4 border-b border-white/[0.08] pb-5 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Grounded chat</p>
          <h2 className="mt-2 font-[var(--font-display)] text-2xl font-semibold text-slate-100">Ask your document set</h2>
          <p className="mt-2 max-w-2xl text-sm leading-7 text-slate-300">
            Answers stay tied to retrieved context. Citations and supporting chunks stay attached to each response.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <StatusBadge
            label={state.documents.length > 0 ? "Documents loaded" : "No documents"}
            tone={state.documents.length > 0 ? "success" : "warning"}
          />
          <StatusBadge
            label={state.indexedChunkCount > 0 ? "Ready to answer" : "Preparing documents"}
            tone={state.indexedChunkCount > 0 ? "success" : "warning"}
          />
          {grounding ? <StatusBadge label={grounding.label} tone={grounding.tone} /> : null}
        </div>
      </div>

      <div className="relative flex min-h-[620px] flex-col gap-5">
        {state.indexedChunkCount > 0 ? (
          <div className="rounded-[28px] border border-white/[0.08] bg-[linear-gradient(180deg,rgba(255,255,255,0.04),rgba(255,255,255,0.02))] p-5">
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Workspace summary</p>
                <h3 className="mt-2 font-[var(--font-display)] text-xl font-semibold text-slate-100">
                  High-level overview of the indexed document set
                </h3>
                <p className="mt-2 max-w-2xl text-sm leading-7 text-slate-300">
                  Useful for large uploads before you start asking detailed questions.
                </p>
              </div>
              <div className="flex items-center gap-2">
                {isSummarizing ? <StatusBadge label="Generating summary" tone="default" /> : null}
                {summaryGrounding ? <StatusBadge label={summaryGrounding.label} tone={summaryGrounding.tone} /> : null}
              </div>
            </div>

            {isSummarizing && !state.summary ? (
              <div className="mt-4 space-y-3">
                <LoadingSkeleton className="h-24 w-full rounded-[22px]" />
                <LoadingSkeleton className="h-16 w-4/5 rounded-[22px]" />
              </div>
            ) : state.summary ? (
              <div className="mt-4 space-y-4">
                <div className="rounded-[24px] border border-white/[0.08] bg-[#101013] p-5">
                  <div className="mb-3 flex items-center gap-2 text-xs uppercase tracking-[0.22em] text-accent">
                    <ScrollText className="h-3.5 w-3.5" />
                    Summary
                  </div>
                  <p className="text-sm leading-8 text-slate-100">{state.summary.answer}</p>
                </div>

                {hasSummaryEvidence ? (
                  <div className="rounded-[22px] border border-white/[0.08] bg-white/[0.03] p-4">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm font-medium text-white">Summary evidence</span>
                      {isSummaryEvidenceOpen ? (
                        <Button variant="ghost" size="sm" className="gap-2" onClick={() => setIsSummaryEvidenceOpen(false)}>
                          <X className="h-4 w-4" />
                          Close
                        </Button>
                      ) : (
                        <Button variant="ghost" size="sm" onClick={() => setIsSummaryEvidenceOpen(true)}>
                          Show
                        </Button>
                      )}
                    </div>

                    {isSummaryEvidenceOpen ? (
                      <div className="mt-4 space-y-4">
                        {state.summary.citations.length > 0 ? (
                          <div>
                            <p className="text-[11px] uppercase tracking-[0.22em] text-slate-500">Citations</p>
                            <div className="mt-3 space-y-3">
                              {state.summary.citations.map((citation) => (
                                <CitationCard key={citation.chunk_id} citation={citation} />
                              ))}
                            </div>
                          </div>
                        ) : null}
                        {state.summary.retrievedChunks.length > 0 ? (
                          <div className={state.summary.citations.length > 0 ? "border-t border-white/[0.08] pt-4" : ""}>
                            <p className="text-[11px] uppercase tracking-[0.22em] text-slate-500">Supporting chunks</p>
                            <div className="mt-3 space-y-3">
                              {state.summary.retrievedChunks.slice(0, 3).map((chunk) => (
                                <div
                                  key={chunk.chunk_id}
                                  className="rounded-[20px] border border-white/[0.08] bg-[#101013] p-4"
                                >
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
              </div>
            ) : null}
          </div>
        ) : null}

        <div className="min-h-0 flex-1 overflow-y-auto pr-1">
          {isEmpty ? (
            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              className="mx-auto grid max-w-4xl gap-4 lg:grid-cols-[1.2fr_0.8fr]"
            >
              <div className="rounded-[30px] border border-white/[0.08] bg-[linear-gradient(180deg,rgba(255,255,255,0.04),rgba(255,255,255,0.02))] p-7">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/[0.12] text-accent shadow-[0_0_30px_rgba(103,212,255,0.14)]">
                  <Sparkles className="h-5 w-5" />
                </div>
                <h3 className="mt-5 max-w-xl font-[var(--font-display)] text-2xl font-semibold text-slate-100">
                  Start with a question that is clearly present in your documents.
                </h3>
                <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-300">
                  Best results come from concrete prompts about dates, deadlines, named entities, amounts, or policy
                  rules already visible in the uploaded files.
                </p>
                {state.indexedChunkCount === 0 ? null : suggestedQuestions.length > 0 ? (
                  <div className="mt-6 flex flex-wrap gap-2">
                    {suggestedQuestions.map((suggestion) => (
                      <button
                        key={suggestion}
                        type="button"
                        onClick={() => setPrompt(suggestion)}
                        className="rounded-full border border-white/[0.10] bg-white/[0.03] px-4 py-2 text-sm text-slate-300 transition hover:border-accent/[0.30] hover:bg-white/[0.05] hover:text-slate-100"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="mt-6 rounded-[22px] border border-dashed border-white/[0.08] bg-white/[0.02] px-4 py-4 text-sm text-slate-400">
                    DocuMind is generating document-aware question suggestions from your uploaded files.
                  </div>
                )}
              </div>

              <div className="rounded-[30px] border border-white/[0.08] bg-[#101013] p-6">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/[0.04] text-accent">
                    <Orbit className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-100">Grounding first</p>
                    <p className="text-sm text-slate-400">The workspace is optimized for evidence-backed answers.</p>
                  </div>
                </div>
                <div className="mt-5 space-y-3">
                  <div className="rounded-[22px] border border-white/[0.08] bg-white/[0.03] p-4">
                    <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Ask about</p>
                    <p className="mt-2 text-sm leading-7 text-slate-300">
                      timelines, launch dates, owners, limits, support hours, thresholds
                    </p>
                  </div>
                  <div className="rounded-[22px] border border-white/[0.08] bg-white/[0.03] p-4">
                    <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Avoid asking</p>
                    <p className="mt-2 text-sm leading-7 text-slate-300">
                      general world knowledge that does not exist in the uploaded document set
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>
          ) : (
            <AnimatePresence initial={false}>
              <div className="space-y-4">
                {state.messages.map((message) => (
                  <MessageBubble key={message.id} message={message} />
                ))}
                {isChatting ? (
                  <div className="space-y-3">
                    <LoadingSkeleton className="h-20 w-4/5 rounded-[24px]" />
                    <LoadingSkeleton className="h-24 w-3/5 rounded-[24px]" />
                  </div>
                ) : null}
                <div ref={bottomRef} />
              </div>
            </AnimatePresence>
          )}
        </div>

        <div className="rounded-[28px] border border-white/[0.08] bg-[#101013]/95 p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
          <div className="mb-3 flex items-center justify-between">
            <label htmlFor="chat-input" className="text-sm font-medium text-slate-300">
              Prompt
            </label>
            <div className="flex items-center gap-2">
              <div className="group relative flex items-center gap-1">
                <span className="text-xs uppercase tracking-[0.2em] text-slate-500">K</span>
                <CircleHelp className="h-3.5 w-3.5 text-slate-500" />
                <div className="pointer-events-none absolute right-0 top-6 z-10 hidden w-56 rounded-2xl border border-white/[0.08] bg-[#111114] p-3 text-xs leading-6 text-slate-300 shadow-[0_18px_50px_rgba(0,0,0,0.35)] group-hover:block">
                  K controls how many source chunks DocuMind pulls in before answering. Lower values are tighter. Higher
                  values add more context.
                </div>
              </div>
              <select
                value={topK}
                onChange={(event) => setTopK(Number(event.target.value))}
                className="rounded-full border border-white/[0.10] bg-[#111114] px-3 py-1.5 text-sm text-slate-100 outline-none"
                style={{ colorScheme: "dark" }}
              >
                {[3, 4, 5, 6, 8].map((value) => (
                  <option key={value} value={value} className="bg-[#111114] text-slate-100">
                    {value}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex flex-col gap-3 md:flex-row md:items-end">
            <textarea
              id="chat-input"
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              placeholder="Ask a grounded question about your uploaded documents..."
              className="min-h-[110px] flex-1 rounded-[24px] border border-white/[0.08] bg-white/[0.02] px-4 py-4 text-sm text-slate-100 outline-none placeholder:text-slate-500 focus:border-accent/[0.35]"
            />
            <Button
              size="md"
              className="gap-2 md:h-[46px] md:min-w-[140px]"
              onClick={onSubmit}
              disabled={isChatting || state.indexedChunkCount === 0 || prompt.trim().length === 0}
            >
              Ask DocuMind
              <CornerDownLeft className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </Surface>
  );
}
