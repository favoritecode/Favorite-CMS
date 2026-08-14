import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { backendUrl, fetchAdminBackend, safeError, serviceUnavailableError } from "@/lib/admin-api";

const cookieName = "favorite_admin_session";

function secureCookie(request: Request): boolean {
  const forwardedProtocol = request.headers.get("x-forwarded-proto")?.split(",")[0]?.trim().toLowerCase();
  return new URL(request.url).protocol === "https:" || forwardedProtocol === "https";
}

export async function POST(request: Request) {
  let input: unknown;
  try { input = await request.json(); } catch { return NextResponse.json({ error: "Invalid login request." }, { status: 400 }); }
  const response = await fetchAdminBackend("/admin/api/session", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(input), cache: "no-store" });
  if (!response) return NextResponse.json({ error: serviceUnavailableError }, { status: 503 });
  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok || typeof payload !== "object" || payload === null || !("data" in payload)) return NextResponse.json({ error: safeError(payload) }, { status: response.status });
  const data = (payload as { data?: unknown }).data;
  if (typeof data !== "object" || data === null || !("access_token" in data) || typeof data.access_token !== "string") return NextResponse.json({ error: "Authentication response was invalid." }, { status: 502 });
  const jar = await cookies();
  jar.set(cookieName, data.access_token, { httpOnly: true, sameSite: "strict", secure: secureCookie(request), path: "/admin" });
  return NextResponse.json({ success: true });
}

export async function DELETE(request: Request) {
  const jar = await cookies(); const token = jar.get(cookieName)?.value;
  if (token) await fetch(`${backendUrl}/admin/api/session`, { method: "DELETE", headers: { authorization: `Bearer ${token}` }, cache: "no-store" }).catch(() => null);
  jar.set(cookieName, "", { httpOnly: true, sameSite: "strict", secure: secureCookie(request), path: "/admin", maxAge: 0 });
  return NextResponse.json({ success: true });
}
