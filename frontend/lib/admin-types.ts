export type AdminSection = "dashboard" | "posts" | "pages" | "media" | "themes" | "menus" | "plugins" | "users" | "roles" | "settings" | "diagnostics";

export type AdminModule = {
  id: string;
  label: string;
  destination: string;
  owner: string;
};

export type ContentItem = {
  id: string;
  type: string;
  title: string;
  data: { slug?: string; body?: string; featured_image?: string; labels?: string[]; visibility?: "public" | "unlisted" | "private" };
  state: "draft" | "published" | "archived" | string;
  visibility?: "public" | "unlisted" | "private";
};

export type ContentCapabilities = {
  create: boolean;
  read: boolean;
  update: boolean;
  delete: boolean;
  publish: boolean;
  archive: boolean;
};

export type ContentPreview = {
  title: string;
  data: { slug: string; body: string; featured_image?: string; labels?: string[]; visibility?: string };
  html: string;
};

export type MediaItem = {
  id: string;
  name: string;
  mime_type: string;
  type: string;
  size: number;
  metadata: Record<string, unknown>;
  public?: boolean;
};

export type ExtensionItem = {
  id: string;
  name: string;
  version: string;
  description: string;
  author: string;
  type: "theme" | "plugin";
  state: string;
  failure: string | null;
  compatible: boolean;
  active: boolean;
  dependencies: Record<string, string>;
  optional_dependencies: Record<string, string>;
  permissions: string[];
  granted_permissions: string[];
  package_managed: boolean;
};

export type UserItem = { id: string; email: string; display_name: string; state: string; roles: string[]; permissions: string[] };
export type RoleItem = { id: string; name: string; built_in: boolean; permissions: string[]; users: number };
export type PermissionItem = { id: string; owner: string; action: string; resource_type: string; group: string };
export type RoleAdministration = { roles: RoleItem[]; permissions: PermissionItem[] };

export type Operations = {
  version: string;
  status: string;
  components: { name: string; status: string; critical: boolean; message: string }[];
  configuration: {
    database: string;
    database_provider: string;
    storage: string;
    storage_provider: string;
    authentication: string;
    active_theme: string;
  };
  migration: { status: string; applied: number | null; pending: number | null; mode: string };
  installation: { status: string; automatic_install?: boolean; automatic_migration?: boolean };
  update: { status: string; mode?: string; remote_updates?: boolean };
  recovery: { status: string; mode?: string; backup_count?: number; native_postgresql_restore?: boolean };
  notification: { status: string; provider_configured?: boolean; pending?: number; failed?: number };
  queue: { status: string };
  scheduler: { status: string };
  content: { status: string; seo_projection: boolean };
  media: { status: string; supported: string };
  theme: { status: string; active: string | null };
};

export type Diagnostics = {
  liveness: { status: string; live: boolean };
  readiness: { status: string; ready: boolean };
  operations: Operations;
};

export type Dashboard = {
  areas: string[];
  content?: { count: number | null; draft?: number; published?: number; archived?: number };
  media?: { count: number | null };
  extensions?: { installed: number; active_plugins: number; active_theme: string | null };
  health?: Diagnostics;
};
