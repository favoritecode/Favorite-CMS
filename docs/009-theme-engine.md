\# Favorite CMS



Document ID: 009



Title: Theme Engine



Version: 1.0.0



Status: Draft



Author: Favorite CMS



Created: 2026-08-07



Last Updated: 2026-08-07



Depends On:

\- 001-project-overview.md

\- 002-system-architecture.md

\- 003-project-principles.md

\- 004-technology-stack.md

\- 005-folder-structure.md

\- 006-development-workflow.md

\- 007-core-engine.md

\- 008-extension-system.md



Next Document:

010-plugin-engine.md



\---



\# 1. Purpose



This document defines the architecture, responsibilities, lifecycle, and behavior of the Favorite CMS Theme Engine.



The Theme Engine is responsible for discovering, validating, loading, activating, and rendering Themes.



It provides a consistent presentation layer while remaining completely independent from business logic.



The Theme Engine manages only presentation.



It never manages application logic, database operations, authentication, or business features.



\---



\# 2. Theme Engine Objectives



The Theme Engine is designed to provide:



\- Theme Discovery

\- Theme Validation

\- Theme Installation

\- Theme Activation

\- Theme Switching

\- Template Resolution

\- Layout Management

\- Asset Management

\- Theme Configuration

\- Theme Rendering



The Theme Engine must remain lightweight, secure, and extensible.



\---



\# 3. Theme Responsibilities



The Theme Engine is responsible for:



\- Discovering installed Themes

\- Reading theme.json

\- Validating Theme compatibility

\- Registering Theme assets

\- Loading layouts

\- Loading templates

\- Rendering pages

\- Registering widget areas

\- Loading theme configuration

\- Switching active Themes



The Theme Engine must never:



\- Execute business logic

\- Access the database directly

\- Register API endpoints

\- Modify Core behavior

\- Process payments

\- Handle authentication



\---



\# 4. Theme Engine Architecture



The Theme Engine consists of the following components.



```text

Theme Engine

│

├── Theme Discovery

├── Theme Validator

├── Theme Loader

├── Theme Registry

├── Template Resolver

├── Layout Manager

├── Component Manager

├── Widget Manager

├── Asset Manager

├── Theme Renderer

└── Theme Config Manager

```



Each component has a single responsibility.



Communication between components must occur only through documented interfaces.







\---



\# 5. Theme Discovery



The Theme Engine automatically discovers installed Themes.



Discovery locations include:



```text

/themes/

```



Every directory inside the Themes folder is treated as a Theme candidate.



A directory is recognized as a valid Theme only if it contains a valid `theme.json` manifest.



Directories without a valid manifest must be ignored.



\---



\# 6. Theme Validation



Before a Theme can be installed or activated, it must pass validation.



Validation includes:



\- Manifest validation

\- Theme identifier validation

\- Version compatibility

\- Required Core version

\- Required Plugin dependencies

\- Directory structure validation

\- Required template validation

\- Required asset validation



A Theme that fails validation must never become active.



Validation errors should clearly describe the reason for failure.



\---



\# 7. Theme Lifecycle



Every Theme follows the same lifecycle.



```text

Theme Package

&#x20;     │

&#x20;     ▼

Discovery

&#x20;     │

&#x20;     ▼

Validation

&#x20;     │

&#x20;     ▼

Installation

&#x20;     │

&#x20;     ▼

Registration

&#x20;     │

&#x20;     ▼

Activation

&#x20;     │

&#x20;     ▼

Rendering

&#x20;     │

&#x20;     ▼

Update

&#x20;     │

&#x20;     ▼

Deactivation

&#x20;     │

&#x20;     ▼

Removal

```



The Theme Engine is responsible for managing every lifecycle stage.



\---



\# 8. Theme Activation



Only one Theme may remain active at any time.



During activation, the Theme Engine must:



\- Validate the Theme

\- Verify compatibility

\- Load theme.json

\- Register Theme assets

\- Register layouts

\- Register templates

\- Load Theme configuration

\- Mark the Theme as active



If activation fails, the previously active Theme must remain active.



The system must never be left without an active Theme.



\---



\# 9. Theme Switching



Theme switching must be safe and atomic.



The Theme Engine should:



1\. Validate the new Theme.

2\. Prepare the new Theme.

3\. Activate the new Theme.

4\. Verify successful activation.

5\. Deactivate the previous Theme.



If any step fails, the Theme Engine must automatically restore the previous Theme.



Theme switching must not require restarting the application.







\---



\# 10. Template Resolution



The Theme Engine is responsible for selecting the correct template for every request.



Template resolution follows a deterministic order.



Example:



```text

HTTP Request

&#x20;     │

&#x20;     ▼

Route

&#x20;     │

&#x20;     ▼

Request Type

&#x20;     │

&#x20;     ▼

Plugin Template (if available)

&#x20;     │

&#x20;     ▼

Theme Template

&#x20;     │

&#x20;     ▼

Default Template

&#x20;     │

&#x20;     ▼

404 Template

```



The Template Resolver must always return exactly one template.



If no matching template is found, the Theme Engine must load the default fallback template.



\---



\# 11. Layout Management



Layouts define the overall page structure.



A layout may include:



\- Header

\- Navigation

\- Sidebar

\- Main Content

\- Footer

\- Widget Areas



Multiple templates may share the same layout.



Layouts should maximize component reuse.



\---



\# 12. Component System



Components are reusable presentation elements.



Examples include:



\- Header

\- Footer

\- Navigation

\- Breadcrumb

\- Card

\- Modal

\- Pagination

\- Search Box

\- Media Player Container



Components must remain presentation-only.



Components must never contain business logic.



\---



\# 13. Widget Areas



Themes may define multiple widget areas.



Examples include:



\- Header

\- Sidebar

\- Footer

\- Homepage

\- Article

\- Player Sidebar



Plugins may register widgets into available widget areas.



The Theme Engine is responsible for rendering widget areas in the correct order.



\---



\# 14. Asset Management



The Theme Engine manages all Theme assets.



Supported assets include:



\- CSS

\- JavaScript

\- Fonts

\- Images

\- Icons

\- Static Files



The Asset Manager is responsible for:



\- Registering assets

\- Versioning assets

\- Loading assets

\- Preventing duplicate asset loading



Assets should be optimized for production whenever possible.

---

# 15. Theme Override Rules

Themes may override Plugin templates and components without modifying Plugin source code.

Override priority:

Theme Override

↓

Plugin Default

↓

System Default

The Theme Engine must always select the highest-priority compatible resource.

---

# 16. Theme Update Process

Every Theme update must follow the official Extension update process.

Update process:

- Validate package
- Create backup
- Install update
- Verify templates
- Verify assets
- Activate updated Theme

If verification fails, the previous Theme version must be restored automatically.

---

# 17. Theme Failure Handling

If a Theme fails during activation or rendering:

- Record the failure
- Restore the previously active Theme
- Notify the administrator
- Keep the website operational

A Theme failure must never stop the Core.

---

# 18. Theme Security

Themes must never:

- Execute business logic
- Access the database directly
- Access private Core APIs
- Modify Plugins

Themes communicate only through the Theme Engine and officially documented interfaces.

---

## Acceptance Criteria

- [x] Theme discovery defined.
- [x] Theme validation documented.
- [x] Theme lifecycle documented.
- [x] Theme activation documented.
- [x] Theme switching documented.
- [x] Template resolution documented.
- [x] Layout system documented.
- [x] Component system documented.
- [x] Widget system documented.
- [x] Asset management documented.
- [x] Theme override rules defined.
- [x] Theme update process documented.
- [x] Theme failure handling documented.
- [x] Theme security documented.

---

End of Document

Next Document:

010-plugin-engine.md









