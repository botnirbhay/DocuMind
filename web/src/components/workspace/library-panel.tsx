"use client";

import { FileStack, Trash2 } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Surface } from "@/components/ui/surface";
import type { WorkspaceSnapshot } from "@/hooks/use-documind-workspace";

export function LibraryPanel({
  state,
  onClearWorkspace,
  isResetting
}: {
  state: WorkspaceSnapshot;
  onClearWorkspace: () => void | Promise<void>;
  isResetting: boolean;
}) {
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);

  const onClear = async () => {
    await onClearWorkspace();
    setIsConfirmOpen(false);
  };

  return (
    <Surface className="rounded-[30px] p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Source library</p>
          <h3 className="mt-2 font-[var(--font-display)] text-xl font-semibold text-slate-100">Uploaded documents</h3>
        </div>
        <FileStack className="h-5 w-5 text-accent" />
      </div>

      {state.documents.length === 0 ? (
        <div className="rounded-[24px] border border-white/[0.08] bg-white/[0.03] p-5 text-sm leading-7 text-slate-300">
          Your uploaded documents will appear here. Use this list to keep track of what is currently available in the
          workspace.
        </div>
      ) : (
        <div className="space-y-3">
          {state.documents.map((document) => (
            <div key={document.document_id} className="rounded-[22px] border border-white/[0.08] bg-white/[0.03] p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-medium text-slate-100">{document.filename}</p>
                  <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">
                    {`${document.file_type.toUpperCase()} • ${document.chunks_extracted} chunks`}
                  </p>
                </div>
                <span className="rounded-full border border-white/[0.08] bg-white/[0.05] px-3 py-1 text-xs text-slate-300">
                  {document.status}
                </span>
              </div>
              <p className="mt-3 text-xs text-slate-500">{document.document_id}</p>
            </div>
          ))}
        </div>
      )}

      <Button
        variant="ghost"
        className="mt-4 w-full gap-2 text-slate-300 hover:text-white"
        onClick={() => setIsConfirmOpen(true)}
        disabled={isResetting}
      >
        <Trash2 className={`h-4 w-4 ${isResetting ? "animate-pulse" : ""}`} />
        {isResetting ? "Clearing workspace..." : "Clear all documents"}
      </Button>

      <ConfirmDialog
        open={isConfirmOpen}
        title="Remove all documents?"
        description="This clears every uploaded file from the current workspace and resets the current chat session."
        confirmLabel="Clear workspace"
        isConfirming={isResetting}
        onClose={() => setIsConfirmOpen(false)}
        onConfirm={onClear}
      />
    </Surface>
  );
}
