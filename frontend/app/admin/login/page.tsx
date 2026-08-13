import { LoginForm } from "./login-form";
export default function AdminLogin() {
  return <main className="grid min-h-screen place-items-center bg-slate-100 px-6"><section className="w-full max-w-md rounded-2xl bg-white p-8 shadow-sm" aria-labelledby="login-title"><p className="text-sm font-semibold uppercase tracking-wider text-sky-700">Favorite CMS</p><h1 id="login-title" className="mt-2 text-3xl font-bold text-slate-950">Admin sign in</h1><p className="mt-2 text-slate-600">Use your existing Favorite CMS account.</p><LoginForm /></section></main>;
}
