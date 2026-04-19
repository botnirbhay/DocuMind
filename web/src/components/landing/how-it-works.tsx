"use client";

import { motion } from "framer-motion";

import { SectionHeading } from "@/components/ui/section-heading";

const steps = [
  {
    label: "01",
    title: "Upload your files",
    body: "Add one or more documents and let DocuMind prepare them for search and question answering."
  },
  {
    label: "02",
    title: "Prepare the workspace",
    body: "DocuMind organizes the document text so the most relevant passages can be found quickly."
  },
  {
    label: "03",
    title: "Ask and verify",
    body: "Search directly or ask a question in chat, then open the citations to verify the answer."
  }
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="px-6 py-24 md:px-10 lg:px-14">
      <div className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
        <SectionHeading
          eyebrow="How it works"
          title="A simple three-step flow from file upload to source-backed answer."
          body="The workspace keeps the process straightforward: upload files, let them be prepared, then ask questions and inspect the supporting evidence."
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
