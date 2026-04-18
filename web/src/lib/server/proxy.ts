import { NextRequest, NextResponse } from "next/server";

import { resolveBackendBaseUrl } from "./backend";

type ProxyOptions = {
  path: string;
  method?: "GET" | "POST";
  bodyType?: "json" | "formData";
};

export async function proxyToBackend(request: NextRequest, options: ProxyOptions) {
  const method = options.method ?? request.method;
  const headers = new Headers();
  const accept = request.headers.get("accept");
  const contentType = request.headers.get("content-type");

  if (accept) {
    headers.set("accept", accept);
  }

  let body: BodyInit | undefined;

  if (options.bodyType === "json") {
    if (contentType) {
      headers.set("content-type", contentType);
    }
    body = await request.text();
  }

  if (options.bodyType === "formData") {
    body = await request.formData();
  }

  try {
    const response = await fetch(`${resolveBackendBaseUrl()}${options.path}`, {
      method,
      headers,
      body,
      cache: "no-store"
    });

    const payload = await response.text();
    const responseType = response.headers.get("content-type") || "application/json";

    return new NextResponse(payload, {
      status: response.status,
      headers: {
        "content-type": responseType
      }
    });
  } catch {
    return NextResponse.json(
      {
        detail: `Unable to reach DocuMind backend at ${resolveBackendBaseUrl()}.`
      },
      { status: 502 }
    );
  }
}
