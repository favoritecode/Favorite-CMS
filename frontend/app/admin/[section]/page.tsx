import { notFound } from "next/navigation";
import { ManagementConsole } from "../manage/management-console";
import type { AdminSection } from "@/lib/admin-types";

type ManagedSection = Exclude<AdminSection, "dashboard">;
const adminSections: ManagedSection[] = ["posts", "pages", "media", "themes", "menus", "plugins", "users", "settings", "diagnostics"];

export default async function AdminSectionPage({ params }: { params: Promise<{ section: string }> }) {
  const { section } = await params;
  if (!adminSections.includes(section as ManagedSection)) notFound();
  return <ManagementConsole section={section as ManagedSection} />;
}
