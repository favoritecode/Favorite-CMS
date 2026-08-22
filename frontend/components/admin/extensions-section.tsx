"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Blocks, Check, ChevronRight, CircleAlert, Palette, Power, RefreshCw, Settings2, ShieldCheck, Trash2, Upload } from "lucide-react";
import { adminRequest, isAuthenticationError } from "@/lib/admin-client";
import type { ExtensionItem } from "@/lib/admin-types";
import { EmptyState, ErrorPanel, LoadingPanel, primaryButton, secondaryButton, StatusBadge, useToast } from "./admin-ui";
import { PluginSettings } from "./plugin-settings";

type PendingAction = { extension: ExtensionItem; action: "activate" | "deactivate" | "uninstall" } | null;

export function ExtensionsSection({ kind }: { kind: "theme" | "plugin" }) {
  const router = useRouter();
  const { notify } = useToast();
  const [extensions, setExtensions] = useState<ExtensionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [pending, setPending] = useState<PendingAction>(null);
  const [grants, setGrants] = useState<Set<string>>(new Set());
  const [submitting, setSubmitting] = useState(false);
  const [configuration, setConfiguration] = useState<ExtensionItem | null>(null);
  const [uploading, setUploading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try { setExtensions(await adminRequest<ExtensionItem[]>("/admin/manage/transport/extensions")); }
    catch (reason) {
      if (isAuthenticationError(reason)) { router.replace("/admin/login"); return; }
      setError(reason instanceof Error ? reason.message : "Extensions could not be loaded.");
    } finally { setLoading(false); }
  }, [router]);
  useEffect(() => { void load(); }, [load]);

  const items = useMemo(() => extensions.filter(extension => extension.type === kind), [extensions, kind]);
  function requestAction(extension: ExtensionItem, action: "activate" | "deactivate" | "uninstall") {
    setPending({ extension, action });
    setGrants(new Set(extension.granted_permissions));
  }
  function toggleGrant(permission: string) {
    setGrants(current => { const next = new Set(current); if (next.has(permission)) next.delete(permission); else next.add(permission); return next; });
  }

  async function runAction() {
    if (!pending) return;
    setSubmitting(true);
    try {
      await adminRequest<ExtensionItem[]>("/admin/manage/transport/extensions", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ type: pending.extension.type, id: pending.extension.id, action: pending.action, ...(pending.extension.type === "plugin" && pending.action === "activate" ? { granted_permissions: [...grants] } : {}) }) });
      notify(`${pending.extension.name} ${pending.action === "activate" ? "activated" : pending.action === "deactivate" ? "deactivated" : "uninstalled"}.`);
      setPending(null); await load();
    } catch (reason) { notify(reason instanceof Error ? reason.message : "Extension lifecycle operation failed.", "error"); }
    finally { setSubmitting(false); }
  }

  async function upload(file: File, action: "install" | "update", extension?: ExtensionItem) {
    if (file.size > 5_000_000) { notify("The ZIP exceeds the 5 MB package limit.", "error"); return; }
    setUploading(true);
    try {
      const bytes = new Uint8Array(await file.arrayBuffer()); let binary = "";
      for (let offset = 0; offset < bytes.length; offset += 32_768) binary += String.fromCharCode(...bytes.subarray(offset, offset + 32_768));
      await adminRequest<ExtensionItem[]>("/admin/manage/transport/extensions", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ type: kind, action, ...(extension ? { id: extension.id } : {}), archive: btoa(binary) }) });
      notify(`${kind === "theme" ? "Theme" : "Plugin"} ${action === "install" ? "installed inactive" : "updated"}.`); await load();
    } catch (reason) { notify(reason instanceof Error ? reason.message : "Package operation failed.", "error"); }
    finally { setUploading(false); }
  }

  const title = kind === "theme" ? "themes" : "plugins";
  return <div className="space-y-5">
    <div className="flex flex-wrap items-center justify-between gap-3 border-y border-slate-200 bg-white px-4 py-3"><div><p className="text-sm text-slate-600">{items.length} installed {title}</p>{kind === "plugin" && <p className="text-xs text-amber-700">Uploaded Plugins are restricted to declarative, non-executable packages. ZIP validation is not a code sandbox.</p>}</div><div className="flex gap-2"><label className={`${primaryButton} cursor-pointer ${uploading ? "pointer-events-none opacity-50" : ""}`}><Upload className="size-4" />Add {kind}<input className="sr-only" type="file" accept=".zip,application/zip" onChange={event => { const file = event.target.files?.[0]; if (file) void upload(file, "install"); event.target.value = ""; }} /></label><button type="button" className={secondaryButton} onClick={() => void load()} disabled={loading}><RefreshCw className={`size-4 ${loading ? "animate-spin" : ""}`} />Refresh</button></div></div>
    {loading && extensions.length === 0 ? <LoadingPanel label={`Loading ${title}`} /> : error ? <ErrorPanel message={error} onRetry={() => void load()} /> : items.length === 0 ? <EmptyState title={`No ${title} installed`} detail={`Favorite CMS did not discover any valid ${kind} manifests.`} /> : <div className="grid gap-4 xl:grid-cols-2">{items.map(extension => <ExtensionCard key={extension.id} extension={extension} onAction={requestAction} onConfigure={setConfiguration} onUpdate={file => void upload(file, "update", extension)} />)}</div>}
    {pending && <LifecycleDialog pending={pending} grants={grants} busy={submitting} onToggle={toggleGrant} onCancel={() => setPending(null)} onConfirm={() => void runAction()} />}
    {configuration && <PluginSettings plugin={configuration} onClose={() => setConfiguration(null)} />}
  </div>;
}

function ExtensionCard({ extension, onAction, onConfigure, onUpdate }: { extension: ExtensionItem; onAction: (extension: ExtensionItem, action: "activate" | "deactivate" | "uninstall") => void; onConfigure: (extension: ExtensionItem) => void; onUpdate: (file: File) => void }) {
  const Icon = extension.type === "theme" ? Palette : Blocks;
  const enabled = extension.state === "enabled";
  const configurable = extension.type === "plugin" && ["favorite.plugin.example", "favorite.plugin.seo", "favorite.plugin.contact", "favorite.plugin.sitemap", "favorite.plugin.analytics"].includes(extension.id);
  return <article className="flex flex-col border border-slate-200 bg-white shadow-sm">
    <div className="flex flex-1 flex-col p-5">
      <div className="flex items-start gap-4"><span className={`grid size-11 shrink-0 place-items-center rounded-md ${extension.active || enabled ? "bg-sky-50 text-sky-700" : "bg-slate-100 text-slate-500"}`}><Icon className="size-5" /></span><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><h2 className="font-semibold">{extension.name}</h2>{extension.active && <StatusBadge value="active" />}<StatusBadge value={extension.state} />{!extension.package_managed && <StatusBadge value="bundled" />}{!extension.compatible && <StatusBadge value="incompatible" />}</div><p className="mt-1 text-xs text-slate-500">v{extension.version} by {extension.author}</p></div></div>
      <p className="mt-4 text-sm leading-6 text-slate-600">{extension.description}</p>
      <p className="mt-3 break-all font-mono text-xs text-slate-400">{extension.id}</p>
      {Object.keys(extension.dependencies).length > 0 && <DependencyList title="Required dependencies" values={extension.dependencies} />}
      {Object.keys(extension.optional_dependencies).length > 0 && <DependencyList title="Optional dependencies" values={extension.optional_dependencies} />}
      {extension.type === "plugin" && extension.permissions.length > 0 && <div className="mt-4"><p className="text-xs font-semibold uppercase text-slate-500">Declared capabilities</p><div className="mt-2 flex flex-wrap gap-1.5">{extension.permissions.map(permission => <span key={permission} className={`rounded-full px-2 py-1 font-mono text-[11px] ring-1 ring-inset ${extension.granted_permissions.includes(permission) ? "bg-emerald-50 text-emerald-800 ring-emerald-200" : "bg-slate-100 text-slate-600 ring-slate-200"}`}>{permission}</span>)}</div></div>}
      {extension.failure && <div className="mt-4 flex gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800"><CircleAlert className="mt-0.5 size-4 shrink-0" /><span>{extension.failure}</span></div>}
    </div>
    <div className="flex flex-wrap justify-end gap-2 border-t border-slate-200 bg-slate-50 px-4 py-3">
      {extension.package_managed ? <label className={`${secondaryButton} cursor-pointer`}><Upload className="size-4" />Update<input className="sr-only" type="file" accept=".zip,application/zip" onChange={event => { const file = event.target.files?.[0]; if (file) onUpdate(file); event.target.value = ""; }} /></label> : <span className="self-center text-xs text-slate-500" title="Bundled extensions are updated with the CMS distribution.">Distribution managed</span>}
      {configurable && enabled && <button type="button" className={secondaryButton} onClick={() => onConfigure(extension)}><Settings2 className="size-4" />Configure</button>}
      {extension.type === "theme" ? extension.active ? <button type="button" className={secondaryButton} disabled><Check className="size-4" />Active theme</button> : <button type="button" className={primaryButton} onClick={() => onAction(extension, "activate")} disabled={!extension.compatible}><Palette className="size-4" />Activate</button> : enabled ? <button type="button" className={secondaryButton} onClick={() => onAction(extension, "deactivate")}><Power className="size-4" />Deactivate</button> : <button type="button" className={primaryButton} onClick={() => onAction(extension, "activate")} disabled={!extension.compatible}><Power className="size-4" />Activate</button>}
      {extension.package_managed && !enabled && !extension.active && <button type="button" className={secondaryButton} onClick={() => onAction(extension, "uninstall")}><Trash2 className="size-4" />Uninstall</button>}
    </div>
  </article>;
}

function DependencyList({ title, values }: { title: string; values: Record<string, string> }) {
  return <div className="mt-4"><p className="text-xs font-semibold uppercase text-slate-500">{title}</p><ul className="mt-2 grid gap-1">{Object.entries(values).map(([name, version]) => <li key={name} className="flex items-center gap-2 text-xs text-slate-600"><ChevronRight className="size-3" /><span className="font-mono">{name}</span><span>{version}</span></li>)}</ul></div>;
}

function LifecycleDialog({ pending, grants, busy, onToggle, onCancel, onConfirm }: { pending: NonNullable<PendingAction>; grants: Set<string>; busy: boolean; onToggle: (permission: string) => void; onCancel: () => void; onConfirm: () => void }) {
  const needsApproval = pending.extension.type === "plugin" && pending.action === "activate" && pending.extension.permissions.length > 0;
  const allGranted = pending.extension.permissions.every(permission => grants.has(permission));
  const label = pending.action === "activate" ? "Activate" : pending.action === "deactivate" ? "Deactivate" : "Uninstall";
  return <div className="fixed inset-0 z-[70] grid place-items-center bg-slate-950/45 p-4" role="presentation"><section className="w-full max-w-lg rounded-md bg-white shadow-2xl" role="dialog" aria-modal="true" aria-labelledby="lifecycle-title"><div className="border-b border-slate-200 px-5 py-4"><p className="text-xs font-semibold uppercase text-sky-700">Extension lifecycle</p><h2 id="lifecycle-title" className="mt-1 text-lg font-semibold">{label} {pending.extension.name}?</h2></div><div className="p-5"><p className="text-sm leading-6 text-slate-600">{pending.action === "uninstall" ? "This removes the inactive uploaded package. Bundled extensions are protected." : pending.extension.type === "theme" ? "Activating this theme replaces the current public presentation theme. Favorite CMS will preserve the previous valid theme if activation fails." : pending.action === "activate" ? "The plugin runtime will be enabled using only explicitly approved capabilities." : "The plugin runtime and its registered Admin/API presentation contracts will be disabled."}</p>{needsApproval && <fieldset className="mt-5"><legend className="flex items-center gap-2 text-sm font-semibold"><ShieldCheck className="size-4 text-sky-700" />Capability approval</legend><div className="mt-3 grid gap-2">{pending.extension.permissions.map(permission => <label key={permission} className="flex min-h-11 items-center gap-3 rounded-md border border-slate-200 px-3 text-sm hover:bg-slate-50"><input type="checkbox" checked={grants.has(permission)} onChange={() => onToggle(permission)} className="size-4 rounded border-slate-300 text-sky-700 focus:ring-sky-600" /><span className="font-mono text-xs">{permission}</span></label>)}</div></fieldset>}</div><div className="flex justify-end gap-2 border-t border-slate-200 bg-slate-50 px-5 py-3"><button type="button" className={secondaryButton} onClick={onCancel} disabled={busy} autoFocus>Cancel</button><button type="button" className={primaryButton} onClick={onConfirm} disabled={busy || (needsApproval && !allGranted)}>{label}</button></div></section></div>;
}
