"use client";

import { AlertCircle } from "lucide-react";
import { AdminFrame } from "@/components/admin/admin-frame";
import { ContentSection } from "@/components/admin/content-section";
import { DiagnosticsSection } from "@/components/admin/diagnostics-section";
import { ExtensionsSection } from "@/components/admin/extensions-section";
import { MediaSection } from "@/components/admin/media-section";
import { SettingsSection } from "@/components/admin/settings-section";
import { UsersSection, RolesSection } from "@/components/admin/administration-section";
import { ApplicationsSection } from "@/components/admin/applications-section";
import type { AdminSection } from "@/lib/admin-types";

const details: Record<Exclude<AdminSection, "dashboard">, { title: string; description: string }> = {
  posts: { title: "Posts", description: "Write, review, publish, archive, and manage post content." },
  pages: { title: "Pages", description: "Manage the structured pages presented by your public site." },
  media: { title: "Media", description: "Manage bounded text documents through the existing Media and Storage contracts." },
  themes: { title: "Themes", description: "Review installed themes and safely change the active public presentation." },
  menus: { title: "Menus", description: "Navigation structures and presentation assignments." },
  plugins: { title: "Plugins", description: "Manage plugin lifecycle, declared capabilities, dependencies, and owned settings." },
  applications: { title: "Applications", description: "Manage records owned by active declarative Domain Plugins through their registered schemas." },
  users: { title: "Users", description: "Accounts, roles, and status under the explicit identity permission model." },
  roles: { title: "Roles & permissions", description: "Manage transparent role membership and explicit PermissionEngine grants." },
  settings: { title: "Settings", description: "Update platform-owned site settings without exposing infrastructure configuration." },
  diagnostics: { title: "Diagnostics", description: "Authorized, redacted operational health across Favorite CMS engines and providers." },
};

export function ManagementConsole({ section }: { section: Exclude<AdminSection, "dashboard"> }) {
  const current = details[section];
  return <AdminFrame section={section} title={current.title} description={current.description}>
    {section === "posts" && <ContentSection contentType="post" />}
    {section === "pages" && <ContentSection contentType="page" />}
    {section === "media" && <MediaSection />}
    {section === "themes" && <ExtensionsSection kind="theme" />}
    {section === "menus" && <MissingContract title="Menu administration is not exposed yet" detail="MenuEngine supports internal menu, location, assignment, and item operations, but the backend does not provide an authorized Admin API or listing contract. No menu data has been fabricated." />}
    {section === "plugins" && <ExtensionsSection kind="plugin" />}
    {section === "applications" && <ApplicationsSection />}
    {section === "users" && <UsersSection />}
    {section === "roles" && <RolesSection />}
    {section === "settings" && <SettingsSection />}
    {section === "diagnostics" && <DiagnosticsSection />}
  </AdminFrame>;
}

function MissingContract({ title, detail }: { title: string; detail: string }) {
  return <section role="status" className="border border-slate-200 bg-white p-6 shadow-sm"><div className="flex max-w-3xl items-start gap-4"><span className="grid size-10 shrink-0 place-items-center rounded-md bg-amber-50 text-amber-700"><AlertCircle className="size-5" /></span><div><h2 className="font-semibold text-slate-950">{title}</h2><p className="mt-2 text-sm leading-6 text-slate-600">{detail}</p></div></div></section>;
}
