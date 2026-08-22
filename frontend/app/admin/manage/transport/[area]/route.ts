import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";
import { fetchAdminBackend, safeError, serviceUnavailableError } from "@/lib/admin-api";

const destinations = new Map([
  ["dashboard", "/admin/api/dashboard"], ["content", "/admin/api/content"], ["media", "/admin/api/media"],
  ["content-preview", "/admin/api/content/preview"], ["content-capabilities", "/admin/api/content/capabilities"],
  ["content-seo", "/admin/api/content/seo"],
  ["settings", "/admin/api/settings"], ["extensions", "/admin/api/extensions"], ["applications", "/admin/api/applications"], ["users", "/admin/api/users"], ["roles", "/admin/api/roles"],
  ["diagnostics", "/admin/api/diagnostics"], ["plugin-example", "/api/plugins/example"],
  ["plugin-seo", "/api/plugins/seo/settings"], ["plugin-seo-content", "/api/plugins/seo/content"],
  ["plugin-contact", "/api/plugins/contact/settings"],
  ["plugin-sitemap", "/api/plugins/sitemap/settings"], ["plugin-analytics", "/api/plugins/analytics/settings"],
]);
async function forward(request: NextRequest, area: string) {
  const destination = destinations.get(area);
  if (!destination) return NextResponse.json({ error: "Management resource is unavailable." }, { status: 404 });
  const token = (await cookies()).get("favorite_admin_session")?.value;
  if (!token) return NextResponse.json({ error: "Authentication is required." }, { status: 401 });
  const body = request.method === "GET" ? undefined : await request.text();
  const response = await fetchAdminBackend(`${destination}${request.nextUrl.search}`, { method: request.method,
    headers: { authorization: `Bearer ${token}`, ...(body ? { "content-type": "application/json" } : {}) }, body, cache: "no-store" });
  if (!response) return NextResponse.json({ error: serviceUnavailableError }, { status: 503 });
  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) return NextResponse.json({ error: safeError(payload) }, { status: response.status });
  return NextResponse.json(payload);
}
export async function GET(request: NextRequest, context: { params: Promise<{ area: string }> }) { return forward(request, (await context.params).area); }
export async function POST(request: NextRequest, context: { params: Promise<{ area: string }> }) { return forward(request, (await context.params).area); }
export async function PATCH(request: NextRequest, context: { params: Promise<{ area: string }> }) { return forward(request, (await context.params).area); }
export async function DELETE(request: NextRequest, context: { params: Promise<{ area: string }> }) { return forward(request, (await context.params).area); }
