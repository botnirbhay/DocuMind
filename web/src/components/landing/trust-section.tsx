"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Shield, Sparkles, Workflow } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import { Surface } from "@/components/ui/surface";
import { cn } from "@/lib/utils";

const items = [
  {
    icon: Shield,
    title: "Citations stay visible",
    body: "Open the supporting evidence directly from the answer instead of guessing where it came from."
  },
  {
    icon: Workflow,
    title: "Designed for long documents",
    body: "Upload multiple files, review the summary, and move into detailed questions without losing context."
  },
  {
    icon: Sparkles,
    title: "Clean and readable",
    body: "The interface stays dark, quiet, and easy to scan so the document content remains the focus."
  }
];

export function TrustSection() {
  return (
    <section className="px-6 py-24 md:px-10 lg:px-14">
      <div className="mx-auto max-w-7xl">
        <Surface className="overflow-hidden rounded-[34px] p-8 md:p-10">
          <div className="grid gap-10 lg:grid-cols-[0.9fr_1.1fr]">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-accent">Why people use it</p>
              <h2 className="mt-4 font-[var(--font-display)] text-4xl font-semibold tracking-tight text-white">
                Built to keep answers useful and easy to verify.
              </h2>
              <p className="mt-5 max-w-xl text-lg leading-8 text-slate-300">
                DocuMind keeps your documents, answers, and supporting evidence together so you can move from upload to
                verified answer without extra steps.
              </p>
              <Link
                href="/workspace"
                className={cn(buttonVariants({ size: "lg" }), "mt-8 inline-flex gap-2")}
              >
                Open workspace
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              {items.map((item, index) => (
                <motion.div
                  key={item.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.06, duration: 0.45 }}
                  className="rounded-[24px] border border-white/10 bg-white/[0.05] p-5"
                >
                  <item.icon className="h-5 w-5 text-accent" />
                  <h3 className="mt-4 font-[var(--font-display)] text-lg font-semibold text-white">{item.title}</h3>
                  <p className="mt-3 text-sm leading-7 text-slate-300">{item.body}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </Surface>
      </div>
    </section>
  );
}
