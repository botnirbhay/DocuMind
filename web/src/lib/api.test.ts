import { extractApiError, resolveApiBaseUrl } from "./api";

describe("resolveApiBaseUrl", () => {
  it("defaults to same-origin proxy", () => {
    expect(resolveApiBaseUrl(undefined)).toBe("");
  });

  it("strips trailing slash", () => {
    expect(resolveApiBaseUrl("http://localhost:8000/")).toBe("http://localhost:8000");
  });
});

describe("extractApiError", () => {
  it("uses backend detail when present", async () => {
    const response = new Response(JSON.stringify({ detail: "Vector index is not ready." }), {
      status: 400,
      headers: { "Content-Type": "application/json" }
    });

    await expect(extractApiError(response)).resolves.toBe("Vector index is not ready.");
  });

  it("falls back to status text when payload is not json", async () => {
    const response = new Response("bad gateway", { status: 502 });
    await expect(extractApiError(response)).resolves.toBe("Request failed with status 502.");
  });
});
