\# Favorite CMS



Document ID: 002



Title: System Architecture



Version: 0.1.0



Status: Draft



Author: Favorite CMS



Created: 2026-08-07



Last Updated: 2026-08-07



Depends On:

001-project-overview.md



Next Document:

003-project-principles.md



\---



\# 1. Purpose



This document defines the overall architecture of Favorite CMS.



It describes how the Core, Themes, Plugins, APIs, Storage, Database, and User Interface interact with each other.



This document is considered the highest-level technical specification of the platform.



Every future module must follow the architecture defined here.



\---



\# 2. Architecture Overview



Favorite CMS follows a layered modular architecture.



The platform consists of three primary layers:



1\. Core

2\. Theme

3\. Plugin



Each layer has a clearly defined responsibility.



No layer is allowed to replace or duplicate the responsibility of another layer.



\---



\# 3. High-Level Architecture



&#x20;                   User

&#x20;                     │

&#x20;                     ▼

&#x20;            Frontend Theme

&#x20;                     │

&#x20;                     ▼

&#x20;               Public API

&#x20;                     │

&#x20;                     ▼

&#x20;             Favorite CMS Core

&#x20;                     │

&#x20;       ┌─────────────┼─────────────┐

&#x20;       │             │             │

&#x20;       ▼             ▼             ▼

&#x20;   Theme Engine  Plugin Engine  System Services

&#x20;       │             │             │

&#x20;       └─────────────┼─────────────┘

&#x20;                     │

&#x20;                     ▼

&#x20;              Database Layer

&#x20;                     │

&#x20;                     ▼

&#x20;         Storage / File System



\---



\# 4. Core Responsibilities



The Core is responsible for platform infrastructure.



Its responsibilities include:



\- Bootstrapping

\- Authentication

\- Authorization

\- User Management

\- Routing

\- Theme Management

\- Plugin Management

\- REST API

\- Settings Engine

\- File Management

\- Logging

\- Security

\- Database Access

\- Event System

\- Hook System

\- Dependency Management

\- Update Management



The Core must remain independent from business-specific features.





\---



\# 5. Layer Relationships



The platform consists of three independent architectural layers.



&#x20;                Core

&#x20;               /    \\

&#x20;              /      \\

&#x20;         Theme      Plugin



The Core is the only mandatory layer.



Themes and Plugins are optional extensions.



Neither Themes nor Plugins are allowed to replace Core responsibilities.



Themes and Plugins are isolated from each other and communicate only through officially supported APIs provided by the Core.



\---



\# 6. Core Architecture



The Core contains only platform infrastructure.



Core Modules:



\- Bootstrap

\- Configuration

\- Router

\- Authentication

\- Authorization

\- User Management

\- Theme Engine

\- Plugin Engine

\- Event Manager

\- Hook Manager

\- Settings Manager

\- File Manager

\- Logger

\- Cache Manager

\- Update Manager

\- Dependency Manager

\- REST API

\- Database Layer



The Core does not contain business modules.



Movie management, E-commerce, Membership, Streaming, Digital Products, Physical Products, Forums, and similar functionality must always be implemented as Plugins.



\---



\# 7. Theme Architecture



Themes are visual packages.



Themes define only how data is presented.



A Theme may contain:



\- Layouts

\- Templates

\- Components

\- CSS

\- JavaScript

\- Fonts

\- Images

\- Icons

\- Theme Configuration



Themes never contain business logic.



Themes never directly communicate with the database.



Themes receive data only through the Core APIs and Plugin APIs.



\---



\# 8. Plugin Architecture



Plugins extend the capabilities of the Core.



A Plugin may register:



\- Routes

\- REST APIs

\- Admin Menus

\- Frontend Pages

\- Widgets

\- Permissions

\- Scheduled Tasks

\- Database Migrations

\- Services

\- Hooks

\- Event Listeners



Every Plugin must be independently installable, removable, enableable, disableable, and updateable.



A Plugin must never directly modify another Plugin or the Core source code.





\---



\# 9. Request Flow



Every request must follow the same processing pipeline.



&#x20;                Client

&#x20;                   │

&#x20;                   ▼

&#x20;           HTTP Request

&#x20;                   │

&#x20;                   ▼

&#x20;              Web Server

&#x20;                   │

&#x20;                   ▼

&#x20;            Favorite CMS Core

&#x20;                   │

&#x20;       ┌───────────┴───────────┐

&#x20;       │                       │

&#x20;Authentication            Public Route

&#x20;       │                       │

&#x20;       └───────────┬───────────┘

&#x20;                   ▼

&#x20;            Plugin Processing

&#x20;                   │

&#x20;                   ▼

&#x20;            Business Services

&#x20;                   │

&#x20;                   ▼

&#x20;             Database Layer

&#x20;                   │

&#x20;                   ▼

&#x20;            Response Builder

&#x20;                   │

&#x20;                   ▼

&#x20;             Theme Renderer

&#x20;                   │

&#x20;                   ▼

&#x20;              HTTP Response



Every request must pass through the Core.



Themes never communicate directly with the database.



Plugins never bypass the Core.



\---



\# 10. Data Flow



Data always flows in one direction.



Database

&#x20;   │

&#x20;   ▼

Core Services

&#x20;   │

&#x20;   ▼

Plugin Services

&#x20;   │

&#x20;   ▼

Public API

&#x20;   │

&#x20;   ▼

Theme

&#x20;   │

&#x20;   ▼

User Interface



Reverse communication is not allowed.



Themes cannot write directly to the database.



Themes communicate only through APIs.



\---



\# 11. Theme Loading Flow



When a request reaches the frontend:



HTTP Request



↓



Router



↓



Resolve Current Theme



↓



Load Theme Configuration



↓



Load Required Templates



↓



Collect Plugin Data



↓



Render Components



↓



Generate HTML



↓



Return Response



Themes are loaded only after the Core has finished processing the request.



Themes never initialize system services.



\---



\# 12. Plugin Loading Flow



System Startup



↓



Load Core



↓



Load Configuration



↓



Load Active Plugins



↓



Validate Dependencies



↓



Register Services



↓



Register Hooks



↓



Register Routes



↓



Register APIs



↓



Ready



Plugins are initialized only after the Core has completed its startup process.







\---



\# 13. Dependency Rules



Favorite CMS follows strict dependency rules.



Allowed dependencies:



Core

↓



Theme



Core

↓



Plugin



Plugin

↓



Core Public APIs



Theme

↓



Core Public APIs



Theme

↓



Plugin Public APIs



The following dependencies are NOT allowed:



Core

✗

Plugin



Core

✗

Theme



Plugin

✗

Plugin (Direct Access)



Theme

✗

Database



Theme

✗

Core Internal Services



Every communication must happen through officially documented public interfaces.



\---



\# 14. Failure Isolation



The system must isolate failures whenever possible.



Examples:



A Theme failure must not stop the Core.



A Plugin failure must not stop the Core.



A Movie Plugin failure must not disable the Shop Plugin.



A Shop Plugin failure must not disable User Authentication.



Failures should remain isolated inside the component where they occur.



Recovery mechanisms should always prefer disabling the failing component instead of stopping the platform.



\---



\# 15. Recovery Strategy



If a Theme fails during activation:



↓



Reject activation



↓



Keep previous Theme active



If a Plugin fails during installation:



↓



Rollback installation



↓



Disable Plugin



↓



Keep Core running



If a Plugin fails after an update:



↓



Restore previous version



↓



Disable failing Plugin



↓



Keep system operational



System availability always has higher priority than feature availability.



\---



\# 16. Architecture Principles



The architecture is based on the following principles.



\- Separation of Concerns

\- Modular Design

\- Low Coupling

\- High Cohesion

\- API First

\- Documentation First

\- Local First Development

\- AI Assisted Development

\- Plugin First Expansion

\- Long Term Maintainability



These principles must guide every architectural decision made throughout the lifetime of the project.





\---



\# 17. Core Evolution Policy



The Core must evolve very slowly.



New business features must never be added directly into the Core.



The Core should only receive updates for:



\- Security improvements

\- Performance optimizations

\- Bug fixes

\- Infrastructure improvements

\- Public API improvements

\- Developer experience improvements



Business functionality must always be delivered through Plugins.



The long-term objective is to keep the Core stable for many years while allowing unlimited expansion through Themes and Plugins.



\---



\# 18. Scalability Strategy



Favorite CMS is designed to scale horizontally through modular expansion rather than by increasing Core complexity.



Future functionality should be added as:



\- New Plugins

\- New Themes

\- Shared Libraries

\- Public APIs



The Core should remain lightweight regardless of the number of installed Plugins.



\---



\# 19. Architectural Summary



The architecture of Favorite CMS is based on a simple principle.



Core provides infrastructure.



Themes provide presentation.



Plugins provide functionality.



Every future module developed for the platform must respect this separation.



Violating these boundaries increases maintenance cost and reduces long-term stability.



\---



\## Acceptance Criteria



\- \[x] High-level architecture defined.

\- \[x] Core responsibilities documented.

\- \[x] Theme responsibilities documented.

\- \[x] Plugin responsibilities documented.

\- \[x] Request flow defined.

\- \[x] Data flow defined.

\- \[x] Theme loading flow documented.

\- \[x] Plugin loading flow documented.

\- \[x] Dependency rules documented.

\- \[x] Failure isolation documented.

\- \[x] Recovery strategy documented.

\- \[x] Core evolution policy documented.



\---



End of Document



Next Document:

003-project-principles.md

