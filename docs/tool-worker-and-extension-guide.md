# Tool Worker, Plugin, and Theme guide

Favorite CMS keeps the web application stable by separating declarative extensions from resource-heavy work. A Plugin declares permissions, fields, routes, blocks, and Tool jobs. Core validates and authorizes those declarations. A separately deployed Tool Worker performs only fixed operations that the operator enabled.

## What the Worker supports

Version 0.1.0 provides two fixed Worker operations:

- `favorite.tool.ocr`: English/Bengali OCR for a bounded image obtained from an operator-allowlisted public HTTPS host.
- `favorite.tool.direct-media-download`: retrieval of a bounded direct image, audio, video, or PDF URL from an operator-allowlisted public HTTPS host.

This is not a general-purpose downloader. It does not resolve video-page URLs, bypass platform protections, DRM, authentication, or access controls. Only direct media URLs may be used. Operators are responsible for permission to retrieve supplied media.

The Worker does not execute Plugin code. Tool IDs are a fixed allowlist in the Worker. It rejects private/local destinations, redirects, URL credentials, excessive payloads, unexpected fields, unsupported media types, and unknown operations. OCR invokes the operator-installed Tesseract executable with a fixed argument list and `shell=False`.

## Run the Worker

Install Favorite CMS in its own environment, install Tesseract separately, and copy `.env.worker.example` to a local ignored environment file. Set a unique token of at least 32 characters and an exact comma-separated HTTPS source-host allowlist. Bengali OCR requires Tesseract's `ben` trained data.

Load the Worker environment into the Worker process, then run:

```powershell
python -m uvicorn favorite_worker.app:create_app --factory --host 127.0.0.1 --port 8060
```

On Windows, the repository's existing `scripts/start-local-cms.ps1` starts or reuses this Worker before backend/frontend startup whenever both CMS-side Worker settings are configured. `scripts/install-local-cms-autostart.ps1` installs that same unified startup flow at user logon; it does not create a second service architecture.

Configure the CMS-side Tool provider with the matching private Worker URL and token through Configuration. Keep both values server-only. Put the Worker behind an internal network boundary; do not publish its bearer token or artifact endpoint to browsers.

The current Worker keeps active job state in memory and completed download artifacts in its configured spool. A Worker restart can therefore interrupt an in-flight job. Artifact retention and cleanup are operator-managed in 0.1.0. Private CMS Media cannot yet be sent to the Worker because a signed service-to-service Media delivery contract does not exist. Public anonymous Tool execution is also disabled until rate-limit, quota, and abuse-control contracts exist.

## Create a declarative Tool Plugin

Create `plugins/<plugin-id>/plugin.json` and `contributions.json`. Use a stable reverse-domain identifier. The manifest declares only capabilities understood by PluginEngine; it cannot select Python modules, commands, services, environment variables, or filesystem paths.

Minimal manifest:

```json
{
  "id": "favorite.plugin.my-tool",
  "type": "plugin",
  "name": "My Tool",
  "version": "1.0.0",
  "minimumCoreVersion": "0.1.0",
  "maximumCoreVersion": "0.1.0",
  "dependencies": {},
  "optionalDependencies": {},
  "permissions": ["permission.register", "tool.register"]
}
```

Minimal Tool contribution:

```json
{
  "schemaVersion": 1,
  "permissions": [{"id": "favorite.plugin.my-tool.execute", "action": "execute", "resource": "plugin_tool"}],
  "entities": [],
  "tools": [{
    "id": "favorite.tool.my-tool",
    "label": "My Tool",
    "description": "A bounded Tool operation.",
    "executePermission": "favorite.plugin.my-tool.execute",
    "worker": "default",
    "public": false,
    "fields": [{"id": "source", "type": "text", "required": true, "maxLength": 500}]
  }],
  "blocks": []
}
```

The operation will not run until the Worker independently implements the exact Tool ID. Installation and activation remain separate. An administrator must explicitly approve declared capabilities, and the executing identity must have the Tool's execute permission. Deactivation removes registered contributions while Plugin-scoped durable state remains owned by Settings/Tool contracts.

Test manifest rejection, compatibility, capability denial, inactive default state, activation, job submission, cancellation, failure normalization, deactivation cleanup, restart behavior, and distribution inclusion. Never place credentials, executable packages, dependencies, databases, generated artifacts, or Worker spool data in a Plugin package.

## Create a Theme

A Theme is presentation-only. Create `themes/<theme-id>/theme.json` plus only the declared static resources permitted by ThemeEngine. Use the existing Starter Theme as the authoritative example. Declare the identifier, version, Core compatibility, and resource list; keep paths relative and bounded.

Themes may render existing public presentation models. They cannot query Database, Storage providers, Authentication, Permission, Configuration, environment variables, or private Core services. They cannot execute Python or JavaScript supplied as server code. Test manifest validation, missing/oversized/undeclared resources, traversal and symlink rejection, activation, failed-activation rollback, public rendering, and fallback to the previous valid Theme.

## Distribution checklist

Add approved runtime Plugin/Theme/Worker paths to `distribution/manifest.json`. Run the official deterministic distribution builder twice, compare SHA-256, inspect every entry, extract to a clean directory, install dependencies, migrate and install explicitly, and run real browser transport. Exclude tests, `.env`, Worker spool, databases, Storage contents, caches, bytecode, `.next`, `node_modules`, logs, and credentials.

## Security boundary

Favorite CMS does not sandbox arbitrary third-party executable code. Declarative Plugins and presentation-only Themes are the supported safe model. Adding a new resource-heavy operation requires a reviewed, fixed Worker implementation plus an explicit Plugin capability; a package cannot introduce its own callable. Remote package download, marketplace installation, arbitrary outbound HTTP, and arbitrary executable Plugin/Theme loading remain unsupported.
