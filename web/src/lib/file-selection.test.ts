import { mergeSelectedFiles } from "./file-selection";

describe("mergeSelectedFiles", () => {
  it("appends files across repeated selections", () => {
    const first = new File(["alpha"], "alpha.txt", { lastModified: 1, type: "text/plain" });
    const second = new File(["beta"], "beta.txt", { lastModified: 2, type: "text/plain" });

    expect(mergeSelectedFiles([first], [second]).map((file) => file.name)).toEqual(["alpha.txt", "beta.txt"]);
  });

  it("deduplicates the same file selection", () => {
    const first = new File(["alpha"], "alpha.txt", { lastModified: 1, type: "text/plain" });
    const duplicate = new File(["alpha"], "alpha.txt", { lastModified: 1, type: "text/plain" });

    expect(mergeSelectedFiles([first], [duplicate])).toHaveLength(1);
  });
});
