"use client";

import { motion } from "framer-motion";
import Link from "next/link";

import { ChatPanel } from "@/components/workspace/chat-panel";
import { ControlRail } from "@/components/workspace/control-rail";
import { LibraryPanel } from "@/components/workspace/library-panel";
import { useWorkspaceActions, useWorkspaceState } from "@/hooks/use-documind-workspace";

export function WorkspaceShell() {
  const state = useWorkspaceState();
  const actions = useWorkspaceActions();

  if (!state.hasHydrated) {
    return (
      <main className="min-h-screen px-4 py-4 md:px-6 md:py-6 lg:px-8">
        <div className="mx-auto max-w-[1600px]">
          <div className="glass-panel rounded-[28px] px-5 py-5 md:px-6">
            <p className="text-sm text-slate-400">Preparing workspace...</p>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen px-4 py-4 md:px-6 md:py-6 lg:px-8">
      <div className="mx-auto max-w-[1600px]">
        <motion.header
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-5 flex flex-col gap-4 rounded-[28px] border border-white/[0.08] bg-[linear-gradient(180deg,rgba(18,18,22,0.92),rgba(10,10,12,0.9))] px-5 py-5 md:flex-row md:items-center md:justify-between md:px-6"
        >
          <div>
            <Link href="/" className="text-sm text-slate-400 transition hover:text-white">
              Back to landing
            </Link>
            <h1 className="mt-2 font-[var(--font-display)] text-3xl font-semibold text-white">Document workspace</h1>
            <p className="mt-2 max-w-2xl text-sm leading-7 text-slate-300">
              Upload files, build the index, and chat with concise answers backed by visible source evidence.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Stat label="Documents" value={String(state.documents.length)} />
            <Stat label="Indexed chunks" value={String(state.indexedChunkCount)} />
            <Stat label="Session" value={state.sessionId.slice(0, 6)} />
            <Stat label="Messages" value={String(state.messages.length)} />
          </div>
        </motion.header>

        <div className="grid gap-4 xl:grid-cols-[320px_minmax(0,1fr)]">
          <div className="space-y-4">
            <ControlRail {...actions} state={state} />
            <LibraryPanel
              state={state}
              onClearWorkspace={actions.clearWorkspace}
              isResetting={actions.isResetting}
            />
          </div>
          <ChatPanel {...actions} state={state} />
        </div>
      </div>
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[22px] border border-white/[0.08] bg-white/[0.03] px-4 py-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
      <p className="text-[11px] uppercase tracking-[0.22em] text-slate-500">{label}</p>
      <p className="mt-2 font-[var(--font-display)] text-xl font-semibold text-slate-100">{value}</p>
    </div>
  );
}
