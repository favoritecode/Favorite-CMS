"use client";

import { type FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Palette, Save, Search, Settings } from "lucide-react";
import { adminRequest, isAuthenticationError } from "@/lib/admin-client";
import { ErrorPanel, fieldClass, LoadingPanel, primaryButton, useToast } from "./admin-ui";

type SiteSetting = { key: string; value: string; customized: boolean };

export function SettingsSection() {
  const router = useRouter();
  const { notify } = useToast();
  const [setting, setSetting] = useState<SiteSetting | null>(null);
  const [value, setValue] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try { const result = await adminRequest<SiteSetting>("/admin/manage/transport/settings"); setSetting(result); setValue(result.value); }
    catch (reason) {
      if (isAuthenticationError(reason)) { router.replace("/admin/login"); return; }
      setError(reason instanceof Error ? reason.message : "Settings could not be loaded.");
    } finally { setLoading(false); }
  }, [router]);
  useEffect(() => { void load(); }, [load]);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSaving(true);
    try { const result = await adminRequest<SiteSetting>("/admin/manage/transport/settings", { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify({ value }) }); setSetting(result); setValue(result.value); notify("Site settings saved."); }
    catch (reason) { notify(reason instanceof Error ? reason.message : "Settings could not be saved.", "error"); }
    finally { setSaving(false); }
  }

  if (loading && !setting) return <LoadingPanel label="Loading settings" />;
  if (error) return <ErrorPanel message={error} onRetry={() => void load()} />;
  return <div className="grid gap-6 xl:grid-cols-[minmax(0,1.5fr)_minmax(18rem,0.7fr)]">
    <section className="border border-slate-200 bg-white shadow-sm" aria-labelledby="site-settings-title"><div className="border-b border-slate-200 px-5 py-4"><div className="flex items-center gap-3"><span className="grid size-9 place-items-center rounded-md bg-sky-50 text-sky-700"><Settings className="size-[18px]" /></span><div><h2 id="site-settings-title" className="font-semibold">General</h2><p className="mt-0.5 text-sm text-slate-500">Site identity settings owned by the platform.</p></div></div></div><form onSubmit={save} className="grid gap-5 p-5"><label className="grid gap-2 text-sm font-medium">Site title<input className={fieldClass} value={value} onChange={event => setValue(event.target.value)} required maxLength={500} /><span className="text-xs font-normal text-slate-500">Used by the Favorite CMS platform setting contract.</span></label><div className="flex items-center justify-between gap-3 border-t border-slate-100 pt-4"><p className="text-xs text-slate-500">{setting?.customized ? "Customized value" : "Platform default"}</p><button type="submit" className={primaryButton} disabled={saving || value === setting?.value}><Save className="size-4" />{saving ? "Saving" : "Save changes"}</button></div></form></section>
    <aside className="space-y-3" aria-labelledby="related-settings-title"><h2 id="related-settings-title" className="text-sm font-semibold uppercase text-slate-600">Related configuration</h2><RelatedLink href="/admin/themes" icon={Palette} title="Appearance" detail="Active theme and presentation lifecycle" /><RelatedLink href="/admin/plugins" icon={Search} title="SEO and plugins" detail="Plugin-owned configuration and capabilities" /></aside>
  </div>;
}

function RelatedLink({ href, icon: Icon, title, detail }: { href: string; icon: typeof Palette; title: string; detail: string }) {
  return <a href={href} className="flex items-center gap-3 rounded-md border border-slate-200 bg-white p-4 shadow-sm hover:border-sky-300 focus:outline-none focus:ring-2 focus:ring-sky-600"><span className="grid size-9 shrink-0 place-items-center rounded-md bg-slate-100 text-slate-600"><Icon className="size-[18px]" /></span><span className="min-w-0 flex-1"><strong className="block text-sm">{title}</strong><span className="mt-0.5 block text-xs leading-5 text-slate-500">{detail}</span></span><ArrowRight className="size-4 text-slate-400" /></a>;
}
