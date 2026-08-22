"use client";

import { type FormEvent, useCallback, useEffect, useState } from "react";
import { Plus, RefreshCw, Save, Trash2, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { adminRequest, isAuthenticationError } from "@/lib/admin-client";
import type { DomainApplication, DomainField, DomainRecord } from "@/lib/admin-types";
import { EmptyState, ErrorPanel, fieldClass, LoadingPanel, primaryButton, secondaryButton, useToast } from "./admin-ui";

export function ApplicationsSection() {
  const router = useRouter(); const { notify } = useToast();
  const [applications, setApplications] = useState<DomainApplication[]>([]); const [selected, setSelected] = useState("");
  const [editing, setEditing] = useState<DomainRecord | "new" | null>(null); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  const load = useCallback(async () => {
    setLoading(true); setError("");
    try { const result = await adminRequest<DomainApplication[]>("/admin/manage/transport/applications"); setApplications(result); setSelected(current => current || key(result[0])); }
    catch (reason) { if (isAuthenticationError(reason)) { router.replace("/admin/login"); return; } setError(reason instanceof Error ? reason.message : "Applications could not be loaded."); }
    finally { setLoading(false); }
  }, [router]);
  useEffect(() => { void load(); }, [load]);
  const application = applications.find(item => key(item) === selected);
  async function remove(record: DomainRecord) {
    if (!application || !window.confirm("Delete this Plugin-owned record? This action cannot be undone.")) return;
    try { await adminRequest("/admin/manage/transport/applications", { method: "DELETE", headers: { "content-type": "application/json" }, body: JSON.stringify({ owner: application.owner, entity: application.entity, id: record.id }) }); notify("Application record deleted."); await load(); }
    catch (reason) { notify(reason instanceof Error ? reason.message : "Record could not be deleted.", "error"); }
  }
  if (loading && applications.length === 0) return <LoadingPanel label="Loading Plugin applications" />;
  if (error) return <ErrorPanel message={error} onRetry={() => void load()} />;
  if (applications.length === 0) return <EmptyState title="No accessible Plugin applications" detail="Activate a declarative Domain Plugin and explicitly assign its record permissions to a role." />;
  return <div className="grid gap-5 lg:grid-cols-[17rem_1fr]">
    <aside className="border border-slate-200 bg-white p-3 shadow-sm"><h2 className="px-2 py-2 font-semibold">Plugin applications</h2>{applications.map(item => <button key={key(item)} type="button" onClick={() => { setSelected(key(item)); setEditing(null); }} className={`mt-1 w-full rounded-md p-3 text-left ${selected === key(item) ? "bg-sky-50 text-sky-950" : "hover:bg-slate-50"}`}><strong className="block text-sm">{item.label}</strong><span className="block truncate font-mono text-[11px] text-slate-500">{item.owner} · {item.entity}</span></button>)}</aside>
    {application && <section className="min-w-0"><div className="mb-3 flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-lg font-semibold">{application.label}</h2><p className="text-sm text-slate-500">{application.records.length} records · schema owned by {application.owner}</p></div><div className="flex gap-2"><button type="button" className={secondaryButton} onClick={() => void load()}><RefreshCw className="size-4" />Refresh</button><button type="button" className={primaryButton} onClick={() => setEditing("new")}><Plus className="size-4" />Add record</button></div></div>
      {application.records.length === 0 ? <EmptyState title={`No ${application.label.toLowerCase()} yet`} detail="Create the first record using the active Plugin's validated field schema." /> : <div className="overflow-x-auto border border-slate-200 bg-white"><table className="w-full text-left text-sm"><thead className="bg-slate-50"><tr>{application.fields.slice(0, 4).map(field => <th key={field.id} className="p-3 font-semibold">{label(field.id)}</th>)}<th className="p-3 text-right">Actions</th></tr></thead><tbody>{application.records.map(record => <tr key={record.id} className="border-t border-slate-200">{application.fields.slice(0, 4).map(field => <td key={field.id} className="max-w-64 truncate p-3">{display(record.values[field.id])}</td>)}<td className="p-3"><div className="flex justify-end gap-2"><button className={secondaryButton} onClick={() => setEditing(record)}>Edit</button><button className={secondaryButton} onClick={() => void remove(record)}><Trash2 className="size-4" />Delete</button></div></td></tr>)}</tbody></table></div>}
    </section>}
    {application && editing && <RecordDialog application={application} record={editing === "new" ? null : editing} onClose={() => setEditing(null)} onSaved={async () => { setEditing(null); await load(); }} />}
  </div>;
}

function RecordDialog({ application, record, onClose, onSaved }: { application: DomainApplication; record: DomainRecord | null; onClose: () => void; onSaved: () => Promise<void> }) {
  const { notify } = useToast(); const [values, setValues] = useState<Record<string, unknown>>(record?.values ?? {}); const [saving, setSaving] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault(); setSaving(true);
    try { await adminRequest("/admin/manage/transport/applications", { method: record ? "PATCH" : "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ owner: application.owner, entity: application.entity, ...(record ? { id: record.id } : {}), values }) }); notify(record ? "Application record updated." : "Application record created."); await onSaved(); }
    catch (reason) { notify(reason instanceof Error ? reason.message : "Record could not be saved.", "error"); }
    finally { setSaving(false); }
  }
  return <div className="fixed inset-0 z-[70] bg-slate-950/45 p-0 sm:p-4"><section className="ml-auto flex h-full w-full max-w-2xl flex-col bg-white shadow-2xl sm:rounded-md" role="dialog" aria-modal="true" aria-labelledby="record-title"><header className="flex items-center justify-between border-b border-slate-200 px-5 py-4"><div><p className="text-xs font-semibold uppercase text-sky-700">{application.label}</p><h2 id="record-title" className="font-semibold">{record ? "Edit record" : "Add record"}</h2></div><button type="button" aria-label="Close" className="rounded p-2 hover:bg-slate-100" onClick={onClose}><X className="size-5" /></button></header><form onSubmit={submit} className="flex min-h-0 flex-1 flex-col"><div className="grid flex-1 gap-5 overflow-y-auto p-5">{application.fields.map(field => <RecordField key={field.id} field={field} value={values[field.id]} onChange={value => setValues(current => ({ ...current, [field.id]: value }))} />)}</div><footer className="flex justify-end gap-2 border-t border-slate-200 bg-slate-50 p-4"><button type="button" className={secondaryButton} onClick={onClose}>Cancel</button><button type="submit" className={primaryButton} disabled={saving}><Save className="size-4" />{saving ? "Saving" : "Save record"}</button></footer></form></section></div>;
}

function RecordField({ field, value, onChange }: { field: DomainField; value: unknown; onChange: (value: unknown) => void }) {
  const common = { required: field.required, name: field.id };
  if (field.type === "boolean") return <label className="flex items-center gap-3 text-sm font-medium"><input type="checkbox" checked={Boolean(value)} onChange={event => onChange(event.target.checked)} />{label(field.id)}</label>;
  if (field.type === "enum") return <label className="grid gap-2 text-sm font-medium">{label(field.id)}<select className={fieldClass} value={String(value ?? "")} onChange={event => onChange(event.target.value)} {...common}><option value="">Select</option>{field.choices.map(choice => <option key={choice}>{choice}</option>)}</select></label>;
  if (field.type === "text") return <label className="grid gap-2 text-sm font-medium">{label(field.id)}<textarea className={`${fieldClass} min-h-32`} maxLength={field.max_length ?? undefined} value={String(value ?? "")} onChange={event => onChange(event.target.value)} {...common} /></label>;
  return <label className="grid gap-2 text-sm font-medium">{label(field.id)}<input className={fieldClass} type={field.type === "integer" || field.type === "decimal" ? "number" : "text"} step={field.type === "decimal" ? "any" : undefined} maxLength={field.max_length ?? undefined} value={String(value ?? "")} onChange={event => onChange(field.type === "integer" ? Number(event.target.value) : event.target.value)} {...common} /><span className="text-xs font-normal text-slate-500">{field.type === "media" ? "Enter an approved Media ID." : field.type === "relation" ? "Enter a related record ID." : `${field.type} field`}</span></label>;
}
function key(value?: DomainApplication) { return value ? `${value.owner}:${value.entity}` : ""; }
function label(value: string) { return value.replaceAll("_", " ").replace(/\b\w/g, letter => letter.toUpperCase()); }
function display(value: unknown) { return value === undefined ? "—" : typeof value === "boolean" ? (value ? "Yes" : "No") : String(value); }
