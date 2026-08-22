"use client";

import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Activity, Blocks, ChevronDown, Files, Gauge, Image as ImageIcon, LockKeyhole, LogOut, Menu, Navigation, Newspaper, Palette, Settings, ShieldCheck, UserRound, Users, X } from "lucide-react";
import { adminRequest, isAuthenticationError } from "@/lib/admin-client";
import type { AdminModule, AdminSection } from "@/lib/admin-types";
import { ToastProvider } from "./admin-ui";

type NavigationItem = { id: AdminSection; label: string; href: string; icon: typeof Gauge; module?: string };
const navigation: { label: string; items: NavigationItem[] }[] = [
  { label: "Dashboard", items: [{ id: "dashboard", label: "Dashboard", href: "/admin", icon: Gauge }] },
  { label: "Content", items: [
    { id: "posts", label: "Posts", href: "/admin/posts", icon: Newspaper, module: "admin.content" },
    { id: "pages", label: "Pages", href: "/admin/pages", icon: Files, module: "admin.content" },
    { id: "media", label: "Media", href: "/admin/media", icon: ImageIcon, module: "admin.media" },
  ] },
  { label: "Appearance", items: [
    { id: "themes", label: "Themes", href: "/admin/themes", icon: Palette, module: "admin.extensions" },
    { id: "menus", label: "Menus", href: "/admin/menus", icon: Navigation, module: "admin.menus" },
  ] },
  { label: "Extensions", items: [
    { id: "plugins", label: "Plugins", href: "/admin/plugins", icon: Blocks, module: "admin.extensions" },
  ] },
  { label: "System", items: [
    { id: "users", label: "Users", href: "/admin/users", icon: Users, module: "admin.users" },
    { id: "roles", label: "Roles & permissions", href: "/admin/roles", icon: ShieldCheck, module: "admin.roles" },
    { id: "settings", label: "Settings", href: "/admin/settings", icon: Settings, module: "admin.settings" },
    { id: "diagnostics", label: "Diagnostics", href: "/admin/diagnostics", icon: Activity, module: "admin.diagnostics" },
  ] },
];

export function AdminFrame({ section, title, description, actions, children }: {
  section: AdminSection; title: string; description?: string; actions?: ReactNode; children: ReactNode;
}) {
  const router = useRouter();
  const [modules, setModules] = useState<AdminModule[]>([]);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  const [signingOut, setSigningOut] = useState(false);

  useEffect(() => {
    let active = true;
    adminRequest<AdminModule[]>("/admin/modules")
      .then(value => { if (active) setModules(value); })
      .catch(error => { if (isAuthenticationError(error)) router.replace("/admin/login"); });
    return () => { active = false; };
  }, [router]);

  useEffect(() => setMobileOpen(false), [section]);
  const availableModules = useMemo(() => new Set(modules.map(module => module.id)), [modules]);
  const declaredModules = useMemo(() => new Set(navigation.flatMap(group => group.items.flatMap(item => item.module ? [item.module] : []))), []);
  const contributedModules = useMemo(() => modules.filter(module => !declaredModules.has(module.id)), [declaredModules, modules]);

  async function signOut() {
    setSigningOut(true);
    try { await fetch("/admin/session", { method: "DELETE" }); }
    finally { router.replace("/admin/login"); router.refresh(); }
  }

  const nav = <nav aria-label="Administration" className="flex flex-1 flex-col gap-5 overflow-y-auto px-3 py-4">
    {navigation.map(group => <div key={group.label}>
      <p className="mb-1.5 px-3 text-[11px] font-semibold uppercase text-slate-500">{group.label}</p>
      <div className="space-y-1">{group.items.filter(item => item.module === undefined || availableModules.has(item.module)).map(item => {
        const Icon = item.icon;
        const current = section === item.id;
        return <Link key={item.id} href={item.href} aria-current={current ? "page" : undefined} className={`flex min-h-10 items-center gap-3 rounded-md px-3 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-sky-400 ${current ? "bg-white text-slate-950 shadow-sm" : "text-slate-300 hover:bg-slate-800 hover:text-white"}`}>
          <Icon className="size-[18px] shrink-0" /><span className="min-w-0 flex-1 truncate">{item.label}</span>
        </Link>;
      })}</div>
    </div>)}
    {contributedModules.length > 0 && <div>
      <p className="mb-1.5 px-3 text-[11px] font-semibold uppercase text-slate-500">Modules</p>
      <div className="space-y-1">{contributedModules.map(module => <Link key={module.id} href={module.destination} className="flex min-h-10 items-center gap-3 rounded-md px-3 text-sm font-medium text-slate-300 hover:bg-slate-800 hover:text-white focus:outline-none focus:ring-2 focus:ring-sky-400">
        <LockKeyhole className="size-[18px] shrink-0" /><span className="min-w-0 flex-1 truncate">{module.label}</span>
      </Link>)}</div>
    </div>}
  </nav>;

  return <ToastProvider><div className="min-h-screen bg-slate-100 text-slate-950">
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 flex-col bg-slate-950 md:flex">
      <Link href="/admin" className="flex h-16 items-center gap-3 border-b border-slate-800 px-5 text-white focus:outline-none focus:ring-2 focus:ring-inset focus:ring-sky-400">
        <span className="grid size-9 place-items-center rounded-md bg-sky-500 text-sm font-black text-slate-950">F</span>
        <span><strong className="block text-sm">Favorite CMS</strong><span className="block text-xs text-slate-400">Administration</span></span>
      </Link>
      {nav}
      <div className="border-t border-slate-800 p-4 text-xs text-slate-500">Favorite CMS 0.1.0</div>
    </aside>

    {mobileOpen && <div className="fixed inset-0 z-50 md:hidden">
      <button type="button" aria-label="Close navigation" className="absolute inset-0 bg-slate-950/50" onClick={() => setMobileOpen(false)} />
      <aside className="relative flex h-full w-[min(19rem,85vw)] flex-col bg-slate-950 shadow-2xl">
        <div className="flex h-16 items-center justify-between border-b border-slate-800 px-4 text-white"><strong>Favorite CMS</strong><button type="button" title="Close menu" aria-label="Close menu" onClick={() => setMobileOpen(false)} className="rounded-md p-2 hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-400"><X className="size-5" /></button></div>
        {nav}
      </aside>
    </div>}

    <div className="md:pl-64">
      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="flex min-h-16 items-center gap-3 px-4 sm:px-6 lg:px-8">
          <button type="button" title="Open menu" aria-label="Open menu" onClick={() => setMobileOpen(true)} className="rounded-md border border-slate-300 p-2 text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-sky-600 md:hidden"><Menu className="size-5" /></button>
          <div className="min-w-0 flex-1"><p className="truncate text-xs font-medium text-slate-500">Administration <span aria-hidden="true">/</span> <span className="text-slate-700">{title}</span></p></div>
          <div className="relative">
            <button type="button" aria-label="Account" aria-haspopup="menu" aria-expanded={accountOpen} onClick={() => setAccountOpen(value => !value)} className="flex min-h-10 items-center gap-2 rounded-md border border-slate-300 bg-white px-3 text-sm font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-sky-600">
              <UserRound className="size-4" /><span className="hidden sm:inline">Account</span><ChevronDown className="size-4" />
            </button>
            {accountOpen && <div role="menu" className="absolute right-0 mt-2 w-56 rounded-md border border-slate-200 bg-white p-1.5 shadow-xl">
              <div className="border-b border-slate-100 px-3 py-2"><p className="text-sm font-medium">Authenticated session</p><p className="text-xs text-slate-500">Permissions are role-managed</p></div>
              <button type="button" role="menuitem" onClick={signOut} disabled={signingOut} className="mt-1 flex min-h-10 w-full items-center gap-2 rounded-md px-3 text-sm font-medium text-red-700 hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-600 disabled:opacity-50"><LogOut className="size-4" />{signingOut ? "Signing out" : "Sign out"}</button>
            </div>}
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-[94rem] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div><h1 className="text-2xl font-semibold text-slate-950">{title}</h1>{description && <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-600">{description}</p>}</div>
          {actions && <div className="flex shrink-0 flex-wrap gap-2">{actions}</div>}
        </div>
        {children}
      </main>
    </div>
  </div></ToastProvider>;
}
