"use client";

import { motion } from "framer-motion";
import { Binary, FileUp, Layers3, MessagesSquare, SearchCheck } from "lucide-react";

import { SectionHeading } from "@/components/ui/section-heading";
import { Surface } from "@/components/ui/surface";

const features = [
  {
    icon: FileUp,
    title: "Document upload",
    body: "Upload PDF, DOCX, and TXT files and prepare them for search and question answering."
  },
  {
    icon: Binary,
    title: "Fast indexing",
    body: "Process your files into searchable chunks so answers stay tied to the uploaded material."
  },
  {
    icon: SearchCheck,
    title: "Source-backed search",
    body: "Review the most relevant passages before or after you ask a question."
  },
  {
    icon: MessagesSquare,
    title: "Grounded chat",
    body: "Ask questions and get concise answers with citations and clear confidence signals."
  },
  {
    icon: Layers3,
    title: "Clear workspace",
    body: "Keep documents, summaries, and evidence in one place without clutter."
  }
];

export function FeatureHighlights() {
  return (
    <section className="px-6 py-24 md:px-10 lg:px-14">
      <div className="mx-auto max-w-7xl">
        <SectionHeading
          eyebrow="What you can do"
          title="Everything you need to read, search, and ask."
          body="DocuMind helps you upload files, review relevant passages, and ask grounded questions without losing track of the source."
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
