"use client";

import { motion } from "framer-motion";
import { Binary, FileUp, Layers3, MessagesSquare, SearchCheck } from "lucide-react";

import { SectionHeading } from "@/components/ui/section-heading";
import { Surface } from "@/components/ui/surface";

const features = [
  {
    icon: FileUp,
    title: "Polished ingestion",
    body: "Upload PDF, DOCX, and TXT files with clean metadata and chunking strategies designed for retrieval."
  },
  {
    icon: Binary,
    title: "Local vector indexing",
    body: "Index document chunks against the existing FastAPI backend without introducing cloud-only assumptions."
  },
  {
    icon: SearchCheck,
    title: "Transparent retrieval",
    body: "Inspect the retrieval layer directly so source quality is visible before the answer is generated."
  },
  {
    icon: MessagesSquare,
    title: "Grounded chat",
    body: "Answers stay tied to retrieved evidence, with confidence and fallback behavior surfaced clearly."
  },
  {
    icon: Layers3,
    title: "SaaS-grade presentation",
    body: "A dark-first product experience with motion, depth, and responsive layout rather than an internal dashboard."
  }
];

export function FeatureHighlights() {
  return (
    <section className="px-6 py-24 md:px-10 lg:px-14">
      <div className="mx-auto max-w-7xl">
        <SectionHeading
          eyebrow="What stands out"
          title="A product experience built around retrieval quality."
          body="DocuMind is not just a chat box on top of files. The interface is designed to make ingestion, indexing, retrieval, and evidence-backed answers feel trustworthy and polished."
        />
        <div className="mt-12 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 26 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-10%" }}
              transition={{ delay: index * 0.06, duration: 0.5 }}
            >
              <Surface className="h-full rounded-[24px] p-5">
                <feature.icon className="h-5 w-5 text-accent" />
                <h3 className="mt-5 font-[var(--font-display)] text-lg font-semibold text-white">{feature.title}</h3>
                <p className="mt-3 text-sm leading-7 text-slate-300">{feature.body}</p>
              </Surface>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
