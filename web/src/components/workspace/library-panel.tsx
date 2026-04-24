"use client";

import { FileStack, Trash2, X } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Surface } from "@/components/ui/surface";
import type { WorkspaceSnapshot } from "@/hooks/use-documind-workspace";

export function LibraryPanel({
  state,
  onClearWorkspace,
  onRemoveDocument,
  isResetting,
  isRemovingDocument
}: {
  state: WorkspaceSnapshot;
  onClearWorkspace: () => void | Promise<void>;
  onRemoveDocument: (documentId: string) => void | Promise<void>;
  isResetting: boolean;
  isRemovingDocument: boolean;
}) {
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);

  const onClear = async () => {
    await onClearWorkspace();
    setIsConfirmOpen(false);
  };

  return (
    <Surface className="rounded-[30px] p-5">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-[var(--font-display)] text-xl font-semibold text-slate-100">Documents</h3>
        <FileStack className="h-5 w-5 text-accent" />
      </div>

      {state.documents.length === 0 ? (
        <div className="rounded-[24px] border border-white/[0.08] bg-white/[0.03] p-5 text-sm leading-7 text-slate-300">
          Your uploaded documents will appear here.
        </div>
      ) : (
        <div className="space-y-3">
          {state.documents.map((document) => (
            <div key={document.document_id} className="rounded-[22px] border border-white/[0.08] bg-white/[0.03] p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-medium text-slate-100">{document.filename}</p>
                  <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">
                    {`${document.file_type.toUpperCase()} | ${document.chunks_extracted} chunks`}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => void onRemoveDocument(document.document_id)}
                  disabled={isRemovingDocument || isResetting}
                  className="rounded-full border border-white/[0.08] bg-white/[0.03] p-2 text-slate-400 transition hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
                  aria-label={`Remove ${document.filename}`}
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <Button
        variant="ghost"
        className="mt-4 w-full gap-2 text-slate-300 hover:text-white"
        onClick={() => setIsConfirmOpen(true)}
        disabled={isResetting || state.documents.length === 0}
      >
        <Trash2 className={`h-4 w-4 ${(isResetting || isRemovingDocument) ? "animate-pulse" : ""}`} />
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
