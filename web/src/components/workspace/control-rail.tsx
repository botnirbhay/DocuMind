"use client";

import { AnimatePresence, motion } from "framer-motion";
import { CircleHelp, FileUp, Sparkles } from "lucide-react";
import { useRef, useState, type ChangeEvent } from "react";

import { Button } from "@/components/ui/button";
import { Surface } from "@/components/ui/surface";
import type { WorkspaceActions } from "@/hooks/use-documind-workspace";
import { mergeSelectedFiles } from "@/lib/file-selection";

export function ControlRail({
  uploadDocuments,
  isUploading,
  isResetting
}: Pick<
  WorkspaceActions,
  | "uploadDocuments"
  | "isUploading"
  | "isResetting"
>) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [chunkingStrategy, setChunkingStrategy] = useState<"recursive" | "fixed">("recursive");
  const [chunkSize, setChunkSize] = useState(800);
  const [chunkOverlap, setChunkOverlap] = useState(120);

  const onFilesSelected = (event: ChangeEvent<HTMLInputElement>) => {
    const incomingFiles = Array.from(event.target.files ?? []);
    if (incomingFiles.length === 0) {
      return;
    }

    setSelectedFiles((current) => mergeSelectedFiles(current, incomingFiles));

    if (inputRef.current) {
      inputRef.current.value = "";
    }
  };

  const onUpload = async () => {
    if (selectedFiles.length === 0) return;
    await uploadDocuments({ files: selectedFiles, chunkingStrategy, chunkSize, chunkOverlap });
    setSelectedFiles([]);
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  };

  return (
    <Surface className="rounded-[30px] p-5">
      <div className="mb-5 flex items-start justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-accent/80">Documents</p>
          <h2 className="mt-2 font-[var(--font-display)] text-xl font-semibold text-white">Bring documents in</h2>
        </div>
        <Sparkles className="h-5 w-5 text-accent" />
      </div>

      <label className="group flex cursor-pointer flex-col gap-3 rounded-[24px] border border-dashed border-white/[0.15] bg-white/[0.03] p-4 transition hover:border-accent/[0.35] hover:bg-white/[0.05]">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-accent/10 text-accent">
          <FileUp className="h-5 w-5" />
        </div>
        <div>
          <p className="font-medium text-white">Upload source files</p>
          <p className="mt-1 text-sm leading-6 text-slate-400">
            PDF, DOCX, or TXT. Files are indexed automatically after upload.
          </p>
        </div>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.txt"
          className="hidden"
          onChange={onFilesSelected}
        />
      </label>

      <AnimatePresence initial={false}>
        {selectedFiles.length > 0 ? (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-4 overflow-hidden rounded-[22px] border border-white/[0.08] bg-white/[0.03] px-4 py-3"
          >
            <div className="mb-2 flex items-center justify-between gap-3">
              <p className="text-sm font-medium text-white">Selected files</p>
              <span className="text-xs uppercase tracking-[0.18em] text-slate-500">{selectedFiles.length} ready</span>
            </div>
            <div className="space-y-1 text-sm text-slate-300">
              {selectedFiles.map((file) => (
                <div key={`${file.name}-${file.size}`} className="flex items-center justify-between gap-3">
                  <span className="truncate">{file.name}</span>
                  <span className="text-slate-500">{Math.max(1, Math.round(file.size / 1024))} KB</span>
                </div>
              ))}
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>

      <div className="mt-5 space-y-4">
        <div>
          <label className="mb-2 block text-sm text-slate-300">Chunking strategy</label>
          <div className="grid grid-cols-2 gap-2">
            {(["recursive", "fixed"] as const).map((value) => (
              <button
                key={value}
                type="button"
                onClick={() => setChunkingStrategy(value)}
                className={`rounded-full border px-3 py-2 text-sm transition ${
                  chunkingStrategy === value
                    ? "border-accent/[0.40] bg-accent/[0.10] text-slate-100"
                    : "border-white/[0.08] bg-white/[0.03] text-slate-400 hover:text-slate-100"
                }`}
              >
                {value === "recursive" ? "Recursive" : "Fixed"}
              </button>
            ))}
          </div>
        </div>

        <RangeControl
          label="Chunk size"
          helpText="Chunk size is how much text DocuMind keeps in one searchable piece. Larger chunks keep more context, smaller chunks are more precise."
          value={chunkSize}
          min={200}
          max={1600}
          step={100}
          onChange={setChunkSize}
        />
        <RangeControl
          label="Chunk overlap"
          helpText="Chunk overlap repeats a small part of the previous chunk in the next one, which helps avoid losing meaning at chunk boundaries."
          value={chunkOverlap}
          min={0}
          max={400}
          step={20}
          onChange={setChunkOverlap}
        />
      </div>

      <div className="mt-5 space-y-3">
        <Button
          size="lg"
          className="w-full"
          onClick={onUpload}
          disabled={isUploading || isResetting || selectedFiles.length === 0}
        >
          {isUploading
            ? "Uploading and indexing..."
            : `Upload ${selectedFiles.length} document${selectedFiles.length === 1 ? "" : "s"}`}
        </Button>
      </div>
    </Surface>
  );
}

function RangeControl({
  label,
  helpText,
  value,
  min,
  max,
  step,
  onChange
}: {
  label: string;
  helpText: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (value: number) => void;
}) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-sm text-slate-300">
        <div className="group relative flex items-center gap-2">
          <span>{label}</span>
          <CircleHelp className="h-3.5 w-3.5 text-slate-500" />
          <div className="pointer-events-none absolute left-0 top-6 z-10 hidden w-64 rounded-2xl border border-white/[0.08] bg-[#111114] p-3 text-xs leading-6 text-slate-300 shadow-[0_18px_50px_rgba(0,0,0,0.35)] group-hover:block">
            {helpText}
          </div>
        </div>
        <span className="text-slate-500">{value}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="w-full accent-sky-300"
      />
    </div>
  );
}
