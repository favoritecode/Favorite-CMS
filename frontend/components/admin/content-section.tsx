"use client";

import { type FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Archive, ExternalLink, Eye, FilePenLine, FileText, Plus, RefreshCw, Search, Send, Trash2, X } from "lucide-react";
import { AdminRequestError, adminRequest, isAuthenticationError } from "@/lib/admin-client";
import type { ContentCapabilities, ContentItem, ContentPreview } from "@/lib/admin-types";
import { manuallyEditedSlug, regeneratedSlug, slugifyTitle, titleDrivenSlug, uniqueSlugSuggestion } from "@/lib/content-editor";
import { ArticleEditor } from "./article-editor";
import { uploadAdminImage } from "@/lib/media-upload";
import { ConfirmDialog, EmptyState, ErrorPanel, fieldClass, LoadingPanel, primaryButton, secondaryButton, StatusBadge, useToast } from "./admin-ui";

type FieldErrors = Partial<Record<"title" | "slug" | "body" | "featuredImage" | "labels", string>>;
type VisibilityChoice = "draft" | "published" | "unlisted" | "private";
type EditorState = { mode: "create" | "edit"; item?: ContentItem; title: string; slug: string; slugManual: boolean; body: string; featuredImage: string; labels: string; visibility: VisibilityChoice; errors: FieldErrors };
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
  const [autosaving, setAutosaving] = useState(false); const [autosaveStatus, setAutosaveStatus] = useState("Draft autosave starts after required fields are complete.");
  const autosaveSequence = useRef(0); const autosaveInFlight = useRef(false); const editorRef = useRef<EditorState | null>(null); editorRef.current = editor;
  const [autosaveRetry, setAutosaveRetry] = useState(0);
  const draftFingerprint = editor ? JSON.stringify([editor.title, editor.slug, editor.body, editor.featuredImage, editor.labels, editor.visibility]) : "";
  const latestFingerprint = useRef(draftFingerprint); latestFingerprint.current = draftFingerprint;

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

  function openCreate() { setAutosaveStatus("Draft autosave starts after required fields are complete."); setEditor({ mode: "create", title: "", slug: "", slugManual: false, body: "<p></p>", featuredImage: "", labels: "", visibility: "published", errors: {} }); }
  function openEdit(item: ContentItem) { const visibility: VisibilityChoice = item.state === "draft" ? "draft" : item.data.visibility === "unlisted" ? "unlisted" : item.data.visibility === "private" ? "private" : "published"; setAutosaveStatus(item.state === "draft" ? "Draft is saved." : "Published changes are saved manually."); setEditor({ mode: "edit", item, title: item.title, slug: item.data.slug ?? "", slugManual: true, body: item.data.body ?? "<p></p>", featuredImage: item.data.featured_image ?? "", labels: (item.data.labels ?? []).join(", "), visibility, errors: {} }); }
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
    if (current.featuredImage && !validFeaturedImage(current.featuredImage)) errors.featuredImage = "Use an HTTP, HTTPS, or site-relative image URL.";
    if (contentLabels(current.labels).length > 20 || contentLabels(current.labels).some(label => label.length > 40)) errors.labels = "Use at most 20 labels, up to 40 characters each.";
    if (publishing) {
      const duplicate = allItems.find(item => item.id !== current.item?.id && item.state !== "archived" && item.data.slug === current.slug);
      if (duplicate) errors.slug = `This slug is already used. Try ${uniqueSlugSuggestion(slugifyTitle(current.slug), allItems.map(item => item.data.slug ?? ""))}.`;
    }
    setEditor({ ...current, errors }); return Object.keys(errors).length === 0;
  }

  useEffect(() => {
    const snapshot = editorRef.current;
    if (!snapshot || snapshot.item?.state === "published" || submitting) return;
    if (!draftReady(snapshot)) { setAutosaveStatus("Waiting for a valid title, slug, and article body."); return; }
    const sequence = ++autosaveSequence.current;
    setAutosaveStatus("Unsaved changes…");
    const timer = window.setTimeout(async () => {
      if (autosaveInFlight.current) { setAutosaveRetry(value => value + 1); return; }
      autosaveInFlight.current = true;
      setAutosaving(true); setAutosaveStatus("Saving draft…");
      try {
        const payload = snapshot.mode === "create"
          ? { type_id: contentType, title: snapshot.title, data: editorData(snapshot) }
          : { id: snapshot.item?.id, title: snapshot.title, data: editorData(snapshot), action: "save" };
        const value = await adminRequest<ContentItem>("/admin/manage/transport/content", { method: snapshot.mode === "create" ? "POST" : "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify(payload) });
        if (sequence !== autosaveSequence.current) {
          if (snapshot.mode === "create") {
            setEditor(current => current ? { ...current, mode: "edit", item: value } : current);
            setItems(current => replaceContent(current, value, contentType)); setAllItems(current => replaceContent(current, value));
          }
          return;
        }
        setEditor(current => current ? { ...current, mode: "edit", item: value, errors: {} } : current);
        setItems(current => replaceContent(current, value, contentType)); setAllItems(current => replaceContent(current, value));
        setAutosaveStatus("Draft saved automatically.");
      } catch (reason) {
        if (sequence !== autosaveSequence.current) return;
        setAutosaveStatus("Autosave failed. Review the fields and try again.");
        if (isAuthenticationError(reason)) router.replace("/admin/login");
        notify(reason instanceof Error ? reason.message : "Draft could not be autosaved.", "error");
      } finally {
        autosaveInFlight.current = false;
        if (sequence === autosaveSequence.current) setAutosaving(false);
        if (latestFingerprint.current !== draftFingerprint) setAutosaveRetry(value => value + 1);
      }
    }, 1_500);
    return () => window.clearTimeout(timer);
  }, [draftFingerprint, contentType, submitting, autosaveRetry, notify, router]);

  async function saveDraft() {
    if (!editor || !validate(editor)) return;
    setSubmitting(true);
    try {
      const body = editor.mode === "create"
        ? { type_id: contentType, title: editor.title, data: editorData(editor) }
        : { id: editor.item?.id, title: editor.title, data: editorData(editor), action: editor.item?.state === "published" && editor.visibility === "draft" ? "unpublish" : "save" };
      const value = await adminRequest<ContentItem>("/admin/manage/transport/content", { method: editor.mode === "create" ? "POST" : "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
      notify(editor.mode === "create" ? "Draft created." : "Draft saved.");
      openEdit(value); await load();
    } catch (reason) { handleEditorError(reason, "Content could not be saved."); }
    finally { setSubmitting(false); }
  }

  async function showPreview() {
    if (!editor || !validate(editor)) return;
    setSubmitting(true);
    try {
      setPreview(await adminRequest<ContentPreview>("/admin/manage/transport/content-preview", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ title: editor.title, data: editorData(editor) }) }));
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
        const source = action === "publish" && editor?.item?.id === item.id ? { ...item, title: editor.title, data: editorData(editor) } : item;
        const updated = await adminRequest<ContentItem>("/admin/manage/transport/content", { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify({ id: source.id, title: source.title, data: source.data, action }) });
        notify(action === "publish" ? `${singular[0].toUpperCase()}${singular.slice(1)} published.` : `${singular[0].toUpperCase()}${singular.slice(1)} archived.`);
        if (editor?.item?.id === item.id) openEdit(updated);
      }
      setConfirmation(null); await load();
    } catch (reason) { handleEditorError(reason, "Content action failed."); }
    finally { setSubmitting(false); }
  }

  async function publishNow() {
    if (!editor || !validate(editor, true)) return;
    setSubmitting(true); autosaveSequence.current += 1;
    try {
      let draft = editor.item;
      if (!draft) {
        draft = await adminRequest<ContentItem>("/admin/manage/transport/content", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ type_id: contentType, title: editor.title, data: editorData(editor) }) });
      }
      const published = await adminRequest<ContentItem>("/admin/manage/transport/content", { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify({ id: draft.id, title: editor.title, data: editorData(editor), action: "publish" }) });
      openEdit(published);
      setAutosaveStatus("Published changes are saved manually."); notify(`${singular[0].toUpperCase()}${singular.slice(1)} published.`); await load();
    } catch (reason) { handleEditorError(reason, "Content could not be published."); }
    finally { setSubmitting(false); }
  }

  return <div className="space-y-5">
    <div className="flex flex-col gap-3 border-y border-slate-200 bg-white p-4 sm:flex-row sm:items-center">
      <label className="relative min-w-0 flex-1"><span className="sr-only">Search {plural}</span><Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" /><input className={`${fieldClass} pl-9`} value={query} onChange={event => setQuery(event.target.value)} placeholder={`Search ${plural}`} /></label>
      <label className="sm:w-44"><span className="sr-only">Filter by state</span><select className={fieldClass} value={stateFilter} onChange={event => setStateFilter(event.target.value)}><option value="all">All states</option><option value="draft">Draft</option><option value="published">Published</option><option value="archived">Archived</option></select></label>
      <button type="button" className={primaryButton} onClick={openCreate} disabled={!capabilities.create} title={!capabilities.create ? "Create permission is required" : undefined}><Plus className="size-4" />New {singular}</button>
    </div>
    {loading && items.length === 0 ? <LoadingPanel label={`Loading ${plural}`} /> : error ? <ErrorPanel message={error} onRetry={() => void load()} /> : filtered.length === 0 ? <EmptyState title={items.length ? `No matching ${plural}` : `No ${plural} yet`} detail={items.length ? "Change the search or state filter." : `Create your first ${singular} as a private draft.`} action={!items.length && capabilities.create ? <button className={primaryButton} onClick={openCreate}><Plus className="size-4" />Create {singular}</button> : undefined} /> : <ContentTable items={filtered} capabilities={capabilities} onEdit={openEdit} onAction={(action, item) => setConfirmation({ action, item })} />}
    {editor && <EditorPanel editor={editor} singular={singular} capabilities={capabilities} busy={submitting || autosaving} autosaveStatus={autosaveStatus} onTitle={updateTitle} onSlug={updateSlug} onRegenerate={regenerate} onBody={body => setEditor({ ...editor, body, errors: { ...editor.errors, body: undefined } })} onFeaturedImage={featuredImage => setEditor({ ...editor, featuredImage, errors: { ...editor.errors, featuredImage: undefined } })} onLabels={labels => setEditor({ ...editor, labels, errors: { ...editor.errors, labels: undefined } })} onVisibility={visibility => setEditor({ ...editor, visibility })} onClose={() => !submitting && !autosaving && setEditor(null)} onSave={() => void saveDraft()} onPublish={() => void publishNow()} onPreview={() => void showPreview()} onAction={(action, item) => setConfirmation({ action, item })} />}
    {preview && <PreviewDialog preview={preview} onClose={() => setPreview(null)} />}
    <ConfirmDialog open={confirmation !== null} title={confirmation?.action === "delete" ? `Delete ${singular}?` : confirmation?.action === "publish" ? `Publish this ${singular}?` : `Archive this ${singular}?`} detail={confirmation?.action === "delete" ? "This permanently deletes the content record. This action cannot be undone." : confirmation?.action === "publish" ? "The saved draft and current editor changes will become public." : "This content will leave the published workflow."} confirmLabel={confirmation?.action === "delete" ? "Delete" : confirmation?.action === "publish" ? "Publish" : "Archive"} tone={confirmation?.action === "publish" ? "primary" : "danger"} busy={submitting} onCancel={() => setConfirmation(null)} onConfirm={() => void confirmAction()} />
  </div>;
}

function editorData(editor: EditorState) {
  return { slug: editor.slug, body: editor.body, featured_image: editor.featuredImage.trim(), labels: contentLabels(editor.labels), visibility: editor.visibility === "published" ? "public" : editor.visibility === "draft" ? "private" : editor.visibility };
}

function contentLabels(value: string): string[] { return [...new Map(value.split(",").map(label => label.trim()).filter(Boolean).map(label => [label.toLocaleLowerCase(), label])).values()]; }

function validFeaturedImage(value: string): boolean {
  const reference = value.trim();
  if (!reference || reference.length > 1_000 || /[\r\n\t]/.test(reference)) return false;
  if (reference.startsWith("/") && !reference.startsWith("//")) return true;
  try {
    const parsed = new URL(reference);
    return (parsed.protocol === "http:" || parsed.protocol === "https:") && !parsed.username && !parsed.password;
  } catch { return false; }
}

function draftReady(editor: EditorState): boolean {
  const slugReady = /^(?!-)(?!.*--)[\p{Letter}\p{Number}\p{Mark}]+(?:-[\p{Letter}\p{Number}\p{Mark}]+)*$/u.test(editor.slug.normalize("NFKC").toLocaleLowerCase());
  const bodyReady = editor.body.replace(/<[^>]*>/g, "").replace(/&nbsp;/g, " ").trim().length > 0 || /<img\s/i.test(editor.body);
  return Boolean(editor.title.trim() && slugReady && bodyReady && (!editor.featuredImage || validFeaturedImage(editor.featuredImage)));
}

function replaceContent(items: ContentItem[], value: ContentItem, type?: string): ContentItem[] {
  if (type && value.type !== type) return items;
  return items.some(item => item.id === value.id) ? items.map(item => item.id === value.id ? value : item) : [...items, value];
}

function ContentTable({ items, capabilities, onEdit, onAction }: { items: ContentItem[]; capabilities: ContentCapabilities; onEdit: (item: ContentItem) => void; onAction: (action: "publish" | "archive" | "delete", item: ContentItem) => void }) {
  return <div className="overflow-hidden border border-slate-200 bg-white shadow-sm"><div className="overflow-x-auto"><table className="w-full min-w-[46rem] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-4 py-3 font-semibold">Title</th><th className="px-4 py-3 font-semibold">Slug</th><th className="px-4 py-3 font-semibold">State</th><th className="px-4 py-3 text-right font-semibold">Actions</th></tr></thead><tbody className="divide-y divide-slate-100">{items.map(item => <tr key={item.id} className="hover:bg-slate-50"><td className="px-4 py-3"><button type="button" onClick={() => onEdit(item)} className="flex items-center gap-3 text-left font-semibold hover:text-sky-700 focus:outline-none focus:ring-2 focus:ring-sky-600"><span className="grid size-9 place-items-center rounded-md bg-slate-100 text-slate-500"><FileText className="size-[18px]" /></span><span className="max-w-sm truncate">{item.title}</span></button></td><td className="px-4 py-3 font-mono text-xs text-slate-600">/{item.data.slug}</td><td className="px-4 py-3"><StatusBadge value={item.state} /></td><td className="px-4 py-3"><div className="flex justify-end gap-1"><Action title="Edit" onClick={() => onEdit(item)}><FilePenLine /></Action>{item.state === "draft" && capabilities.publish && <Action title="Publish" onClick={() => onAction("publish", item)}><Send /></Action>}{item.state === "published" && <a href={`/site/content/${encodeURIComponent(item.id)}`} target="_blank" rel="noreferrer" title="View live" aria-label="View live" className="rounded-md p-2 text-slate-500 hover:bg-slate-100 hover:text-sky-700"><ExternalLink className="size-4" /></a>}{item.state === "published" && capabilities.archive && <Action title="Archive" onClick={() => onAction("archive", item)}><Archive /></Action>}{capabilities.delete && <Action title="Delete" danger onClick={() => onAction("delete", item)}><Trash2 /></Action>}</div></td></tr>)}</tbody></table></div></div>;
}
function Action({ title, danger, onClick, children }: { title: string; danger?: boolean; onClick: () => void; children: React.ReactNode }) { return <button type="button" title={title} aria-label={title} onClick={onClick} className={`rounded-md p-2 focus:outline-none focus:ring-2 ${danger ? "text-red-600 hover:bg-red-50 focus:ring-red-600" : "text-slate-500 hover:bg-slate-100 hover:text-sky-700 focus:ring-sky-600"}`}><span className="[&>svg]:size-4">{children}</span></button>; }

function EditorPanel({ editor, singular, capabilities, busy, autosaveStatus, onTitle, onSlug, onRegenerate, onBody, onFeaturedImage, onLabels, onVisibility, onClose, onSave, onPublish, onPreview, onAction }: { editor: EditorState; singular: string; capabilities: ContentCapabilities; busy: boolean; autosaveStatus: string; onTitle: (value: string) => void; onSlug: (value: string) => void; onRegenerate: () => void; onBody: (value: string) => void; onFeaturedImage: (value: string) => void; onLabels: (value: string) => void; onVisibility: (value: VisibilityChoice) => void; onClose: () => void; onSave: () => void; onPublish: () => void; onPreview: () => void; onAction: (action: "publish" | "delete", item: ContentItem) => void }) {
  const canSave = editor.mode === "create" ? capabilities.create : capabilities.update;
  const canPublish = editor.item?.state !== "published" && capabilities.create && capabilities.update && capabilities.publish;
  return <div className="fixed inset-0 z-50 bg-slate-950/45 p-0 lg:p-4" role="presentation"><section role="dialog" aria-modal="true" aria-labelledby="editor-title" className="mx-auto flex h-full w-full max-w-[94rem] flex-col bg-slate-100 shadow-2xl lg:rounded-md">
    <header className="flex min-h-16 items-center justify-between gap-3 border-b border-slate-200 bg-white px-4 sm:px-6"><div className="min-w-0"><p className="text-xs font-semibold uppercase text-sky-700">{editor.mode === "create" ? `New ${singular}` : editor.item?.state}</p><h2 id="editor-title" className="truncate font-semibold">{editor.title || `Untitled ${singular}`}</h2></div><div className="flex items-center gap-2"><button type="button" className={secondaryButton} onClick={onPreview} disabled={busy}><Eye className="size-4" />Preview</button><button type="button" title="Close editor" aria-label="Close editor" onClick={onClose} disabled={busy} className="rounded-md p-2 text-slate-500 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-600"><X className="size-5" /></button></div></header>
    <div className="min-h-0 flex-1 overflow-y-auto p-4 sm:p-6"><div className="mx-auto grid max-w-[86rem] gap-5 xl:grid-cols-[minmax(0,1fr)_19rem]">
      <main className="min-w-0 space-y-4"><label className="grid gap-1.5"><span className="text-sm font-semibold">Title</span><input className={`min-h-14 w-full rounded-md border bg-white px-4 text-xl font-semibold outline-none focus:ring-2 ${editor.errors.title ? "border-red-400 focus:ring-red-100" : "border-slate-300 focus:border-sky-600 focus:ring-sky-100"}`} value={editor.title} onChange={event => onTitle(event.target.value)} maxLength={500} placeholder={`Add ${singular} title`} autoFocus />{editor.errors.title && <span className="text-sm text-red-700" role="alert">{editor.errors.title}</span>}</label><div><ArticleEditor value={editor.body} onChange={onBody} disabled={busy || !canSave} />{editor.errors.body && <p className="mt-1.5 text-sm text-red-700" role="alert">{editor.errors.body}</p>}</div></main>
      <aside className="space-y-4"><section className="border border-slate-200 bg-white p-4 shadow-sm"><h3 className="text-sm font-semibold">Publishing</h3><dl className="mt-4 grid grid-cols-[auto_1fr] gap-x-3 gap-y-3 text-sm"><dt className="text-slate-500">Status</dt><dd className="text-right"><StatusBadge value={editor.item?.state ?? "draft"} /></dd></dl><label className="mt-4 grid gap-1.5 text-xs font-medium text-slate-700">Visibility<select className={fieldClass} value={editor.visibility} onChange={event => onVisibility(event.target.value as VisibilityChoice)}><option value="draft">Draft</option><option value="published">Published — public and searchable</option><option value="unlisted">Unlisted — direct link only</option><option value="private">Private — signed-in access only</option></select></label><p className="mt-2 text-xs leading-5 text-slate-500">Draft stays unpublished. Unlisted is hidden from listings, Search and Sitemap. Private is never publicly accessible.</p><p className="mt-4 text-xs leading-5 text-slate-500" role="status" aria-live="polite">{autosaveStatus}</p><div className="mt-5 grid gap-2">{editor.item?.state === "published" || editor.visibility === "draft" ? <button type="button" className={primaryButton} onClick={onSave} disabled={busy || !canSave}>{editor.item?.state === "published" && editor.visibility === "draft" ? "Move to draft" : "Save changes"}</button> : <button type="button" className={primaryButton} onClick={onPublish} disabled={busy || !canPublish}><Send className="size-4" />Publish now</button>}</div></section>
        <section className="border border-slate-200 bg-white p-4 shadow-sm"><div className="flex items-center justify-between gap-2"><h3 className="text-sm font-semibold">Slug</h3><button type="button" title="Regenerate slug" aria-label="Regenerate slug" onClick={onRegenerate} className="rounded p-1.5 text-slate-500 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-600"><RefreshCw className="size-4" /></button></div><div className="mt-3 flex items-center rounded-md border border-slate-300 focus-within:border-sky-600 focus-within:ring-2 focus-within:ring-sky-100"><span className="pl-3 text-sm text-slate-400">/</span><input aria-label="Slug" className="min-h-10 min-w-0 flex-1 border-0 bg-transparent px-1 py-2 text-sm outline-none" value={editor.slug} onChange={event => onSlug(event.target.value)} maxLength={120} /></div>{editor.errors.slug && <p className="mt-2 text-sm text-red-700" role="alert">{editor.errors.slug}</p>}</section>
        <FeaturedImagePanel value={editor.featuredImage} error={editor.errors.featuredImage} disabled={busy} onChange={onFeaturedImage} />
        <section className="border border-slate-200 bg-white p-4 shadow-sm"><h3 className="text-sm font-semibold">Labels / tags</h3><p className="mt-1 text-xs leading-5 text-slate-500">Comma-separated labels. Up to 20 labels, 40 characters each.</p><label className="mt-3 grid gap-1.5 text-xs font-medium">Labels<input className={fieldClass} value={editor.labels} onChange={event => onLabels(event.target.value)} maxLength={820} placeholder="news, release, guide" /></label>{editor.errors.labels && <p className="mt-2 text-sm text-red-700" role="alert">{editor.errors.labels}</p>}</section>
        {editor.item && <ContentSeoPanel contentId={editor.item.id} />}
        {editor.item && capabilities.delete && <button type="button" className="inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-md border border-red-300 bg-white px-3 text-sm font-semibold text-red-700 hover:bg-red-50" onClick={() => { const item = editor.item; if (item) onAction("delete", item); }} disabled={busy}><Trash2 className="size-4" />Delete {singular}</button>}
      </aside>
    </div></div>
    <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 bg-white px-4 py-3 sm:px-6"><div><button type="button" className={secondaryButton} onClick={onPreview} disabled={busy}><Eye className="size-4" />Preview</button><span className="ml-3 text-xs text-slate-500" role="status">{autosaveStatus}</span></div><div className="flex gap-2">{editor.item?.state === "published" || editor.visibility === "draft" ? <button type="button" className={primaryButton} onClick={onSave} disabled={busy || !canSave}>{editor.item?.state === "published" && editor.visibility === "draft" ? "Move to draft" : "Save changes"}</button> : <button type="button" className={primaryButton} onClick={onPublish} disabled={busy || !canPublish}><Send className="size-4" />Publish now</button>}</div></footer>
  </section></div>;
}

function FeaturedImagePanel({ value, error, disabled, onChange }: { value: string; error?: string; disabled: boolean; onChange: (value: string) => void }) {
  const { notify } = useToast(); const [uploading, setUploading] = useState(false);
  async function upload(file: File | undefined) {
    if (!file) return; setUploading(true);
    try { onChange(await uploadAdminImage(file)); notify("Featured image uploaded and attached."); }
    catch (reason) { notify(reason instanceof Error ? reason.message : "Featured image upload failed.", "error"); }
    finally { setUploading(false); }
  }
  return <section className="border border-slate-200 bg-white p-4 shadow-sm"><h3 className="text-sm font-semibold">Featured image</h3><p className="mt-1 text-xs leading-5 text-slate-500">Paste an HTTP/HTTPS URL or upload PNG, JPEG or WebP from this device (maximum 4 MB).</p><label className="mt-3 grid gap-1.5 text-xs font-medium">Image URL<input className={fieldClass} value={value} onChange={event => onChange(event.target.value)} maxLength={1000} placeholder="https://example.com/cover.jpg" /></label><div className="my-3 flex items-center gap-2 text-[11px] text-slate-400"><span className="h-px flex-1 bg-slate-200" />OR<span className="h-px flex-1 bg-slate-200" /></div><label className="grid gap-1.5 text-xs font-medium">Upload from PC/mobile<input type="file" accept="image/png,image/jpeg,image/webp" className={fieldClass} disabled={disabled || uploading} onChange={event => void upload(event.target.files?.[0])} /></label>{uploading && <p className="mt-2 text-xs text-sky-700" role="status">Uploading image…</p>}{value && validFeaturedImage(value) && <div role="img" aria-label="Featured image preview" className="mt-3 aspect-video w-full rounded-md border border-slate-200 bg-cover bg-center" style={{ backgroundImage: `url(${JSON.stringify(value)})` }} />}{error && <p className="mt-2 text-sm text-red-700" role="alert">{error}</p>}</section>;
}

type SeoMetadata = { title: string; description: string; canonical_path: string; robots: string; open_graph_title: string; open_graph_description: string; open_graph_image: string };
const emptySeo: SeoMetadata = { title: "", description: "", canonical_path: "", robots: "index,follow", open_graph_title: "", open_graph_description: "", open_graph_image: "" };

function ContentSeoPanel({ contentId }: { contentId: string }) {
  const { notify } = useToast();
  const [metadata, setMetadata] = useState<SeoMetadata | null>(null);
  const [saving, setSaving] = useState(false);
  useEffect(() => {
    let active = true;
    adminRequest<{ metadata: SeoMetadata }>(`/admin/manage/transport/content-seo?content_id=${encodeURIComponent(contentId)}`)
      .then(result => { if (active) setMetadata({ ...emptySeo, ...result.metadata }); })
      .catch(() => { if (active) setMetadata(null); });
    return () => { active = false; };
  }, [contentId]);
  if (!metadata) return null;
  const field = (key: keyof SeoMetadata, label: string, maxLength: number, placeholder = "") => <label className="grid gap-1.5 text-xs font-medium text-slate-700">{label}<input className={fieldClass} value={metadata[key]} maxLength={maxLength} placeholder={placeholder} onChange={event => setMetadata({ ...metadata, [key]: event.target.value })} /></label>;
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSaving(true);
    try {
      const result = await adminRequest<{ metadata: SeoMetadata }>("/admin/manage/transport/content-seo", { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify({ content_id: contentId, metadata }) });
      setMetadata({ ...emptySeo, ...result.metadata }); notify("Content SEO metadata saved.");
    } catch (reason) { notify(reason instanceof Error ? reason.message : "Content SEO metadata could not be saved.", "error"); }
    finally { setSaving(false); }
  }
  return <form className="grid gap-3 border border-slate-200 bg-white p-4 shadow-sm" onSubmit={save}><div><h3 className="text-sm font-semibold">SEO and social tags</h3><p className="mt-1 text-xs leading-5 text-slate-500">Write a separate search description here—especially for iframe, video, gallery or other low-text pages. Leave it empty only when you want a safe summary generated from the article text.</p></div>{field("title", "SEO title", 120, "Defaults to the post/page title")}<label className="grid gap-1.5 text-xs font-medium text-slate-700">Custom meta description<textarea className={`${fieldClass} min-h-24 resize-y`} value={metadata.description} maxLength={320} placeholder="Describe this page independently from its body content" onChange={event => setMetadata({ ...metadata, description: event.target.value })} /><span className="font-normal text-slate-500">{metadata.description.length}/320 — this overrides the automatic Content summary.</span></label>{field("canonical_path", "Canonical path", 500, "/published-path")}{field("open_graph_title", "Open Graph title", 120)}{field("open_graph_description", "Open Graph description", 320)}{field("open_graph_image", "Open Graph image path", 500, "/media/reference")}<label className="grid gap-1.5 text-xs font-medium text-slate-700">Robots tag<select className={fieldClass} value={metadata.robots} onChange={event => setMetadata({ ...metadata, robots: event.target.value })}><option value="index,follow">Index and follow</option><option value="noindex,nofollow">No index and no follow</option></select></label><button type="submit" className={primaryButton} disabled={saving}>{saving ? "Saving SEO" : "Save SEO metadata"}</button></form>;
}

function PreviewDialog({ preview, onClose }: { preview: ContentPreview; onClose: () => void }) { return <div className="fixed inset-0 z-[70] bg-slate-950/60 p-0 sm:p-4" role="presentation"><section role="dialog" aria-modal="true" aria-labelledby="preview-title" className="mx-auto flex h-full max-w-6xl flex-col bg-white shadow-2xl sm:rounded-md"><header className="flex min-h-16 items-center justify-between border-b border-slate-200 px-4 sm:px-6"><div><p className="text-xs font-semibold uppercase text-sky-700">Sanitized preview</p><h2 id="preview-title" className="font-semibold">{preview.title}</h2></div><button type="button" title="Close preview" aria-label="Close preview" onClick={onClose} className="rounded p-2 text-slate-500 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-600"><X className="size-5" /></button></header><div className="min-h-0 flex-1 overflow-y-auto bg-slate-50"><div className="public-preview mx-auto bg-white" dangerouslySetInnerHTML={{ __html: preview.html }} /></div></section></div>; }
