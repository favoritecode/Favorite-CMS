import { redirect } from "next/navigation";

export default function LegacyManagementPage() {
  redirect("/admin/pages");
}
