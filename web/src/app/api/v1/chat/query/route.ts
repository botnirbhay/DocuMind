import { NextRequest } from "next/server";

import { proxyToBackend } from "@/lib/server/proxy";

export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  return proxyToBackend(request, {
    path: "/api/v1/chat/query",
    method: "POST",
    bodyType: "json"
  });
}
