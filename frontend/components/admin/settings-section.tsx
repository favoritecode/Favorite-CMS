"use client";

import { type FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Blocks, Palette, Save, Settings, Settings2 } from "lucide-react";
import { adminRequest, isAuthenticationError } from "@/lib/admin-client";
import type { ExtensionItem } from "@/lib/admin-types";
import { ErrorPanel, fieldClass, LoadingPanel, primaryButton, secondaryButton, StatusBadge, useToast } from "./admin-ui";
import { PluginSettings } from "./plugin-settings";

type SettingValue = { value: string; customized: boolean };
type SiteSettings = Record<"site_title" | "site_tagline" | "site_description" | "public_origin" | "default_locale", SettingValue>;
type Values = Record<keyof SiteSettings, string>;

export function SettingsSection() {
  const router = useRouter();
  const { notify } = useToast();
  const [setting, setSetting] = useState<SiteSettings | null>(null);
  const [value, setValue] = useState<Values | null>(null);
  const [plugins, setPlugins] = useState<ExtensionItem[]>([]);
  const [configuration, setConfiguration] = useState<ExtensionItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const result = await adminRequest<SiteSettings>("/admin/manage/transport/settings");
      const extensions = await adminRequest<ExtensionItem[]>("/admin/manage/transport/extensions").catch(() => []);
      setSetting(result); setValue(settingValues(result));
      setPlugins(extensions.filter(item => item.type === "plugin" && item.state === "enabled" && configurablePlugins.has(item.id)));
    }
    catch (reason) {
      if (isAuthenticationError(reason)) { router.replace("/admin/login"); return; }
      setError(reason instanceof Error ? reason.message : "Settings could not be loaded.");
    } finally { setLoading(false); }
  }, [router]);
  useEffect(() => { void load(); }, [load]);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSaving(true);
    try { if (!value) return; const result = await adminRequest<SiteSettings>("/admin/manage/transport/settings", { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify(value) }); setSetting(result); setValue(settingValues(result)); notify("Site settings saved."); }
    catch (reason) { notify(reason instanceof Error ? reason.message : "Settings could not be saved.", "error"); }
    finally { setSaving(false); }
  }

  if (loading && !setting) return <LoadingPanel label="Loading settings" />;
  if (error) return <ErrorPanel message={error} onRetry={() => void load()} />;
  if (!value || !setting) return <ErrorPanel message="Settings are unavailable." onRetry={() => void load()} />;
  const changed = Object.entries(value).some(([key, item]) => setting[key as keyof SiteSettings].value !== item);
  const update = (key: keyof Values, next: string) => setValue(current => current ? { ...current, [key]: next } : current);
  return <div className="space-y-6">
    <section className="border border-slate-200 bg-white shadow-sm" aria-labelledby="site-settings-title"><div className="border-b border-slate-200 px-5 py-4"><div className="flex items-center gap-3"><span className="grid size-9 place-items-center rounded-md bg-sky-50 text-sky-700"><Settings className="size-[18px]" /></span><div><h2 id="site-settings-title" className="font-semibold">Website settings</h2><p className="mt-0.5 text-sm text-slate-500">Public identity and presentation defaults. Infrastructure secrets are never exposed here.</p></div></div></div><form onSubmit={save} className="grid gap-5 p-5 lg:grid-cols-2"><Field label="Site title" value={value.site_title} onChange={next => update("site_title", next)} required maxLength={120} help="Displayed as the website identity." /><Field label="Tagline" value={value.site_tagline} onChange={next => update("site_tagline", next)} maxLength={200} help="A short public introduction." /><label className="grid gap-2 text-sm font-medium lg:col-span-2">Site description<textarea className={`${fieldClass} min-h-24 resize-y`} value={value.site_description} onChange={event => update("site_description", event.target.value)} maxLength={500} /><span className="text-xs font-normal text-slate-500">A neutral public summary.</span></label><Field label="Public website origin" value={value.public_origin} onChange={next => update("public_origin", next)} type="url" maxLength={500} placeholder="https://example.com" help="Optional HTTP(S) origin without credentials or a path." /><label className="grid gap-2 text-sm font-medium">Default language<select className={fieldClass} value={value.default_locale} onChange={event => update("default_locale", event.target.value)}><option value="en">English</option><option value="fr">French</option></select><span className="text-xs font-normal text-slate-500">Only registered locales are available.</span></label><div className="flex items-center justify-between gap-3 border-t border-slate-100 pt-4 lg:col-span-2"><p className="text-xs text-slate-500">Stored by Settings Engine.</p><button type="submit" className={primaryButton} disabled={saving || !changed}><Save className="size-4" />{saving ? "Saving" : "Save changes"}</button></div></form></section>
    <section aria-labelledby="active-plugin-settings"><div className="mb-3 flex items-center gap-3"><span className="grid size-9 place-items-center rounded-md bg-violet-50 text-violet-700"><Blocks className="size-[18px]" /></span><div><h2 id="active-plugin-settings" className="font-semibold">Active Plugin settings</h2><p className="text-sm text-slate-500">Configure enabled Plugins through their own scoped contracts.</p></div></div>{plugins.length === 0 ? <div className="border border-dashed border-slate-300 bg-slate-50 p-5 text-sm text-slate-600">No configurable Plugin is active. Activate one from Plugins first.</div> : <div className="grid gap-3 md:grid-cols-2">{plugins.map(plugin => <article key={plugin.id} className="flex items-center gap-3 border border-slate-200 bg-white p-4 shadow-sm"><Blocks className="size-5 text-violet-700" /><div className="min-w-0 flex-1"><div className="flex items-center gap-2"><h3 className="truncate text-sm font-semibold">{plugin.name}</h3><StatusBadge value="active" /></div><p className="text-xs text-slate-500">v{plugin.version}</p></div><button type="button" className={secondaryButton} onClick={() => setConfiguration(plugin)}><Settings2 className="size-4" />Configure</button></article>)}</div>}</section>
    <aside className="flex items-center gap-3 border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600"><Palette className="size-5" /><span>Theme lifecycle remains under <Link className="font-semibold text-sky-700 underline" href="/admin/themes">Appearance → Themes</Link>.</span></aside>
    {configuration && <PluginSettings plugin={configuration} onClose={() => setConfiguration(null)} />}
  </div>;
}

const configurablePlugins = new Set(["favorite.plugin.example", "favorite.plugin.seo", "favorite.plugin.contact", "favorite.plugin.sitemap", "favorite.plugin.analytics"]);
function settingValues(settings: SiteSettings): Values { return Object.fromEntries(Object.entries(settings).map(([key, item]) => [key, item.value])) as Values; }
function Field({ label, value, onChange, help, ...input }: { label: string; value: string; onChange: (value: string) => void; help: string; required?: boolean; maxLength?: number; type?: string; placeholder?: string }) {
  return <label className="grid gap-2 text-sm font-medium">{label}<input className={fieldClass} value={value} onChange={event => onChange(event.target.value)} {...input} /><span className="text-xs font-normal text-slate-500">{help}</span></label>;
}
