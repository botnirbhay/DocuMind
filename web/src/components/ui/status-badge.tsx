import { motion } from "framer-motion";

import { cn } from "@/lib/utils";

export function StatusBadge({
  label,
  tone = "default"
}: {
  label: string;
  tone?: "default" | "success" | "warning" | "danger";
}) {
  const toneClass =
    tone === "success"
      ? "border-emerald-400/25 bg-emerald-400/10 text-emerald-200"
      : tone === "warning"
        ? "border-amber-400/25 bg-amber-400/10 text-amber-100"
        : tone === "danger"
          ? "border-rose-400/25 bg-rose-400/10 text-rose-100"
          : "border-white/[0.12] bg-white/[0.06] text-slate-200";

  return (
    <motion.span
      layout
      className={cn("inline-flex rounded-full border px-3 py-1 text-xs font-medium tracking-wide", toneClass)}
    >
      {label}
    </motion.span>
  );
}
