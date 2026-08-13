"use client";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export function LoginForm() {
  const router = useRouter(); const [error, setError] = useState(""); const [loading, setLoading] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setLoading(true);
    const form = new FormData(event.currentTarget);
    try {
      const response = await fetch("/admin/session", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ email: form.get("email"), password: form.get("password") }) });
      const payload = await response.json();
      if (!response.ok) { setError(typeof payload.error === "string" ? payload.error : "Authentication failed."); return; }
      router.replace("/admin"); router.refresh();
    } catch { setError("The service is unavailable."); } finally { setLoading(false); }
  }
  return <form onSubmit={submit} className="mt-8 space-y-5" noValidate>
    <div><label htmlFor="email" className="block text-sm font-medium">Email</label><input id="email" name="email" type="email" autoComplete="username" required maxLength={320} className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-950" /></div>
    <div><label htmlFor="password" className="block text-sm font-medium">Password</label><input id="password" name="password" type="password" autoComplete="current-password" required maxLength={512} className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-950" /></div>
    {error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-800">{error}</p>}
    <button disabled={loading} className="w-full rounded-lg bg-sky-700 px-4 py-2.5 font-semibold text-white disabled:opacity-60">{loading ? "Signing in…" : "Sign in"}</button>
  </form>;
}
