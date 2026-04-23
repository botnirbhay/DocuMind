"use client";

import { motion } from "framer-motion";
import { ArrowRight, Bot, DatabaseZap, FileText, ShieldCheck } from "lucide-react";
import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { Surface } from "@/components/ui/surface";
import { cn } from "@/lib/utils";

const highlights = [
  { icon: FileText, label: "Upload PDFs, DOCX, and text files" },
  { icon: DatabaseZap, label: "Prepare files for search and chat" },
  { icon: Bot, label: "Ask grounded questions with citations" },
  { icon: ShieldCheck, label: "Get a clear fallback when nothing matches" }
];

export function HeroSection() {
  return (
    <section className="relative isolate px-6 pb-14 pt-6 md:px-10 lg:px-14">
      <div className="mesh-orb left-[-8rem] top-4 h-64 w-64 bg-sky-400/18" />
      <div className="mesh-orb right-[-10rem] top-8 h-72 w-72 bg-slate-500/18" />

      <div className="mx-auto max-w-7xl">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="mb-6 flex items-center justify-between"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-white/[0.15] bg-white/[0.08] font-[var(--font-display)] text-lg font-semibold text-white">
              D
            </div>
            <div>
              <div className="font-[var(--font-display)] text-lg font-semibold text-white">DocuMind</div>
              <div className="text-sm text-slate-400">Chat with your documents</div>
            </div>
          </div>
          <Link
            href="/workspace"
            className={cn(buttonVariants({ variant: "secondary", size: "sm" }), "hidden md:inline-flex")}
          >
            Open workspace
          </Link>
        </motion.div>

        <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr] lg:gap-8">
          <motion.div
            initial={{ opacity: 0, y: 28 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.08, duration: 0.65 }}
            className="relative"
          >
            <div className="mb-5 inline-flex rounded-full border border-accent/[0.20] bg-accent/[0.10] px-4 py-2 text-xs uppercase tracking-[0.24em] text-accent">
              Answers grounded in your files
            </div>
            <h1 className="max-w-3xl font-[var(--font-display)] text-4xl font-semibold leading-[1.02] tracking-tight text-white md:text-5xl lg:text-6xl">
              Upload documents, ask questions, and inspect the source behind every answer.
            </h1>
            <p className="mt-4 max-w-2xl text-balance text-base leading-7 text-slate-300 md:text-lg">
              Use DocuMind to search, summarize, and chat across your files with citations, confidence, and clear
              supporting evidence.
            </p>
            <div className="mt-6 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/workspace"
                className={cn(buttonVariants({ size: "lg" }), "w-full gap-2 sm:inline-flex sm:w-auto")}
              >
                Open workspace
                <ArrowRight className="h-4 w-4" />
              </Link>
              <a
                href="#how-it-works"
                className={cn(
                  buttonVariants({ variant: "secondary", size: "lg" }),
                  "w-full justify-center sm:inline-flex sm:w-auto"
                )}
              >
                See how it works
              </a>
            </div>
            <div className="mt-7 grid gap-3 sm:grid-cols-2">
              {highlights.map((item) => (
                <div
                  key={item.label}
                  className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.05] px-4 py-3"
                >
                  <item.icon className="h-4 w-4 text-accent" />
                  <span className="text-sm text-slate-200">{item.label}</span>
                </div>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 28 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.18, duration: 0.7 }}
            className="relative"
          >
            <Surface className="relative overflow-hidden p-4">
              <div className="absolute inset-0 bg-hero-grid bg-[size:22px_22px] opacity-20" />
              <div className="absolute -left-8 top-12 h-32 w-32 rounded-full bg-accent/[0.10] blur-3xl" />
              <div className="absolute -right-4 bottom-0 h-40 w-40 rounded-full bg-white/[0.05] blur-3xl" />
              <div className="relative space-y-4">
                <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/[0.05] px-4 py-3">
                  <div>
                    <p className="text-sm font-medium text-white">Example workflow</p>
                    <p className="text-sm text-slate-400">Upload a file, ask a question, inspect the source.</p>
                  </div>
                  <div className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-xs text-emerald-200">
                    Ready
                  </div>
                </div>

                <div className="rounded-[24px] border border-white/10 bg-[#101013] p-4">
                  <div className="mb-3 flex items-center gap-2 text-sm text-slate-400">
                    <span className="h-2 w-2 rounded-full bg-emerald-300" />
                    Upload complete
                  </div>
                  <div className="grid gap-3">
                    <div className="rounded-2xl bg-white/[0.03] p-3">
                      <p className="text-sm font-medium text-white">claims_policy_2026.pdf</p>
                      <p className="mt-1 text-sm text-slate-400">142 chunks indexed • PDF • ready for chat</p>
                    </div>
                    <div className="rounded-2xl bg-white/[0.03] p-3">
                      <p className="text-sm text-slate-400">Question</p>
                      <p className="mt-2 text-base text-white">What is the review timeline for appeals?</p>
                    </div>
                    <div className="rounded-2xl border border-accent/[0.15] bg-accent/[0.08] p-4">
                      <div className="mb-2 flex items-center justify-between">
                        <span className="text-sm font-medium text-white">Grounded answer</span>
                        <span className="rounded-full bg-white/10 px-3 py-1 text-xs text-slate-200">
                          Confidence 0.78
                        </span>
                      </div>
                      <p className="text-sm leading-7 text-slate-100">
                        Appeals are reviewed within seven business days, based on the policy timeline in the uploaded
                        document.
                      </p>
                      <div className="mt-4 rounded-2xl border border-white/10 bg-white/[0.03] px-3 py-3 text-sm text-slate-300">
                        Citation • claims_policy_2026.pdf • page 4 • chunk 018
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </Surface>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
