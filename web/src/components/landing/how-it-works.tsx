"use client";

import { motion } from "framer-motion";

import { SectionHeading } from "@/components/ui/section-heading";

const steps = [
  {
    label: "01",
    title: "Bring in source documents",
    body: "Upload one or more files and let the backend extract, normalize, and prepare them for retrieval."
  },
  {
    label: "02",
    title: "Build the vector index",
    body: "Index every chunk locally through the existing FastAPI pipeline and keep multi-document retrieval ready."
  },
  {
    label: "03",
    title: "Search or ask a grounded question",
    body: "Inspect raw chunk matches or jump straight into chat with citations, confidence, and source previews."
  }
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="px-6 py-24 md:px-10 lg:px-14">
      <div className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
        <SectionHeading
          eyebrow="How it works"
          title="A clean three-step flow from upload to grounded answer."
          body="The workspace mirrors the real backend flow, so what looks elegant on screen still maps to the actual retrieval pipeline behind it."
        />
        <div className="space-y-4">
          {steps.map((step, index) => (
            <motion.div
              key={step.label}
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-12%" }}
              transition={{ delay: index * 0.08, duration: 0.55 }}
              className="glass-panel rounded-[28px] p-6"
            >
              <div className="flex items-start gap-4">
                <div className="rounded-2xl border border-accent/[0.20] bg-accent/[0.10] px-4 py-2 font-[var(--font-display)] text-sm text-accent">
                  {step.label}
                </div>
                <div>
                  <h3 className="font-[var(--font-display)] text-xl font-semibold text-white">{step.title}</h3>
                  <p className="mt-2 text-sm leading-7 text-slate-300">{step.body}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
