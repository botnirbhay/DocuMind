"use client";

import { AnimatePresence, motion } from "framer-motion";

import { Button } from "@/components/ui/button";

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel,
  cancelLabel = "Cancel",
  isConfirming = false,
  onConfirm,
  onClose
}: {
  open: boolean;
  title: string;
  description: string;
  confirmLabel: string;
  cancelLabel?: string;
  isConfirming?: boolean;
  onConfirm: () => void | Promise<void>;
  onClose: () => void;
}) {
  return (
    <AnimatePresence>
      {open ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4 backdrop-blur-sm"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, y: 18, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 12, scale: 0.98 }}
            transition={{ duration: 0.18 }}
            className="w-full max-w-md rounded-[28px] border border-white/[0.08] bg-[#111114] p-6 shadow-[0_24px_80px_rgba(0,0,0,0.45)]"
            onClick={(event) => event.stopPropagation()}
          >
            <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Confirm action</p>
            <h3 className="mt-3 font-[var(--font-display)] text-2xl font-semibold text-slate-100">{title}</h3>
            <p className="mt-3 text-sm leading-7 text-slate-300">{description}</p>
            <div className="mt-6 flex gap-3">
              <Button variant="secondary" className="flex-1" onClick={onClose} disabled={isConfirming}>
                {cancelLabel}
              </Button>
              <Button className="flex-1" onClick={() => void onConfirm()} disabled={isConfirming}>
                {isConfirming ? "Clearing..." : confirmLabel}
              </Button>
            </div>
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
