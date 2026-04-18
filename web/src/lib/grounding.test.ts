import { getGroundingMeta, getRelevanceTone } from "./grounding";

describe("getGroundingMeta", () => {
  it("returns fallback tone when context is insufficient", () => {
    expect(getGroundingMeta(0.1, "Sorry, I couldn't find that in the provided documents.")).toEqual({
      label: "Insufficient context",
      tone: "warning"
    });
  });

  it("returns strong grounding for high confidence", () => {
    expect(getGroundingMeta(0.86, "A grounded answer")).toEqual({
      label: "Strong grounding",
      tone: "success"
    });
  });
});

describe("getRelevanceTone", () => {
  it("maps low scores to weak matches", () => {
    expect(getRelevanceTone(0.12)).toEqual({
      label: "Weak match",
      tone: "warning"
    });
  });
});
