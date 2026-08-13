\# Favorite CMS



Document ID: 007



Title: Core Engine



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


Next Document:
008-extension-system.md


\---



\# 1. Purpose



This document defines the architecture, responsibilities, lifecycle, and internal behavior of the Favorite CMS Core Engine.



The Core Engine is the heart of the platform.



It manages application startup, service registration, dependency management, request processing, configuration loading, plugin integration, theme integration, and system-wide infrastructure.



Every other component of the platform depends on the Core Engine.



The Core Engine depends on no business-specific module.



\---



\# 2. Core Objectives



The Core Engine is designed to provide:



\- Stability

\- Extensibility

\- Performance

\- Security

\- Maintainability

\- Framework Independence

\- AI-friendly Architecture



The Core Engine must remain lightweight regardless of the number of installed Plugins or Themes.



Business functionality must never be implemented inside the Core.



\---



\# 3. Core Responsibilities



The Core Engine is responsible for:



\- Bootstrapping

\- Application Lifecycle

\- Configuration Management

\- Service Registration

\- Dependency Injection

\- Event Dispatching

\- Hook Management

\- Engine Registration

\- Plugin Registration

\- Theme Registration

\- Request Routing

\- Error Handling

\- Logging

\- Cache Integration

\- Security Enforcement



The Core Engine provides infrastructure only.



Business logic belongs to Plugins.



Presentation belongs to Themes.



\---



\# 4. Core Architecture



The Core is divided into independent infrastructure components.



```text

Core Engine

│

├── Kernel

├── Service Container

├── Configuration Manager

├── Event Manager

├── Hook Manager

├── Engine Manager

├── Plugin Manager

├── Theme Manager

├── Router

├── Logger

├── Cache Manager

└── Error Handler

```



Each component has one responsibility.



Communication between components must occur through documented public interfaces.



The Core Engine must never depend on Plugin implementation details.





\---



\# 5. Core Lifecycle



The Core Engine follows a fixed lifecycle.



Every application startup must execute the same sequence.



```text

Application Start

&#x20;       │

&#x20;       ▼

Bootstrap

&#x20;       │

&#x20;       ▼

Load Configuration

&#x20;       │

&#x20;       ▼

Initialize Core

&#x20;       │

&#x20;       ▼

Register Core Services

&#x20;       │

&#x20;       ▼

Initialize Service Container

&#x20;       │

&#x20;       ▼

Load Engines

&#x20;       │

&#x20;       ▼

Load Plugins

&#x20;       │

&#x20;       ▼

Load Active Theme

&#x20;       │

&#x20;       ▼

Register Routes

&#x20;       │

&#x20;       ▼

Start HTTP Server

&#x20;       │

&#x20;       ▼

Application Ready

```



The startup sequence must remain deterministic.



No Plugin or Theme may execute before the Core has completed initialization.



\---



\# 6. Kernel



The Kernel is the central controller of the Core Engine.



Responsibilities include:



\- Managing the application lifecycle

\- Coordinating startup

\- Coordinating shutdown

\- Initializing Core components

\- Monitoring system state

\- Handling fatal system failures



Only one Kernel instance exists during application execution.



The Kernel must not contain business logic.



\---



\# 7. Service Container



The Service Container manages all platform services.



Responsibilities include:



\- Registering services

\- Resolving dependencies

\- Managing service lifecycles

\- Providing dependency injection

\- Preventing duplicate registrations



Every Core component should obtain dependencies through the Service Container.



Direct instantiation of shared services should be avoided whenever possible.



\---



\# 8. Configuration Manager



The Configuration Manager is responsible for loading and managing system configuration.



Configuration sources may include:



\- Environment variables

\- Configuration files

\- Database settings

\- Plugin configuration

\- Theme configuration



Configuration should be loaded once during startup and shared throughout the application.



The Configuration Manager must provide a consistent interface for accessing configuration values.





\---



\# 9. Event Manager



The Event Manager provides a centralized event-driven communication system.



Responsibilities include:



\- Registering Events

\- Registering Event Listeners

\- Dispatching Events

\- Managing Event Propagation

\- Supporting Plugin Event Integration



Events enable loose coupling between independent system components.



The Event Manager must never depend on Plugin implementations.



\---



\# 10. Hook Manager



The Hook Manager allows Plugins and Themes to extend platform behavior without modifying Core source code.



Supported Hook Types:



\- Action Hooks

\- Filter Hooks



Responsibilities include:



\- Registering Hooks

\- Executing Hook Callbacks

\- Managing Hook Priority

\- Providing Extension Points



The Hook Manager is the primary extension mechanism of Favorite CMS.



Every public Hook must be documented.



\---



\# 11. Engine Manager



The Engine Manager controls all built-in Engines.



Responsibilities include:



\- Registering Engines

\- Initializing Engines

\- Managing Engine Lifecycle

\- Resolving Engine Dependencies

\- Monitoring Engine Status



Only officially supported Engines may be registered.



Engine initialization order must remain deterministic.



\---



\# 12. Plugin Manager



The Plugin Manager controls the complete Plugin lifecycle.



Responsibilities include:



\- Discovering installed Plugins

\- Reading plugin.json

\- Validating compatibility

\- Resolving dependencies

\- Installing Plugins

\- Enabling Plugins

\- Disabling Plugins

\- Updating Plugins

\- Removing Plugins



A Plugin must never be loaded before passing validation.



Plugin failures must never prevent the Core from starting unless the Plugin is explicitly marked as required.



\---



\# 13. Theme Manager



The Theme Manager controls Theme discovery, validation, activation, and rendering.



Responsibilities include:



\- Discovering installed Themes

\- Reading theme.json

\- Validating compatibility

\- Activating Themes

\- Switching Themes

\- Loading Templates

\- Registering Theme Assets



Only one Theme may remain active at any time.



If Theme activation fails, the previously active Theme must remain active.







\---



\# 14. Request Lifecycle



Every incoming request must pass through the Core Engine.



The request lifecycle is defined as follows.



```text

HTTP Request

&#x20;     │

&#x20;     ▼

Web Server

&#x20;     │

&#x20;     ▼

Kernel

&#x20;     │

&#x20;     ▼

Middleware

&#x20;     │

&#x20;     ▼

Router

&#x20;     │

&#x20;     ▼

Authentication

&#x20;     │

&#x20;     ▼

Authorization

&#x20;     │

&#x20;     ▼

Engine Resolution

&#x20;     │

&#x20;     ▼

Plugin Execution

&#x20;     │

&#x20;     ▼

Response Generation

&#x20;     │

&#x20;     ▼

Theme Rendering

&#x20;     │

&#x20;     ▼

HTTP Response

```



Every request must follow the same lifecycle.



No Plugin or Theme may bypass the Core request pipeline.



\---



\# 15. Error Handling



The Core Engine is responsible for centralized error handling.



Responsibilities include:



\- Capturing Exceptions

\- Logging Errors

\- Returning Safe Responses

\- Preventing System Crashes

\- Reporting Critical Failures



Internal implementation details must never be exposed to end users.



\---



\# 16. Core Security



The Core Engine enforces platform-wide security.



Responsibilities include:



\- Authentication Enforcement

\- Authorization Enforcement

\- CSRF Protection

\- Input Validation

\- Output Sanitization

\- Rate Limiting

\- Secure Configuration Loading



Security policies apply equally to the Core, Engines, Plugins, and Themes.



No component may bypass Core security controls.



\---



\# 17. Core Extension Rules



The Core may be extended only through officially supported extension points.



Supported extension mechanisms include:



\- Events

\- Hooks

\- Public APIs

\- Service Providers



Direct modification of Core source code is prohibited.



Plugins and Themes must use documented extension points only.



\---



\# 18. Core Stability Policy



The Core Engine must evolve slowly.



Core updates should be limited to:



\- Security improvements

\- Performance improvements

\- Infrastructure improvements

\- Bug fixes

\- Public API enhancements



Business features must never be added directly to the Core.



The long-term objective is to keep the Core stable while allowing unlimited expansion through Plugins and Themes.



\---



\## Acceptance Criteria



\- \[x] Core objectives defined.

\- \[x] Core responsibilities documented.

\- \[x] Startup lifecycle documented.

\- \[x] Kernel defined.

\- \[x] Service Container defined.

\- \[x] Configuration Manager defined.

\- \[x] Event Manager defined.

\- \[x] Hook Manager defined.

\- \[x] Engine Manager defined.

\- \[x] Plugin Manager defined.

\- \[x] Theme Manager defined.

\- \[x] Request lifecycle documented.

\- \[x] Error handling defined.

\- \[x] Core security documented.

\- \[x] Core extension rules documented.

\- \[x] Core stability policy documented.



\---



End of Document



Next Document:
008-extension-system.md

