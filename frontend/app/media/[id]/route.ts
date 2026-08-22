import { NextRequest, NextResponse } from "next/server";
import { backendUrl } from "@/lib/admin-api";

export async function GET(_request: NextRequest, context: { params: Promise<{ id: string }> }) {
  const id = (await context.params).id;
  if (!/^[0-9a-f-]{36}$/i.test(id)) return NextResponse.json({ error: "Media was not found." }, { status: 404 });
  try {
    const response = await fetch(`${backendUrl}/media/${encodeURIComponent(id)}`, { cache: "no-store" });
    if (!response.ok) return NextResponse.json({ error: "Media was not found." }, { status: response.status });
    return new NextResponse(await response.arrayBuffer(), { status: 200, headers: {
      "content-type": response.headers.get("content-type") ?? "application/octet-stream",
      "cache-control": response.headers.get("cache-control") ?? "public, max-age=3600",
      "x-content-type-options": "nosniff",
    }});
  } catch { return NextResponse.json({ error: "Media is unavailable." }, { status: 503 }); }
}
