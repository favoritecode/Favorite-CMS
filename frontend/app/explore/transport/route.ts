import { NextRequest, NextResponse } from "next/server";
import { backendUrl, safeError } from "@/lib/admin-api";
export async function GET(request: NextRequest) {
  const kind = request.nextUrl.searchParams.get("kind");
  if (kind !== "search" && kind !== "localization") return NextResponse.json({error:"Resource unavailable."},{status:404});
  const query = new URLSearchParams(request.nextUrl.searchParams); query.delete("kind");
  const response = await fetch(`${backendUrl}/api/${kind}?${query}`, {cache:"no-store"}); const payload:unknown=await response.json().catch(()=>null);
  if(!response.ok)return NextResponse.json({error:safeError(payload)},{status:response.status}); return NextResponse.json(payload);
}
