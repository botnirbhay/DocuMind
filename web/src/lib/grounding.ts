const FALLBACK_ANSWER = "Sorry, I couldn't find that in the provided documents.";

export function getGroundingMeta(confidenceScore: number, answer: string) {
  if (answer === FALLBACK_ANSWER) {
    return { label: "Insufficient context", tone: "warning" as const };
  }
  if (confidenceScore >= 0.72) {
    return { label: "Strong grounding", tone: "success" as const };
  }
  if (confidenceScore >= 0.4) {
    return { label: "Moderate grounding", tone: "default" as const };
  }
  return { label: "Low confidence", tone: "warning" as const };
}

export function getRelevanceTone(score: number) {
  if (score >= 0.72) {
    return { label: "High relevance", tone: "success" as const };
  }
  if (score >= 0.4) {
    return { label: "Relevant", tone: "default" as const };
  }
  return { label: "Weak match", tone: "warning" as const };
}
