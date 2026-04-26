import type { UploadedDocumentResponse, WorkspaceSummary } from "./types";

export function buildSuggestedQuestions(
  documents: UploadedDocumentResponse[],
  summary: WorkspaceSummary | null
): string[] {
  if (summary?.suggestedQuestions?.length) {
    return summary.suggestedQuestions.slice(0, 3);
  }

  if (documents.length === 0) {
    return [];
  }

  const filenames = documents.map((document) => document.filename.toLowerCase()).join(" ");
  if (/(resume|cv|profile)/.test(filenames)) {
    return [
      "What are the candidate's core skills?",
      "Summarize the candidate's professional experience.",
      "Which projects or achievements stand out?"
    ];
  }

  return [];
}
