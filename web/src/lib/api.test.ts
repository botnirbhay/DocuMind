import { abortPendingDocuMindRequests, extractApiError, isAbortError, resolveApiBaseUrl, sendChatQueryRequest } from "./api";

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

describe("request aborts", () => {
  it("aborts pending DocuMind requests", async () => {
    const fetchMock = vi.fn((_input: RequestInfo | URL, init?: RequestInit) => {
      return new Promise<Response>((_resolve, reject) => {
        init?.signal?.addEventListener("abort", () => {
          reject(new DOMException("The operation was aborted.", "AbortError"));
        });
      });
    });

    vi.stubGlobal("fetch", fetchMock);

    const requestPromise = sendChatQueryRequest("session-1", "What file types does the platform accept?", 4);
    abortPendingDocuMindRequests();

    await expect(requestPromise).rejects.toSatisfy((error: unknown) => isAbortError(error));

    vi.unstubAllGlobals();
  });
});
