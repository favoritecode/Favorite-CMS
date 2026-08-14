"use client";

import { createContext, type ReactNode, useCallback, useContext, useEffect, useState } from "react";
import { AlertCircle, CheckCircle2, Inbox, LoaderCircle, X } from "lucide-react";

type Toast = { id: number; message: string; tone: "success" | "error" };
type ToastContextValue = { notify: (message: string, tone?: Toast["tone"]) => void };

const ToastContext = createContext<ToastContextValue | null>(null);

export const primaryButton = "inline-flex min-h-10 items-center justify-center gap-2 rounded-md bg-slate-900 px-3.5 py-2 text-sm font-semibold text-white transition-colors hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-600 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50";
export const secondaryButton = "inline-flex min-h-10 items-center justify-center gap-2 rounded-md border border-slate-300 bg-white px-3.5 py-2 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-sky-600 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50";
export const dangerButton = "inline-flex min-h-10 items-center justify-center gap-2 rounded-md border border-red-300 bg-white px-3.5 py-2 text-sm font-semibold text-red-700 transition-colors hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-600 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50";
export const fieldClass = "min-h-10 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-950 outline-none transition-shadow placeholder:text-slate-400 focus:border-sky-600 focus:ring-2 focus:ring-sky-100 disabled:cursor-not-allowed disabled:bg-slate-100";

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const notify = useCallback((message: string, tone: Toast["tone"] = "success") => {
    const id = Date.now() + Math.random();
    setToasts(current => [...current, { id, message, tone }]);
    window.setTimeout(() => setToasts(current => current.filter(toast => toast.id !== id)), 4500);
  }, []);

  return <ToastContext.Provider value={{ notify }}>
    {children}
    <div className="fixed bottom-4 right-4 z-[80] flex w-[min(24rem,calc(100vw-2rem))] flex-col gap-2" aria-live="polite" aria-atomic="true">
      {toasts.map(toast => <div key={toast.id} className={`flex items-start gap-3 rounded-md border px-4 py-3 shadow-lg ${toast.tone === "success" ? "border-emerald-200 bg-emerald-50 text-emerald-950" : "border-red-200 bg-red-50 text-red-950"}`}>
        {toast.tone === "success" ? <CheckCircle2 className="mt-0.5 size-5 shrink-0" /> : <AlertCircle className="mt-0.5 size-5 shrink-0" />}
        <p className="flex-1 text-sm font-medium">{toast.message}</p>
        <button type="button" aria-label="Dismiss notification" title="Dismiss" onClick={() => setToasts(current => current.filter(item => item.id !== toast.id))} className="rounded p-0.5 hover:bg-black/5 focus:outline-none focus:ring-2 focus:ring-current"><X className="size-4" /></button>
      </div>)}
    </div>
  </ToastContext.Provider>;
}

export function useToast() {
  const value = useContext(ToastContext);
  if (!value) throw new Error("useToast must be used inside ToastProvider");
  return value;
}

export function StatusBadge({ value }: { value: string }) {
  const normalized = value.toLowerCase();
  const tone = ["healthy", "published", "enabled", "active", "ready", "configured"].includes(normalized)
    ? "bg-emerald-50 text-emerald-800 ring-emerald-200"
    : ["degraded", "draft", "pending", "not_configured", "installed"].includes(normalized)
      ? "bg-amber-50 text-amber-800 ring-amber-200"
      : ["unavailable", "error", "failed", "disabled", "archived", "missing"].includes(normalized)
        ? "bg-red-50 text-red-800 ring-red-200"
        : "bg-slate-100 text-slate-700 ring-slate-200";
  return <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-semibold capitalize ring-1 ring-inset ${tone}`}>{value.replaceAll("_", " ")}</span>;
}

export function LoadingPanel({ label = "Loading" }: { label?: string }) {
  return <div className="flex min-h-52 items-center justify-center gap-3 border-y border-slate-200 bg-white text-sm text-slate-600" role="status"><LoaderCircle className="size-5 animate-spin" />{label}</div>;
}

export function EmptyState({ title, detail, action }: { title: string; detail: string; action?: ReactNode }) {
  return <div className="flex min-h-52 flex-col items-center justify-center border-y border-dashed border-slate-300 bg-white px-6 text-center">
    <Inbox className="size-9 text-slate-400" />
    <h3 className="mt-4 text-base font-semibold text-slate-900">{title}</h3>
    <p className="mt-1 max-w-md text-sm text-slate-600">{detail}</p>
    {action && <div className="mt-5">{action}</div>}
  </div>;
}

export function ErrorPanel({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return <div className="flex min-h-44 flex-col items-center justify-center border-y border-red-200 bg-red-50 px-6 text-center" role="alert">
    <AlertCircle className="size-8 text-red-700" />
    <h3 className="mt-3 font-semibold text-red-950">Unable to load this area</h3>
    <p className="mt-1 max-w-xl text-sm text-red-800">{message}</p>
    {onRetry && <button type="button" onClick={onRetry} className={`${secondaryButton} mt-4`}>Try again</button>}
  </div>;
}

export function ConfirmDialog({ open, title, detail, confirmLabel, busy, tone = "danger", onCancel, onConfirm }: {
  open: boolean; title: string; detail: string; confirmLabel: string; busy?: boolean; tone?: "danger" | "primary"; onCancel: () => void; onConfirm: () => void;
}) {
  useEffect(() => {
    if (!open) return;
    const close = (event: KeyboardEvent) => { if (event.key === "Escape" && !busy) onCancel(); };
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, [busy, onCancel, open]);
  if (!open) return null;
  return <div className="fixed inset-0 z-[70] grid place-items-center bg-slate-950/45 p-4" role="presentation" onMouseDown={event => { if (event.currentTarget === event.target && !busy) onCancel(); }}>
    <div className="w-full max-w-md rounded-md bg-white p-5 shadow-2xl" role="dialog" aria-modal="true" aria-labelledby="confirm-title">
      <h2 id="confirm-title" className="text-lg font-semibold text-slate-950">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-slate-600">{detail}</p>
      <div className="mt-6 flex justify-end gap-2">
        <button type="button" className={secondaryButton} onClick={onCancel} disabled={busy} autoFocus>Cancel</button>
        <button type="button" className={tone === "danger" ? dangerButton : primaryButton} onClick={onConfirm} disabled={busy}>{busy && <LoaderCircle className="size-4 animate-spin" />}{confirmLabel}</button>
      </div>
    </div>
  </div>;
}
