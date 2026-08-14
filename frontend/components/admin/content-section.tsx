"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Archive, ExternalLink, Eye, FilePenLine, FileText, Plus, RefreshCw, Search, Send, Trash2, X } from "lucide-react";
import { AdminRequestError, adminRequest, isAuthenticationError } from "@/lib/admin-client";
import type { ContentCapabilities, ContentItem, ContentPreview } from "@/lib/admin-types";
import { manuallyEditedSlug, regeneratedSlug, slugifyTitle, titleDrivenSlug, uniqueSlugSuggestion } from "@/lib/content-editor";
import { ArticleEditor } from "./article-editor";
import { ConfirmDialog, EmptyState, ErrorPanel, fieldClass, LoadingPanel, primaryButton, secondaryButton, StatusBadge, useToast } from "./admin-ui";

type FieldErrors = Partial<Record<"title" | "slug" | "body", string>>;
type EditorState = { mode: "create" | "edit"; item?: ContentItem; title: string; slug: string; slugManual: boolean; body: string; errors: FieldErrors };
type Confirmation = { action: "publish" | "archive" | "delete"; item: ContentItem } | null;
const noCapabilities: ContentCapabilities = { create: false, read: false, update: false, delete: false, publish: false, archive: false };

export function ContentSection({ contentType }: { contentType: "post" | "page" }) {
  const singular = contentType === "post" ? "post" : "page";
  const plural = contentType === "post" ? "posts" : "pages";
  const router = useRouter(); const { notify } = useToast();
  const [items, setItems] = useState<ContentItem[]>([]); const [allItems, setAllItems] = useState<ContentItem[]>([]);
  const [capabilities, setCapabilities] = useState<ContentCapabilities>(noCapabilities);
  const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  const [query, setQuery] = useState(""); const [stateFilter, setStateFilter] = useState("all");
  const [editor, setEditor] = useState<EditorState | null>(null); const [preview, setPreview] = useState<ContentPreview | null>(null);
  const [confirmation, setConfirmation] = useState<Confirmation>(null); const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const [content, allowed] = await Promise.all([
        adminRequest<ContentItem[]>("/admin/manage/transport/content"),
        adminRequest<ContentCapabilities>("/admin/manage/transport/content-capabilities"),
      ]);
      setAllItems(content); setItems(content.filter(item => item.type === contentType)); setCapabilities(allowed);
    } catch (reason) {
      if (isAuthenticationError(reason)) { router.replace("/admin/login"); return; }
      setError(reason instanceof Error ? reason.message : "Content could not be loaded.");
    } finally { setLoading(false); }
  }, [contentType, router]);
  useEffect(() => { void load(); }, [load]);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return items.filter(item => (stateFilter === "all" || item.state === stateFilter) && (!normalized || item.title.toLowerCase().includes(normalized) || (item.data.slug ?? "").toLowerCase().includes(normalized)));
  }, [items, query, stateFilter]);

  function openCreate() { setEditor({ mode: "create", title: "", slug: "", slugManual: false, body: "<p></p>", errors: {} }); }
  function openEdit(item: ContentItem) { setEditor({ mode: "edit", item, title: item.title, slug: item.data.slug ?? "", slugManual: true, body: item.data.body ?? "<p></p>", errors: {} }); }
  function updateTitle(title: string) { setEditor(current => current ? { ...current, title, slug: titleDrivenSlug({ value: current.slug, manual: current.slugManual }, title).value, errors: { ...current.errors, title: undefined, slug: undefined } } : current); }
  function updateSlug(slug: string) { setEditor(current => current ? { ...current, ...manuallyEditedSlug(slug), slug: manuallyEditedSlug(slug).value, slugManual: true, errors: { ...current.errors, slug: undefined } } : current); }
  function regenerate() { setEditor(current => current ? { ...current, slug: regeneratedSlug(current.title).value, slugManual: false, errors: { ...current.errors, slug: undefined } } : current); }

  function validate(current: EditorState, publishing = false): boolean {
    const errors: FieldErrors = {};
    if (!current.title.trim()) errors.title = "Enter a title.";
    if (!current.slug.trim()) errors.slug = "Enter or generate a slug.";
    else if (!/^(?!-)(?!.*--)[\p{Letter}\p{Number}\p{Mark}]+(?:-[\p{Letter}\p{Number}\p{Mark}]+)*$/u.test(current.slug.normalize("NFKC").toLocaleLowerCase())) errors.slug = "Use letters, numbers, and single hyphens.";
    const hasText = current.body.replace(/<[^>]*>/g, "").replace(/&nbsp;/g, " ").trim().length > 0;
    if (!hasText && !/<img\s/i.test(current.body)) errors.body = "Add article content before saving.";
    if (publishing) {
      const duplicate = allItems.find(item => item.id !== current.item?.id && item.state !== "archived" && item.data.slug === current.slug);
      if (duplicate) errors.slug = `This slug is already used. Try ${uniqueSlugSuggestion(slugifyTitle(current.slug), allItems.map(item => item.data.slug ?? ""))}.`;
    }
    setEditor({ ...current, errors }); return Object.keys(errors).length === 0;
  }

  async function saveDraft() {
    if (!editor || !validate(editor)) return;
    setSubmitting(true);
    try {
      const body = editor.mode === "create"
        ? { type_id: contentType, title: editor.title, data: { slug: editor.slug, body: editor.body } }
        : { id: editor.item?.id, title: editor.title, data: { slug: editor.slug, body: editor.body }, action: "save" };
      const value = await adminRequest<ContentItem>("/admin/manage/transport/content", { method: editor.mode === "create" ? "POST" : "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
      notify(editor.mode === "create" ? "Draft created." : "Draft saved.");
      setEditor({ mode: "edit", item: value, title: value.title, slug: value.data.slug ?? "", slugManual: true, body: value.data.body ?? "", errors: {} }); await load();
    } catch (reason) { handleEditorError(reason, "Content could not be saved."); }
    finally { setSubmitting(false); }
  }

  async function showPreview() {
    if (!editor || !validate(editor)) return;
    setSubmitting(true);
    try {
      setPreview(await adminRequest<ContentPreview>("/admin/manage/transport/content-preview", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ title: editor.title, data: { slug: editor.slug, body: editor.body } }) }));
    } catch (reason) { handleEditorError(reason, "Preview could not be generated."); }
    finally { setSubmitting(false); }
  }

  function handleEditorError(reason: unknown, fallback: string) {
    const message = reason instanceof Error ? reason.message : fallback; const normalized = message.toLowerCase();
    if (editor) setEditor({ ...editor, errors: { ...editor.errors, ...(normalized.includes("slug") ? { slug: message } : normalized.includes("title") ? { title: message } : normalized.includes("body") ? { body: message } : {}) } });
    if (reason instanceof AdminRequestError && reason.status === 401) router.replace("/admin/login"); notify(message, "error");
  }

  async function confirmAction() {
    if (!confirmation) return; const { action, item } = confirmation;
    if (action === "publish" && editor && !validate(editor, true)) { setConfirmation(null); return; }
    setSubmitting(true);
    try {
      if (action === "delete") {
        await adminRequest<{ deleted: boolean }>("/admin/manage/transport/content", { method: "DELETE", headers: { "content-type": "application/json" }, body: JSON.stringify({ id: item.id }) }); notify(`${singular[0].toUpperCase()}${singular.slice(1)} deleted.`); if (editor?.item?.id === item.id) setEditor(null);
      } else {
        const source = action === "publish" && editor?.item?.id === item.id ? { ...item, title: editor.title, data: { slug: editor.slug, body: editor.body } } : item;
        const updated = await adminRequest<ContentItem>("/admin/manage/transport/content", { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify({ id: source.id, title: source.title, data: source.data, action }) });
        notify(action === "publish" ? `${singular[0].toUpperCase()}${singular.slice(1)} published.` : `${singular[0].toUpperCase()}${singular.slice(1)} archived.`);
        if (editor?.item?.id === item.id) setEditor({ ...editor, item: updated, title: updated.title, slug: updated.data.slug ?? "", body: updated.data.body ?? "", errors: {} });
      }
      setConfirmation(null); await load();
    } catch (reason) { handleEditorError(reason, "Content action failed."); }
    finally { setSubmitting(false); }
  }

  return <div className="space-y-5">
    <div className="flex flex-col gap-3 border-y border-slate-200 bg-white p-4 sm:flex-row sm:items-center">
      <label className="relative min-w-0 flex-1"><span className="sr-only">Search {plural}</span><Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" /><input className={`${fieldClass} pl-9`} value={query} onChange={event => setQuery(event.target.value)} placeholder={`Search ${plural}`} /></label>
      <label className="sm:w-44"><span className="sr-only">Filter by state</span><select className={fieldClass} value={stateFilter} onChange={event => setStateFilter(event.target.value)}><option value="all">All states</option><option value="draft">Draft</option><option value="published">Published</option><option value="archived">Archived</option></select></label>
      <button type="button" className={primaryButton} onClick={openCreate} disabled={!capabilities.create} title={!capabilities.create ? "Create permission is required" : undefined}><Plus className="size-4" />New {singular}</button>
    </div>
    {loading && items.length === 0 ? <LoadingPanel label={`Loading ${plural}`} /> : error ? <ErrorPanel message={error} onRetry={() => void load()} /> : filtered.length === 0 ? <EmptyState title={items.length ? `No matching ${plural}` : `No ${plural} yet`} detail={items.length ? "Change the search or state filter." : `Create your first ${singular} as a private draft.`} action={!items.length && capabilities.create ? <button className={primaryButton} onClick={openCreate}><Plus className="size-4" />Create {singular}</button> : undefined} /> : <ContentTable items={filtered} capabilities={capabilities} onEdit={openEdit} onAction={(action, item) => setConfirmation({ action, item })} />}
    {editor && <EditorPanel editor={editor} singular={singular} capabilities={capabilities} busy={submitting} onTitle={updateTitle} onSlug={updateSlug} onRegenerate={regenerate} onBody={body => setEditor({ ...editor, body, errors: { ...editor.errors, body: undefined } })} onClose={() => !submitting && setEditor(null)} onSave={() => void saveDraft()} onPreview={() => void showPreview()} onAction={(action, item) => setConfirmation({ action, item })} />}
    {preview && <PreviewDialog preview={preview} onClose={() => setPreview(null)} />}
    <ConfirmDialog open={confirmation !== null} title={confirmation?.action === "delete" ? `Delete ${singular}?` : confirmation?.action === "publish" ? `Publish this ${singular}?` : `Archive this ${singular}?`} detail={confirmation?.action === "delete" ? "This permanently deletes the content record. This action cannot be undone." : confirmation?.action === "publish" ? "The saved draft and current editor changes will become public." : "This content will leave the published workflow."} confirmLabel={confirmation?.action === "delete" ? "Delete" : confirmation?.action === "publish" ? "Publish" : "Archive"} tone={confirmation?.action === "publish" ? "primary" : "danger"} busy={submitting} onCancel={() => setConfirmation(null)} onConfirm={() => void confirmAction()} />
  </div>;
}

function ContentTable({ items, capabilities, onEdit, onAction }: { items: ContentItem[]; capabilities: ContentCapabilities; onEdit: (item: ContentItem) => void; onAction: (action: "publish" | "archive" | "delete", item: ContentItem) => void }) {
  return <div className="overflow-hidden border border-slate-200 bg-white shadow-sm"><div className="overflow-x-auto"><table className="w-full min-w-[46rem] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-4 py-3 font-semibold">Title</th><th className="px-4 py-3 font-semibold">Slug</th><th className="px-4 py-3 font-semibold">State</th><th className="px-4 py-3 text-right font-semibold">Actions</th></tr></thead><tbody className="divide-y divide-slate-100">{items.map(item => <tr key={item.id} className="hover:bg-slate-50"><td className="px-4 py-3"><button type="button" onClick={() => onEdit(item)} className="flex items-center gap-3 text-left font-semibold hover:text-sky-700 focus:outline-none focus:ring-2 focus:ring-sky-600"><span className="grid size-9 place-items-center rounded-md bg-slate-100 text-slate-500"><FileText className="size-[18px]" /></span><span className="max-w-sm truncate">{item.title}</span></button></td><td className="px-4 py-3 font-mono text-xs text-slate-600">/{item.data.slug}</td><td className="px-4 py-3"><StatusBadge value={item.state} /></td><td className="px-4 py-3"><div className="flex justify-end gap-1"><Action title="Edit" onClick={() => onEdit(item)}><FilePenLine /></Action>{item.state === "draft" && capabilities.publish && <Action title="Publish" onClick={() => onAction("publish", item)}><Send /></Action>}{item.state === "published" && <a href={`/site/content/${encodeURIComponent(item.id)}`} target="_blank" rel="noreferrer" title="View live" aria-label="View live" className="rounded-md p-2 text-slate-500 hover:bg-slate-100 hover:text-sky-700"><ExternalLink className="size-4" /></a>}{item.state === "published" && capabilities.archive && <Action title="Archive" onClick={() => onAction("archive", item)}><Archive /></Action>}{capabilities.delete && <Action title="Delete" danger onClick={() => onAction("delete", item)}><Trash2 /></Action>}</div></td></tr>)}</tbody></table></div></div>;
}
function Action({ title, danger, onClick, children }: { title: string; danger?: boolean; onClick: () => void; children: React.ReactNode }) { return <button type="button" title={title} aria-label={title} onClick={onClick} className={`rounded-md p-2 focus:outline-none focus:ring-2 ${danger ? "text-red-600 hover:bg-red-50 focus:ring-red-600" : "text-slate-500 hover:bg-slate-100 hover:text-sky-700 focus:ring-sky-600"}`}><span className="[&>svg]:size-4">{children}</span></button>; }

function EditorPanel({ editor, singular, capabilities, busy, onTitle, onSlug, onRegenerate, onBody, onClose, onSave, onPreview, onAction }: { editor: EditorState; singular: string; capabilities: ContentCapabilities; busy: boolean; onTitle: (value: string) => void; onSlug: (value: string) => void; onRegenerate: () => void; onBody: (value: string) => void; onClose: () => void; onSave: () => void; onPreview: () => void; onAction: (action: "publish" | "delete", item: ContentItem) => void }) {
  const canSave = editor.mode === "create" ? capabilities.create : capabilities.update;
  const canPublish = editor.mode === "edit" && editor.item?.state === "draft" && capabilities.update && capabilities.publish;
  return <div className="fixed inset-0 z-50 bg-slate-950/45 p-0 lg:p-4" role="presentation"><section role="dialog" aria-modal="true" aria-labelledby="editor-title" className="mx-auto flex h-full w-full max-w-[94rem] flex-col bg-slate-100 shadow-2xl lg:rounded-md">
    <header className="flex min-h-16 items-center justify-between gap-3 border-b border-slate-200 bg-white px-4 sm:px-6"><div className="min-w-0"><p className="text-xs font-semibold uppercase text-sky-700">{editor.mode === "create" ? `New ${singular}` : editor.item?.state}</p><h2 id="editor-title" className="truncate font-semibold">{editor.title || `Untitled ${singular}`}</h2></div><div className="flex items-center gap-2"><button type="button" className={secondaryButton} onClick={onPreview} disabled={busy}><Eye className="size-4" />Preview</button><button type="button" title="Close editor" aria-label="Close editor" onClick={onClose} disabled={busy} className="rounded-md p-2 text-slate-500 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-600"><X className="size-5" /></button></div></header>
    <div className="min-h-0 flex-1 overflow-y-auto p-4 sm:p-6"><div className="mx-auto grid max-w-[86rem] gap-5 xl:grid-cols-[minmax(0,1fr)_19rem]">
      <main className="min-w-0 space-y-4"><label className="grid gap-1.5"><span className="text-sm font-semibold">Title</span><input className={`min-h-14 w-full rounded-md border bg-white px-4 text-xl font-semibold outline-none focus:ring-2 ${editor.errors.title ? "border-red-400 focus:ring-red-100" : "border-slate-300 focus:border-sky-600 focus:ring-sky-100"}`} value={editor.title} onChange={event => onTitle(event.target.value)} maxLength={500} placeholder={`Add ${singular} title`} autoFocus />{editor.errors.title && <span className="text-sm text-red-700" role="alert">{editor.errors.title}</span>}</label><div><ArticleEditor value={editor.body} onChange={onBody} disabled={busy || !canSave} />{editor.errors.body && <p className="mt-1.5 text-sm text-red-700" role="alert">{editor.errors.body}</p>}</div></main>
      <aside className="space-y-4"><section className="border border-slate-200 bg-white p-4 shadow-sm"><h3 className="text-sm font-semibold">Publishing</h3><dl className="mt-4 grid grid-cols-[auto_1fr] gap-x-3 gap-y-3 text-sm"><dt className="text-slate-500">Status</dt><dd className="text-right"><StatusBadge value={editor.item?.state ?? "draft"} /></dd><dt className="text-slate-500">Visibility</dt><dd className="text-right font-medium">{editor.item?.state === "published" ? "Public" : "Private"}</dd></dl><div className="mt-5 grid gap-2"><button type="button" className={primaryButton} onClick={onSave} disabled={busy || !canSave}>{editor.item?.state === "published" ? "Save changes" : "Save draft"}</button>{editor.item?.state === "draft" && <button type="button" className={secondaryButton} onClick={() => editor.item && onAction("publish", editor.item)} disabled={busy || !canPublish}><Send className="size-4" />Publish</button>}</div></section>
        <section className="border border-slate-200 bg-white p-4 shadow-sm"><div className="flex items-center justify-between gap-2"><h3 className="text-sm font-semibold">Slug</h3><button type="button" title="Regenerate slug" aria-label="Regenerate slug" onClick={onRegenerate} className="rounded p-1.5 text-slate-500 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-600"><RefreshCw className="size-4" /></button></div><div className="mt-3 flex items-center rounded-md border border-slate-300 focus-within:border-sky-600 focus-within:ring-2 focus-within:ring-sky-100"><span className="pl-3 text-sm text-slate-400">/</span><input aria-label="Slug" className="min-h-10 min-w-0 flex-1 border-0 bg-transparent px-1 py-2 text-sm outline-none" value={editor.slug} onChange={event => onSlug(event.target.value)} maxLength={120} /></div>{editor.errors.slug && <p className="mt-2 text-sm text-red-700" role="alert">{editor.errors.slug}</p>}</section>
        {editor.item && capabilities.delete && <button type="button" className="inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-md border border-red-300 bg-white px-3 text-sm font-semibold text-red-700 hover:bg-red-50" onClick={() => onAction("delete", editor.item)} disabled={busy}><Trash2 className="size-4" />Delete {singular}</button>}
      </aside>
    </div></div>
    <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 bg-white px-4 py-3 sm:px-6"><button type="button" className={secondaryButton} onClick={onPreview} disabled={busy}><Eye className="size-4" />Preview</button><div className="flex gap-2">{editor.item?.state === "draft" && <button type="button" className={secondaryButton} onClick={() => editor.item && onAction("publish", editor.item)} disabled={busy || !canPublish}><Send className="size-4" />Publish</button>}<button type="button" className={primaryButton} onClick={onSave} disabled={busy || !canSave}>{editor.item?.state === "published" ? "Save changes" : "Save draft"}</button></div></footer>
  </section></div>;
}

function PreviewDialog({ preview, onClose }: { preview: ContentPreview; onClose: () => void }) { return <div className="fixed inset-0 z-[70] bg-slate-950/60 p-0 sm:p-4" role="presentation"><section role="dialog" aria-modal="true" aria-labelledby="preview-title" className="mx-auto flex h-full max-w-6xl flex-col bg-white shadow-2xl sm:rounded-md"><header className="flex min-h-16 items-center justify-between border-b border-slate-200 px-4 sm:px-6"><div><p className="text-xs font-semibold uppercase text-sky-700">Sanitized preview</p><h2 id="preview-title" className="font-semibold">{preview.title}</h2></div><button type="button" title="Close preview" aria-label="Close preview" onClick={onClose} className="rounded p-2 text-slate-500 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-600"><X className="size-5" /></button></header><div className="min-h-0 flex-1 overflow-y-auto bg-slate-50"><div className="public-preview mx-auto bg-white" dangerouslySetInnerHTML={{ __html: preview.html }} /></div></section></div>; }
