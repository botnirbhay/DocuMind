import { NextRequest } from "next/server";

import { proxyToBackend } from "@/lib/server/proxy";

export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  return proxyToBackend(request, {
    path: "/api/v1/documents/upload",
    method: "POST",
    bodyType: "formData"
  });
}
