"use client";

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
        <div className="mb-4">
          <Link href="/" className="text-sm text-slate-300 transition hover:text-white">
            Back to home
          </Link>
        </div>
        <div className="grid gap-4 xl:grid-cols-[320px_minmax(0,1fr)]">
          <div className="space-y-4">
            <ControlRail {...actions} />
            <LibraryPanel
              state={state}
              onClearWorkspace={actions.clearWorkspace}
              onRemoveDocument={actions.removeDocument}
              isResetting={actions.isResetting}
              isRemovingDocument={actions.isRemovingDocument}
            />
          </div>
          <ChatPanel {...actions} state={state} />
        </div>
      </div>
    </main>
  );
}
