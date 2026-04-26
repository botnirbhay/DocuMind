import { buildSuggestedQuestions } from "./suggestions";

describe("buildSuggestedQuestions", () => {
  it("prefers summary-provided questions", () => {
    expect(
      buildSuggestedQuestions(
        [{ document_id: "doc-1", filename: "resume.txt", file_type: "txt", chunks_extracted: 1, status: "ingested" }],
        {
          answer: "summary",
          confidenceScore: 0.8,
          citations: [],
          retrievedChunks: [],
          suggestedQuestions: ["Question A", "Question B", "Question C"]
        }
      )
    ).toEqual(["Question A", "Question B", "Question C"]);
  });

  it("uses resume-aware defaults when summary is unavailable", () => {
    expect(
      buildSuggestedQuestions(
        [{ document_id: "doc-1", filename: "candidate-resume.pdf", file_type: "pdf", chunks_extracted: 4, status: "ingested" }],
        null
      )
    ).toContain("Summarize the candidate's professional experience.");
  });
});
