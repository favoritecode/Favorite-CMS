"use client";

import { type FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { LoaderCircle, LogIn } from "lucide-react";
import { fieldClass, primaryButton } from "@/components/admin/admin-ui";
import { parseJsonSafely } from "@/lib/admin-client";

export function LoginForm() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setLoading(true);
    const form = new FormData(event.currentTarget);
    try {
      const response = await fetch("/admin/session", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ email: form.get("email"), password: form.get("password") }) });
      const payload = await parseJsonSafely(response);
      if (!response.ok) {
        const message = typeof payload === "object" && payload !== null && "error" in payload && typeof payload.error === "string"
          ? payload.error
          : response.status === 403 ? "This account is not authorized to use Admin."
            : response.status === 503 ? "The service is unavailable."
              : response.status >= 500 ? "The Admin service encountered an error." : "Authentication failed.";
        setError(message); return;
      }
      router.replace("/admin"); router.refresh();
    } catch { setError("The service is unavailable."); }
    finally { setLoading(false); }
  }

  return <form onSubmit={submit} className="mt-7 space-y-5" noValidate>
    <div><label htmlFor="email" className="block text-sm font-medium text-slate-700">Email address</label><input id="email" name="email" type="email" autoComplete="username" required maxLength={320} className={`${fieldClass} mt-2`} placeholder="you@example.com" /></div>
    <div><label htmlFor="password" className="block text-sm font-medium text-slate-700">Password</label><input id="password" name="password" type="password" autoComplete="current-password" required maxLength={512} className={`${fieldClass} mt-2`} /></div>
    {error && <p role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</p>}
    <button disabled={loading} className={`${primaryButton} w-full`}>{loading ? <LoaderCircle className="size-4 animate-spin" /> : <LogIn className="size-4" />}{loading ? "Signing in" : "Sign in"}</button>
  </form>;
}
