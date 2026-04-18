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
    title: "Grounded by default",
    body: "The backend already supports citations, confidence, and fallback behavior. The frontend makes those signals visible."
  },
  {
    icon: Workflow,
    title: "Built for demos and portfolios",
    body: "Landing page polish and a live workspace sit side by side, making DocuMind feel complete in interviews."
  },
  {
    icon: Sparkles,
    title: "Modern without being noisy",
    body: "Motion, depth, and lighting are present, but they support clarity instead of fighting it."
  }
];

export function TrustSection() {
  return (
    <section className="px-6 py-24 md:px-10 lg:px-14">
      <div className="mx-auto max-w-7xl">
        <Surface className="overflow-hidden rounded-[34px] p-8 md:p-10">
          <div className="grid gap-10 lg:grid-cols-[0.9fr_1.1fr]">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-accent">Why it feels complete</p>
              <h2 className="mt-4 font-[var(--font-display)] text-4xl font-semibold tracking-tight text-white">
                The design sells the product, but the workflow still does the work.
              </h2>
              <p className="mt-5 max-w-xl text-lg leading-8 text-slate-300">
                DocuMind ships as a coherent product narrative: a premium landing experience, a working AI workspace,
                and a backend that already knows how to stay grounded.
              </p>
              <Link
                href="/workspace"
                className={cn(buttonVariants({ size: "lg" }), "mt-8 inline-flex gap-2")}
              >
                Launch the workspace
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
