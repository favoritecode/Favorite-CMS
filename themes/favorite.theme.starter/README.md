# Favorite Starter Theme

Favorite Starter is the neutral public website Theme bundled with Favorite CMS.

It declares its templates, shared layout, header/footer components, and stylesheet in `resources.json`. The Theme contains presentation resources only: it performs no database, Storage, Authentication, Permission, environment, or filesystem operations.

The public platform supplies safe render models from existing Content and Search contracts. Rendering resolves the active Theme and composes these declared resources. If this Theme is inactive or an optional override is unavailable, the existing Theme → Plugin → Platform fallback remains authoritative.

Supported public presentation routes are:

- `/site/welcome` — starter homepage and recent published Content
- `/site/content` — published Content listing
- `/site/content/{content_id}` — published Content detail
- `/site/search/{query}` — public Search results

Version: 1.0.0
