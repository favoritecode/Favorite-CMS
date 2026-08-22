"use client";

import { type FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Clipboard, FileText, Plus, Search, Upload, X } from "lucide-react";
import { adminRequest, isAuthenticationError } from "@/lib/admin-client";
import type { MediaItem } from "@/lib/admin-types";
import { EmptyState, ErrorPanel, fieldClass, LoadingPanel, primaryButton, secondaryButton, useToast } from "./admin-ui";

export function MediaSection() {
  const router = useRouter();
  const { notify } = useToast();
  const [items, setItems] = useState<MediaItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [uploadOpen, setUploadOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try { setItems(await adminRequest<MediaItem[]>("/admin/manage/transport/media")); }
    catch (reason) {
      if (isAuthenticationError(reason)) { router.replace("/admin/login"); return; }
      setError(reason instanceof Error ? reason.message : "Media could not be loaded.");
    } finally { setLoading(false); }
  }, [router]);
  useEffect(() => { void load(); }, [load]);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return normalized ? items.filter(item => item.name.toLowerCase().includes(normalized) || item.mime_type.toLowerCase().includes(normalized)) : items;
  }, [items, query]);

  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSubmitting(true);
    const form = new FormData(event.currentTarget);
    try {
      const labels = String(form.get("labels") ?? "").split(",").map(label => label.trim()).filter(Boolean);
      await adminRequest<MediaItem>("/admin/manage/transport/media", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ file_name: form.get("name"), mime_type: "text/plain", text: form.get("text"), description: form.get("description"), labels, visibility: form.get("visibility") }) });
      notify("Text document added to the media library."); setUploadOpen(false); await load();
    } catch (reason) { notify(reason instanceof Error ? reason.message : "Media upload failed.", "error"); }
    finally { setSubmitting(false); }
  }

  async function copyReference(item: MediaItem) {
    try { await navigator.clipboard.writeText(item.id); notify("Media reference copied."); }
    catch { notify("The media reference could not be copied.", "error"); }
  }

  return <div className="space-y-5">
    <div className="flex flex-col gap-3 border-y border-slate-200 bg-white p-4 sm:flex-row sm:items-center">
      <label className="relative min-w-0 flex-1"><span className="sr-only">Search media</span><Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" /><input className={`${fieldClass} pl-9`} value={query} onChange={event => setQuery(event.target.value)} placeholder="Search media library" /></label>
      <button type="button" className={primaryButton} onClick={() => setUploadOpen(true)}><Upload className="size-4" />Add document</button>
    </div>

    {loading && items.length === 0 ? <LoadingPanel label="Loading media library" /> : error ? <ErrorPanel message={error} onRetry={() => void load()} /> : filtered.length === 0 ? <EmptyState title={items.length ? "No matching media" : "Media library is empty"} detail={items.length ? "Try a different search term." : "The current Media contract accepts bounded UTF-8 text documents."} action={!items.length && <button className={primaryButton} onClick={() => setUploadOpen(true)}><Plus className="size-4" />Add document</button>} /> : <div className="overflow-hidden border border-slate-200 bg-white shadow-sm"><div className="overflow-x-auto"><table className="w-full min-w-[40rem] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-4 py-3 font-semibold">Document</th><th className="px-4 py-3 font-semibold">Type</th><th className="px-4 py-3 font-semibold">Size</th><th className="px-4 py-3 text-right font-semibold">Reference</th></tr></thead><tbody className="divide-y divide-slate-100">{filtered.map(item => <tr key={item.id} className="hover:bg-slate-50"><td className="px-4 py-3"><div className="flex items-center gap-3"><span className="grid size-10 place-items-center rounded-md bg-sky-50 text-sky-700"><FileText className="size-5" /></span><div className="min-w-0"><p className="max-w-md truncate font-semibold">{item.name}</p><p className="mt-0.5 font-mono text-xs text-slate-400">{item.id}</p></div></div></td><td className="px-4 py-3"><p className="font-medium capitalize">{item.type}</p><p className="text-xs text-slate-500">{item.mime_type}</p></td><td className="px-4 py-3 text-slate-600">{formatBytes(item.size)}</td><td className="px-4 py-3 text-right"><button type="button" title="Copy media reference" aria-label={`Copy reference for ${item.name}`} onClick={() => void copyReference(item)} className={secondaryButton}><Clipboard className="size-4" />Copy ID</button></td></tr>)}</tbody></table></div></div>}

    {uploadOpen && <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/45 p-4" role="presentation"><section role="dialog" aria-modal="true" aria-labelledby="upload-title" className="max-h-[94vh] w-full max-w-xl overflow-y-auto rounded-md bg-white shadow-2xl"><div className="flex items-center justify-between border-b border-slate-200 px-5 py-4"><div><p className="text-xs font-semibold uppercase text-sky-700">Media library</p><h2 id="upload-title" className="font-semibold">Add text document</h2></div><button type="button" title="Close" aria-label="Close upload" onClick={() => !submitting && setUploadOpen(false)} className="rounded-md p-2 text-slate-500 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-600"><X className="size-5" /></button></div><form className="grid gap-5 p-5" onSubmit={upload}><label className="grid gap-2 text-sm font-medium">File name<input name="name" className={fieldClass} required maxLength={255} pattern="[A-Za-z0-9][A-Za-z0-9._ -]*" placeholder="editorial-notes.txt" /><span className="text-xs font-normal text-slate-500">A safe file name without folders or paths.</span></label><label className="grid gap-2 text-sm font-medium">Meta description<textarea name="description" className={`${fieldClass} min-h-20 resize-y`} maxLength={320} placeholder="Short description for this media item" /></label><label className="grid gap-2 text-sm font-medium">Labels / tags<input name="labels" className={fieldClass} maxLength={820} placeholder="document, guide, internal" /><span className="text-xs font-normal text-slate-500">Comma-separated; maximum 20 labels.</span></label><label className="grid gap-2 text-sm font-medium">Visibility<select name="visibility" className={fieldClass} defaultValue="draft"><option value="draft">Draft</option><option value="published">Published</option><option value="unlisted">Unlisted</option><option value="private">Private</option></select></label><label className="grid gap-2 text-sm font-medium">Document content<textarea name="text" className={`${fieldClass} min-h-56 resize-y font-mono leading-6`} required maxLength={10000} placeholder="Plain UTF-8 text" /><span className="text-xs font-normal text-slate-500">Maximum 10,000 UTF-8 bytes. Binary image/video upload is not enabled.</span></label><div className="flex justify-end gap-2"><button type="button" className={secondaryButton} onClick={() => setUploadOpen(false)} disabled={submitting}>Cancel</button><button type="submit" className={primaryButton} disabled={submitting}><Upload className="size-4" />{submitting ? "Adding document" : "Add document"}</button></div></form></section></div>}
  </div>;
}

function formatBytes(value: number): string {
  if (value < 1024) return `${value} B`;
  return `${(value / 1024).toFixed(1)} KB`;
}
