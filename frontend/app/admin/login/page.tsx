import { ShieldCheck } from "lucide-react";
import { LoginForm } from "./login-form";

export default function AdminLogin() {
  return <main className="grid min-h-screen place-items-center bg-slate-100 px-4 py-10"><section className="w-full max-w-md overflow-hidden rounded-md border border-slate-200 bg-white shadow-xl" aria-labelledby="login-title"><div className="border-b border-slate-200 bg-slate-950 px-7 py-6 text-white"><div className="flex items-center gap-3"><span className="grid size-10 place-items-center rounded-md bg-sky-500 text-slate-950"><ShieldCheck className="size-5" /></span><div><p className="text-sm font-semibold">Favorite CMS</p><p className="text-xs text-slate-400">Secure administration</p></div></div></div><div className="p-7"><h1 id="login-title" className="text-2xl font-semibold text-slate-950">Sign in to Admin</h1><p className="mt-2 text-sm leading-6 text-slate-600">Use your existing Favorite CMS account to continue.</p><LoginForm /></div></section></main>;
}
