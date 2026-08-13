"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { AdminModule, ApiEnvelope } from "@/lib/admin-api";

type Dashboard = {
  areas: string[];
  content?: { count: number | null };
  media?: { count: number | null };
  extensions?: { installed: number; active_plugins: number; active_theme: string | null };
  health?: { liveness: { live: boolean }; readiness: { ready: boolean }; operations: Operations };
};
type Operations = { version:string; status:string; configuration:{database:string;database_provider:string;storage:string;storage_provider:string}; migration:{status:string;applied:number|null;pending:number|null}; installation:{status:string}; notification:{status:string}; queue:{status:string}; scheduler:{status:string} };
type State = { kind: "loading" } | { kind: "error"; message: string } | { kind: "ready"; modules: AdminModule[]; dashboard: Dashboard };

async function read<T>(url: string): Promise<T> {
  const response = await fetch(url, { cache: "no-store" });
  const payload = await response.json() as ApiEnvelope<T> & { error?: string };
  if (!response.ok || payload.data === undefined) throw Object.assign(new Error(typeof payload.error === "string" ? payload.error : "Admin data could not be loaded."), { status: response.status });
  return payload.data;
}

export function AdminShell() {
  const router = useRouter(); const [state, setState] = useState<State>({ kind: "loading" });
  useEffect(() => { let active = true; Promise.all([read<AdminModule[]>("/admin/modules"), read<Dashboard>("/admin/manage/transport/dashboard")])
    .then(([modules, dashboard]) => active && setState({ kind: "ready", modules, dashboard }))
    .catch((error: unknown) => { if (!active) return; if ((error as { status?: number }).status === 401) router.replace("/admin/login"); else setState({ kind: "error", message: error instanceof Error ? error.message : "The Admin API is unavailable." }); });
    return () => { active = false; }; }, [router]);
  async function logout() { await fetch("/admin/session", { method: "DELETE" }); router.replace("/admin/login"); router.refresh(); }
  return <div className="min-h-screen bg-slate-100 text-slate-950">
    <header className="border-b bg-slate-950 text-white"><div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4"><div><p className="text-xs font-semibold uppercase tracking-[.2em] text-sky-300">Favorite CMS</p><h1 className="text-xl font-bold">Administration</h1></div><button onClick={logout} className="rounded-lg border border-slate-600 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-300 hover:bg-slate-800">Sign out</button></div></header>
    <div className="mx-auto grid max-w-7xl gap-6 px-5 py-8 md:grid-cols-[16rem_1fr]">
      <nav aria-label="Administration" className="rounded-xl bg-white p-4 shadow-sm"><a href="/admin" aria-current="page" className="mb-3 block rounded-lg bg-slate-950 px-3 py-2 font-semibold text-white">Dashboard</a><p className="mb-3 text-xs font-bold uppercase tracking-wider text-slate-500">Management</p>{state.kind === "loading" && <p role="status" className="text-sm text-slate-600">Loading navigation…</p>}{state.kind === "ready" && state.modules.length === 0 && <p className="text-sm text-slate-600">No management modules are available for this account.</p>}{state.kind === "ready" && <ul className="grid gap-1 sm:grid-cols-2 md:grid-cols-1">{state.modules.map(module => <li key={module.id}><a href={module.destination} className="block rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-sky-600 hover:bg-slate-100">{module.label}</a></li>)}</ul>}</nav>
      <main className="space-y-6 rounded-xl bg-white p-6 shadow-sm"><div><p className="text-sm font-semibold text-sky-700">Welcome to Favorite CMS</p><h2 className="text-3xl font-bold">Admin dashboard</h2><p className="mt-2 text-slate-600">Manage your site through the areas explicitly authorized for this account.</p></div>
        {state.kind === "loading" && <p role="status" className="rounded-lg bg-slate-100 p-4 text-slate-600">Loading your authorized workspace…</p>}
        {state.kind === "error" && <div role="alert" className="rounded-lg bg-red-50 p-4 text-red-800"><p className="font-semibold">Could not load Admin</p><p className="mt-1 text-sm">{state.message}</p></div>}
        {state.kind === "ready" && <><section aria-labelledby="overview-title"><h3 id="overview-title" className="text-lg font-bold">Site overview</h3><div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {state.dashboard.content && <Summary label="Content" value={state.dashboard.content.count} href="/admin/manage#content" />}
          {state.dashboard.media && <Summary label="Media" value={state.dashboard.media.count} href="/admin/manage#media" />}
          {state.dashboard.extensions && <Summary label="Active plugins" value={state.dashboard.extensions.active_plugins} href="/admin/manage#extensions" />}
          {state.dashboard.health && <Summary label="Readiness" value={state.dashboard.health.readiness.ready ? "Ready" : "Degraded"} href="/admin/manage#diagnostics" />}
        </div></section>{state.dashboard.health&&<section aria-labelledby="system-title" className="rounded-xl border border-slate-200 p-4"><div className="flex flex-wrap items-center justify-between gap-2"><h3 id="system-title" className="font-bold">System status</h3><span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold uppercase">v{state.dashboard.health.operations.version}</span></div><dl className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4"><Fact label="Database" value={`${state.dashboard.health.operations.configuration.database} · ${state.dashboard.health.operations.configuration.database_provider}`}/><Fact label="Migrations" value={state.dashboard.health.operations.migration.pending===null?"Unknown":`${state.dashboard.health.operations.migration.pending} pending`}/><Fact label="Installation" value={state.dashboard.health.operations.installation.status}/><Fact label="Notification" value={state.dashboard.health.operations.notification.status.replaceAll("_"," ")}/></dl><p className="mt-3 text-sm text-slate-600">Migrations and installation are always explicit operator actions.</p><a className="mt-3 inline-block text-sm font-semibold text-sky-700 hover:underline" href="/admin/manage#diagnostics">View operational diagnostics</a></section>}<section aria-labelledby="theme-title" className="rounded-xl border border-slate-200 p-4"><h3 id="theme-title" className="font-bold">Presentation</h3><p className="mt-1 text-sm text-slate-600">Active theme: <strong>{state.dashboard.extensions?.active_theme ?? "No active theme"}</strong></p><a className="mt-3 inline-block text-sm font-semibold text-sky-700 underline-offset-4 hover:underline" href="/admin/manage#extensions">Manage themes and plugins</a></section></>}
      </main>
    </div>
  </div>;
}

function Summary({ label, value, href }: { label: string; value: string | number | null; href: string }) {
  return <a href={href} className="rounded-xl border border-slate-200 p-4 focus:outline-none focus:ring-2 focus:ring-sky-600 hover:border-sky-300"><span className="text-sm text-slate-600">{label}</span><strong className="mt-1 block text-2xl">{value ?? "Unknown"}</strong></a>;
}
function Fact({label,value}:{label:string;value:string}){return <div><dt className="text-xs font-bold uppercase tracking-wide text-slate-500">{label}</dt><dd className="mt-1 font-semibold capitalize">{value}</dd></div>}
