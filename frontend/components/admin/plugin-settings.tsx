"use client";

import { type FormEvent, useEffect, useState } from "react";
import { Save, X } from "lucide-react";
import { adminRequest } from "@/lib/admin-client";
import type { ExtensionItem } from "@/lib/admin-types";
import { ErrorPanel, fieldClass, LoadingPanel, primaryButton, secondaryButton, useToast } from "./admin-ui";

const routes: Record<string, string> = {
  "favorite.plugin.example": "plugin-example",
  "favorite.plugin.seo": "plugin-seo",
  "favorite.plugin.contact": "plugin-contact",
  "favorite.plugin.sitemap": "plugin-sitemap",
  "favorite.plugin.analytics": "plugin-analytics",
};

export function PluginSettings({ plugin, onClose }: { plugin: ExtensionItem; onClose: () => void }) {
  const { notify } = useToast();
  const area = routes[plugin.id];
  const [value, setValue] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    adminRequest<Record<string, unknown>>(`/admin/manage/transport/${area}`)
      .then(result => { if (active) setValue(result); })
      .catch(reason => { if (active) setError(reason instanceof Error ? reason.message : "Plugin settings could not be loaded."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [area]);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!value) return; setSaving(true);
    try {
      const payload = cleanPayload(plugin.id, value);
      setValue(await adminRequest<Record<string, unknown>>(`/admin/manage/transport/${area}`, { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify(payload) }));
      notify(`${plugin.name} settings saved.`);
    } catch (reason) { notify(reason instanceof Error ? reason.message : "Plugin settings could not be saved.", "error"); }
    finally { setSaving(false); }
  }

  return <div className="fixed inset-0 z-50 bg-slate-950/45 p-0 sm:p-4" role="presentation"><section role="dialog" aria-modal="true" aria-labelledby="plugin-settings-title" className="ml-auto flex h-full w-full max-w-2xl flex-col bg-white shadow-2xl sm:rounded-md"><div className="flex min-h-16 items-center justify-between border-b border-slate-200 px-5"><div><p className="text-xs font-semibold uppercase text-sky-700">Plugin configuration</p><h2 id="plugin-settings-title" className="font-semibold">{plugin.name}</h2></div><button type="button" title="Close settings" aria-label="Close settings" onClick={onClose} className="rounded-md p-2 text-slate-500 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-600"><X className="size-5" /></button></div>{loading ? <LoadingPanel label="Loading plugin settings" /> : error ? <ErrorPanel message={error} /> : value && <form className="flex min-h-0 flex-1 flex-col" onSubmit={save}><div className="min-h-0 flex-1 overflow-y-auto p-5"><PluginFields pluginId={plugin.id} value={value} setValue={setValue} /></div><div className="flex justify-end gap-2 border-t border-slate-200 bg-slate-50 px-5 py-3"><button type="button" className={secondaryButton} onClick={onClose} disabled={saving}>Cancel</button><button type="submit" className={primaryButton} disabled={saving}><Save className="size-4" />{saving ? "Saving" : "Save settings"}</button></div></form>}</section></div>;
}

function PluginFields({ pluginId, value, setValue }: { pluginId: string; value: Record<string, unknown>; setValue: (value: Record<string, unknown>) => void }) {
  const input = (key: string, label: string, options?: { maxLength?: number; type?: string; placeholder?: string }) => <label className="grid gap-2 text-sm font-medium">{label}<input className={fieldClass} type={options?.type ?? "text"} maxLength={options?.maxLength} placeholder={options?.placeholder} value={String(value[key] ?? "")} onChange={event => setValue({ ...value, [key]: event.target.value })} /></label>;
  if (pluginId === "favorite.plugin.example") return <div className="grid gap-5">{input("message", "Plugin message", { maxLength: 280 })}</div>;
  if (pluginId === "favorite.plugin.seo") return <div className="grid gap-5">{input("site_title", "SEO site title", { maxLength: 120 })}<label className="grid gap-2 text-sm font-medium">Meta description<textarea className={`${fieldClass} min-h-28 resize-y`} maxLength={320} value={String(value.description ?? "")} onChange={event => setValue({ ...value, description: event.target.value })} /></label>{input("canonical_base", "Canonical public origin", { type: "url", placeholder: "https://example.com" })}<label className="grid gap-2 text-sm font-medium">Default robots<select className={fieldClass} value={String(value.robots ?? "index,follow")} onChange={event => setValue({ ...value, robots: event.target.value })}><option value="index,follow">Index and follow</option><option value="noindex,nofollow">No index and no follow</option></select></label></div>;
  if (pluginId === "favorite.plugin.contact") return <div className="grid gap-5">{input("recipient", "Contact recipient", { type: "email", maxLength: 254 })}<label className="grid gap-2 text-sm font-medium">Delivery mode<select className={fieldClass} value={String(value.delivery ?? "pending")} onChange={event => setValue({ ...value, delivery: event.target.value })}><option value="pending">Pending</option></select></label>{typeof value.status === "object" && value.status !== null && <StatusSummary status={value.status as Record<string, unknown>} />}</div>;
  if (pluginId === "favorite.plugin.sitemap") return <div className="grid gap-5">{input("base_url", "Public base URL", { type: "url", placeholder: "https://example.com" })}</div>;
  if (pluginId === "favorite.plugin.analytics") return <div className="grid gap-5"><label className="grid gap-2 text-sm font-medium">Analytics provider<select className={fieldClass} value={String(value.provider ?? "none")} onChange={event => setValue({ ...value, provider: event.target.value })}><option value="none">Disabled</option><option value="first-party">First-party</option></select></label>{input("site_id", "Analytics site ID")}</div>;
  return null;
}

function StatusSummary({ status }: { status: Record<string, unknown> }) {
  return <div className="grid grid-cols-2 gap-px overflow-hidden rounded-md border border-slate-200 bg-slate-200 sm:grid-cols-4">{["pending", "delivered", "failed", "attempts"].map(key => <div key={key} className="bg-slate-50 p-3"><p className="text-xs capitalize text-slate-500">{key}</p><strong className="mt-1 block text-xl">{String(status[key] ?? 0)}</strong></div>)}</div>;
}

function cleanPayload(pluginId: string, value: Record<string, unknown>): Record<string, unknown> {
  if (pluginId === "favorite.plugin.contact") return { recipient: value.recipient ?? "", delivery: value.delivery ?? "pending" };
  return Object.fromEntries(Object.entries(value).filter(([key]) => key !== "status"));
}
