import { NextRequest } from "next/server";

import { proxyToBackend } from "@/lib/server/proxy";

export const dynamic = "force-dynamic";

export async function DELETE(
  request: NextRequest,
  { params }: { params: { documentId: string } }
) {
  return proxyToBackend(request, {
    path: `/api/v1/documents/${params.documentId}`,
    method: "DELETE"
  });
}
