"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Activity, RefreshCw, ServerCog } from "lucide-react";
import { AdminRequestError, adminRequest, isAuthenticationError } from "@/lib/admin-client";
import type { Diagnostics, Operations } from "@/lib/admin-types";
import { ErrorPanel, LoadingPanel, secondaryButton, StatusBadge } from "./admin-ui";

export function DiagnosticsSection() {
  const router = useRouter();
  const [diagnostics, setDiagnostics] = useState<Diagnostics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try { setDiagnostics(await adminRequest<Diagnostics>("/admin/manage/transport/diagnostics")); }
    catch (reason) {
      if (isAuthenticationError(reason)) { router.replace("/admin/login"); return; }
      setError(reason instanceof AdminRequestError && reason.status === 403 ? "Your account does not have the diagnostics permission." : reason instanceof Error ? reason.message : "Diagnostics could not be loaded.");
    } finally { setLoading(false); }
  }, [router]);
  useEffect(() => { void load(); }, [load]);

  if (loading && !diagnostics) return <LoadingPanel label="Loading authorized diagnostics" />;
  if (error) return <ErrorPanel message={error} onRetry={() => void load()} />;
  if (!diagnostics) return null;
  const operations = diagnostics.operations;
  return <div className="space-y-6">
    <section className="grid gap-px overflow-hidden border border-slate-200 bg-slate-200 sm:grid-cols-3" aria-label="Overall system status"><HealthSummary label="Application" value={operations.status} icon={Activity} /><HealthSummary label="Liveness" value={diagnostics.liveness.status} detail={diagnostics.liveness.live ? "Application process is live" : "Application process is unavailable"} icon={ServerCog} /><HealthSummary label="Readiness" value={diagnostics.readiness.status} detail={diagnostics.readiness.ready ? "Critical dependencies are ready" : "A critical dependency is unavailable"} icon={Activity} /></section>

    <section className="border border-slate-200 bg-white shadow-sm" aria-labelledby="components-title"><div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-5 py-4"><div><h2 id="components-title" className="font-semibold">Components</h2><p className="mt-0.5 text-sm text-slate-500">Redacted health checks from owning engines.</p></div><button type="button" className={secondaryButton} onClick={() => void load()} disabled={loading}><RefreshCw className={`size-4 ${loading ? "animate-spin" : ""}`} />Refresh</button></div><div className="overflow-x-auto"><table className="w-full min-w-[42rem] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-4 py-3 font-semibold">Component</th><th className="px-4 py-3 font-semibold">Status</th><th className="px-4 py-3 font-semibold">Critical</th><th className="px-4 py-3 font-semibold">Message</th></tr></thead><tbody className="divide-y divide-slate-100">{operations.components.map(component => <tr key={component.name}><td className="px-4 py-3 font-semibold capitalize">{component.name}</td><td className="px-4 py-3"><StatusBadge value={component.status} /></td><td className="px-4 py-3 text-slate-600">{component.critical ? "Yes" : "No"}</td><td className="px-4 py-3 text-slate-600">{component.message}</td></tr>)}</tbody></table></div></section>

    <div className="grid gap-6 xl:grid-cols-2"><DiagnosticGroup title="Configuration" items={configurationItems(operations)} /><DiagnosticGroup title="Operator-controlled lifecycle" items={lifecycleItems(operations)} /><DiagnosticGroup title="Services" items={serviceItems(operations)} /><DiagnosticGroup title="Content and presentation" items={[{ label: "Content engine", value: operations.content.status }, { label: "SEO projection", value: operations.content.seo_projection ? "available" : "unavailable" }, { label: "Media engine", value: operations.media.status }, { label: "Supported media", value: operations.media.supported }, { label: "Theme", value: operations.theme.status }, { label: "Active theme", value: operations.theme.active ?? "none" }]} /></div>
  </div>;
}

function HealthSummary({ label, value, detail, icon: Icon }: { label: string; value: string; detail?: string; icon: typeof Activity }) {
  return <div className="bg-white p-5"><div className="flex items-start justify-between gap-3"><span className="grid size-10 place-items-center rounded-md bg-slate-100 text-slate-600"><Icon className="size-5" /></span><StatusBadge value={value} /></div><h2 className="mt-4 font-semibold">{label}</h2>{detail && <p className="mt-1 text-xs leading-5 text-slate-500">{detail}</p>}</div>;
}

function DiagnosticGroup({ title, items }: { title: string; items: { label: string; value: string | number | null }[] }) {
  return <section className="border border-slate-200 bg-white shadow-sm"><h2 className="border-b border-slate-200 px-5 py-4 font-semibold">{title}</h2><dl className="divide-y divide-slate-100">{items.map(item => <div key={item.label} className="flex items-center justify-between gap-4 px-5 py-3"><dt className="text-sm text-slate-600">{item.label}</dt><dd className="text-right text-sm font-semibold capitalize">{item.value === null ? "Unknown" : String(item.value).replaceAll("_", " ")}</dd></div>)}</dl></section>;
}

function configurationItems(operations: Operations) {
  return [{ label: "Database", value: operations.configuration.database }, { label: "Database provider", value: operations.configuration.database_provider }, { label: "Storage", value: operations.configuration.storage }, { label: "Storage provider", value: operations.configuration.storage_provider }, { label: "Authentication", value: operations.configuration.authentication }, { label: "Theme configuration", value: operations.configuration.active_theme }];
}
function lifecycleItems(operations: Operations) {
  return [{ label: "Migrations", value: operations.migration.status }, { label: "Applied migrations", value: operations.migration.applied }, { label: "Pending migrations", value: operations.migration.pending }, { label: "Migration mode", value: operations.migration.mode }, { label: "Installation", value: operations.installation.status }, { label: "Updates", value: operations.update.status }, { label: "Recovery", value: operations.recovery.status }];
}
function serviceItems(operations: Operations) {
  return [{ label: "Notifications", value: operations.notification.status }, { label: "Queue", value: operations.queue.status }, { label: "Scheduler", value: operations.scheduler.status }];
}
