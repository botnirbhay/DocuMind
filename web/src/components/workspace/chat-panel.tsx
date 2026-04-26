"use client";

import { AnimatePresence, motion } from "framer-motion";
import { CircleHelp, CornerDownLeft, Orbit, Sparkles } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { Surface } from "@/components/ui/surface";
import type { WorkspaceActions, WorkspaceSnapshot } from "@/hooks/use-documind-workspace";
import { buildSuggestedQuestions } from "@/lib/suggestions";
import { MessageBubble } from "./message-bubble";

export function ChatPanel({
  state,
  sendChatQuery,
  isChatting
}: Pick<WorkspaceActions, "sendChatQuery" | "isChatting"> & {
  state: WorkspaceSnapshot;
}) {
  const [prompt, setPrompt] = useState("");
  const [topK, setTopK] = useState(4);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [isChatting, state.messages.length]);

  const onSubmit = async () => {
    const trimmed = prompt.trim();
    if (!trimmed) return;
    setPrompt("");
    try {
      await sendChatQuery(trimmed, topK);
    } catch {
      setPrompt(trimmed);
    }
  };

  const suggestedQuestions = buildSuggestedQuestions(state.documents, null);
  const isEmpty = state.messages.length === 0;

  return (
    <Surface className="relative overflow-hidden rounded-[34px] p-5 md:p-6">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(103,212,255,0.08),transparent_34%)]" />

      <div className="relative flex min-h-[620px] flex-col gap-5">
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
                    Ask about dates, requirements, named entities, or specific sections that appear in your documents.
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
