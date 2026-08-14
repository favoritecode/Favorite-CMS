import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { fetchAdminBackend, safeError, serviceUnavailableError } from "@/lib/admin-api";

export async function GET() {
  const token = (await cookies()).get("favorite_admin_session")?.value;
  if (!token) return NextResponse.json({ error: "Authentication is required." }, { status: 401 });
  const response = await fetchAdminBackend("/admin/api/modules", { headers: { authorization: `Bearer ${token}` }, cache: "no-store" });
  if (!response) return NextResponse.json({ error: serviceUnavailableError }, { status: 503 });
  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) return NextResponse.json({ error: safeError(payload) }, { status: response.status });
  return NextResponse.json(payload);
}
