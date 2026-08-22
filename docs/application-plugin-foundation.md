# Application and isolated Tool Plugin foundation

Favorite CMS supports three deliberately different extension lanes. Presentation Plugins contribute bounded Admin/API/Rendering behavior. Domain Plugins declare data schemas that are persisted and authorized by the Domain Engine. Tool Plugins declare user input and delegate execution to an isolated, operator-configured Worker. An uploaded Plugin never becomes arbitrary Python, JavaScript, SQL, filesystem, or process execution.

## Domain Plugins

`contributions.json` schema version 1 may declare permissions and entities. Domain Engine owns persistence, validation, record identity, timestamps, and authorization. A Plugin receives only its `PluginDomains` facade and cannot operate on another Plugin's contracts.

```json
{
  "schemaVersion": 1,
  "permissions": [
    {"id": "favorite.plugin.catalog.product.create", "action": "create", "resource": "plugin_domain"},
    {"id": "favorite.plugin.catalog.product.read", "action": "read", "resource": "plugin_domain"},
    {"id": "favorite.plugin.catalog.product.update", "action": "update", "resource": "plugin_domain"},
    {"id": "favorite.plugin.catalog.product.delete", "action": "delete", "resource": "plugin_domain"}
  ],
  "entities": [{
    "id": "product",
    "label": "Products",
    "fields": [
      {"id": "name", "type": "string", "required": true, "maxLength": 120},
      {"id": "price", "type": "decimal", "required": true},
      {"id": "status", "type": "enum", "required": true, "choices": ["draft", "published"]},
      {"id": "featured_media", "type": "media"}
    ],
    "permissions": {
      "create": "favorite.plugin.catalog.product.create",
      "read": "favorite.plugin.catalog.product.read",
      "update": "favorite.plugin.catalog.product.update",
      "delete": "favorite.plugin.catalog.product.delete"
    }
  }],
  "tools": [],
  "blocks": []
}
```

Supported field kinds are `string`, `text`, `integer`, `decimal`, `boolean`, `enum`, `media`, and `relation`. Media and relation values are opaque UUID references, never physical paths. Deactivation removes active schemas and Admin access but preserves records for safe reactivation or later migration. Deletion remains an explicit authorized operation.

The Plugin manifest must declare `permission.register` and `domain.register` when those contributions are present. The administrator must explicitly approve the manifest capabilities and separately assign the Plugin's canonical record permissions to a role. Activation is not a hidden role grant.

Authorized records appear under **Admin → Extensions → Applications**. The form and table are generated from the validated schema using trusted Favorite CMS components; Plugins do not inject React or browser JavaScript.

## Isolated Tool Plugins

Tool Plugins declare inputs and a logical Worker identifier. Tool Engine owns validation, authorization, job identity, durable status, bounded results/failures, cancellation, and Worker delegation. The Plugin cannot select a URL, read a Worker token, open sockets, spawn processes, or access Storage/Database directly.

```json
{
  "schemaVersion": 1,
  "permissions": [
    {"id": "favorite.plugin.ocr.execute", "action": "execute", "resource": "plugin_tool", "allowPublic": true}
  ],
  "entities": [],
  "tools": [{
    "id": "favorite.tool.ocr",
    "label": "OCR",
    "description": "Extract text from an approved Media resource.",
    "executePermission": "favorite.plugin.ocr.execute",
    "worker": "default",
    "public": true,
    "fields": [
      {"id": "media_id", "type": "media", "required": true},
      {"id": "language", "type": "select", "required": true, "choices": ["eng", "ben"]}
    ]
  }],
  "blocks": []
}
```

Supported Tool input kinds are `text`, `url`, `media`, `integer`, `boolean`, and `select`. Input is bounded and unknown fields fail closed. URL input accepts HTTP(S) syntax but never controls the Worker destination. A specific Worker must implement its own source-domain allowlist, redirect policy, download bounds, copyright/provider rules, and Media import contract.

The Plugin manifest must explicitly declare `permission.register` and `tool.register`. A public Tool permission must explicitly declare `allowPublic`; otherwise Permission Engine requires an authenticated role grant.

Content can embed a registered public Tool with:

```text
[favorite-tool id="favorite.tool.ocr"]
```

Rendering Engine applies a Core-owned safe form after Content HTML sanitization. An inactive/missing Tool becomes a controlled unavailable state instead of breaking the page. The generic endpoints are:

- `POST /api/tools/{tool_id}/jobs`
- `GET /api/tools/{tool_id}/jobs/{job_id}`
- `DELETE /api/tools/{tool_id}/jobs/{job_id}`

They use Routing → API → Authentication/Permission → Tool Engine. They are not a second router or API system.

## Worker deployment boundary

Production Tool execution requires one operator-controlled gateway configured only through Configuration:

- `FAVORITE_TOOL_WORKER_URL`
- `FAVORITE_TOOL_WORKER_TOKEN`
- `FAVORITE_TOOL_TIMEOUT_SECONDS`

The token is secret and excluded from diagnostics/snapshots. The fixed gateway implements `/v1/health`, `/v1/jobs`, and `/v1/jobs/{id}`. Redirects are rejected, responses are bounded to 1 MB, timeouts are bounded, and browser/Plugin input cannot replace the configured destination. With no gateway configured, Tools report `not_configured` and the rest of the CMS remains healthy.

The Worker should run as a separate process/container with CPU, memory, execution-time, temporary-disk, concurrency, and network limits. Favorite CMS does not claim that same-process Python is sandboxed. OCR, conversion, transcription, and authorized media import belong in Workers. Domain CRUD does not require a Worker.

## Security and lifecycle

- Uploaded packages remain declarative and executable files are rejected.
- Capabilities are checked when a Plugin requests each public facade.
- Permissions, Domain contracts, Tool contracts, Routes, API operations, Rendering and Admin contributions are owner-scoped and removed on deactivation.
- Domain records and Tool job history survive restart; active Plugin state and approved capabilities remain explicitly persisted.
- A failing Plugin/Worker cannot become Database, Storage, Configuration, Routing, API, Permission, or process owner.
- Payment, inventory, booking, downloader, OCR, or other business rules belong to their Plugins/Workers; they are not hard-coded into this generic foundation.

## Current boundary

This repository provides the CMS-side foundation and test Workers only. No live OCR, downloader, payment, email, PostgreSQL, cloud Storage, or production Tool Worker provider was executed. A real Worker must be independently implemented, reviewed, deployed, authenticated, and resource-limited before a Tool can process production jobs.
