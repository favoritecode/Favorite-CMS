"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Activity, ArrowRight, Blocks, FileText, Image as ImageIcon, Palette, Plus, RefreshCw } from "lucide-react";
import { AdminFrame } from "@/components/admin/admin-frame";
import { EmptyState, ErrorPanel, LoadingPanel, secondaryButton, StatusBadge } from "@/components/admin/admin-ui";
import { adminRequest, isAuthenticationError } from "@/lib/admin-client";
import type { Dashboard } from "@/lib/admin-types";

export function AdminShell() {
  const router = useRouter();
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try { setDashboard(await adminRequest<Dashboard>("/admin/manage/transport/dashboard")); }
    catch (reason) {
      if (isAuthenticationError(reason)) { router.replace("/admin/login"); return; }
      setError(reason instanceof Error ? reason.message : "The dashboard could not be loaded.");
    } finally { setLoading(false); }
  }, [router]);

  useEffect(() => { void load(); }, [load]);

  return <AdminFrame section="dashboard" title="Dashboard" description="Operational overview of your authorized Favorite CMS workspace." actions={
    <button type="button" className={secondaryButton} onClick={() => void load()} disabled={loading}><RefreshCw className={`size-4 ${loading ? "animate-spin" : ""}`} />Refresh</button>
  }>
    {loading && !dashboard ? <LoadingPanel label="Loading dashboard" /> : error ? <ErrorPanel message={error} onRetry={() => void load()} /> : dashboard && <DashboardContent dashboard={dashboard} />}
  </AdminFrame>;
}

function DashboardContent({ dashboard }: { dashboard: Dashboard }) {
  const areas = new Set(dashboard.areas);
  if (areas.size === 0) return <EmptyState title="No Admin areas available" detail="This authenticated account has no current Favorite CMS Admin module permissions." />;
  const metrics = [
    dashboard.content && { label: "Total content", value: dashboard.content.count, detail: `${dashboard.content.published ?? 0} published`, icon: FileText, href: "/admin/pages" },
    dashboard.content && { label: "Drafts", value: dashboard.content.draft ?? 0, detail: "Awaiting publication", icon: FileText, href: "/admin/posts" },
    dashboard.media && { label: "Media items", value: dashboard.media.count, detail: "Text documents", icon: ImageIcon, href: "/admin/media" },
    dashboard.extensions && { label: "Active plugins", value: dashboard.extensions.active_plugins, detail: `${dashboard.extensions.installed} extensions installed`, icon: Blocks, href: "/admin/plugins" },
  ].filter(Boolean) as { label: string; value: number | null; detail: string; icon: typeof FileText; href: string }[];

  return <div className="space-y-8">
    {metrics.length > 0 && <section aria-labelledby="overview-title">
      <div className="mb-3 flex items-center justify-between"><h2 id="overview-title" className="text-sm font-semibold uppercase text-slate-600">Overview</h2><span className="text-xs text-slate-500">Live platform data</span></div>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map(metric => { const Icon = metric.icon; return <Link key={metric.label} href={metric.href} className="group rounded-md border border-slate-200 bg-white p-4 shadow-sm transition-colors hover:border-sky-300 focus:outline-none focus:ring-2 focus:ring-sky-600">
          <div className="flex items-start justify-between gap-3"><div><p className="text-sm text-slate-600">{metric.label}</p><strong className="mt-2 block text-3xl font-semibold">{metric.value ?? "—"}</strong></div><span className="grid size-9 place-items-center rounded-md bg-slate-100 text-slate-600 group-hover:bg-sky-50 group-hover:text-sky-700"><Icon className="size-[18px]" /></span></div>
          <p className="mt-3 text-xs text-slate-500">{metric.detail}</p>
        </Link>; })}
      </div>
    </section>}

    <div className="grid gap-6 xl:grid-cols-[minmax(0,1.55fr)_minmax(19rem,0.75fr)]">
      {dashboard.health && <section aria-labelledby="health-title" className="border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-5 py-4"><div><h2 id="health-title" className="font-semibold">System health</h2><p className="mt-0.5 text-sm text-slate-500">Authorized operational status</p></div><StatusBadge value={dashboard.health.operations.status} /></div>
        <div className="grid gap-px bg-slate-200 sm:grid-cols-2 lg:grid-cols-3">
          {dashboard.health.operations.components.slice(0, 9).map(component => <div key={component.name} className="bg-white px-4 py-3"><div className="flex items-center justify-between gap-2"><span className="text-sm font-medium capitalize">{component.name}</span><StatusBadge value={component.status} /></div><p className="mt-2 text-xs leading-5 text-slate-500">{component.message}</p></div>)}
        </div>
        <div className="border-t border-slate-200 px-5 py-3"><Link href="/admin/diagnostics" className="inline-flex items-center gap-2 text-sm font-semibold text-sky-700 hover:text-sky-900 focus:outline-none focus:ring-2 focus:ring-sky-600">View diagnostics <ArrowRight className="size-4" /></Link></div>
      </section>}

      <div className="space-y-6">
        {dashboard.extensions && <section aria-labelledby="appearance-title" className="border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-start gap-3"><span className="grid size-10 place-items-center rounded-md bg-sky-50 text-sky-700"><Palette className="size-5" /></span><div className="min-w-0"><h2 id="appearance-title" className="font-semibold">Active theme</h2><p className="mt-1 break-words text-sm text-slate-600">{dashboard.extensions.active_theme ?? "No active theme"}</p></div></div>
          <Link href="/admin/themes" className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-sky-700 hover:text-sky-900">Manage themes <ArrowRight className="size-4" /></Link>
        </section>}

        <section aria-labelledby="actions-title" className="border border-slate-200 bg-white p-5 shadow-sm">
          <h2 id="actions-title" className="font-semibold">Quick actions</h2>
          <div className="mt-4 grid gap-2">
            {areas.has("content") && <QuickAction href="/admin/posts" icon={Plus} label="Create post" />}
            {areas.has("media") && <QuickAction href="/admin/media" icon={ImageIcon} label="Add media" />}
            {areas.has("extensions") && <QuickAction href="/admin/plugins" icon={Blocks} label="Manage plugins" />}
            {areas.has("diagnostics") && <QuickAction href="/admin/diagnostics" icon={Activity} label="Review diagnostics" />}
          </div>
        </section>
      </div>
    </div>
  </div>;
}

function QuickAction({ href, icon: Icon, label }: { href: string; icon: typeof Plus; label: string }) {
  return <Link href={href} className="flex min-h-11 items-center justify-between rounded-md border border-slate-200 px-3 text-sm font-medium text-slate-700 hover:border-sky-300 hover:bg-sky-50 focus:outline-none focus:ring-2 focus:ring-sky-600"><span className="flex items-center gap-2"><Icon className="size-4 text-slate-500" />{label}</span><ArrowRight className="size-4" /></Link>;
}
