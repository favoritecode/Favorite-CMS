\# Favorite CMS



Document ID: 003



Title: Project Principles



Version: 0.1.0



Status: Draft



Author: Favorite CMS



Created: 2026-08-07



Last Updated: 2026-08-07



Depends On:

001-project-overview.md

002-system-architecture.md



Next Document:

004-technology-stack.md



\---



\# 1. Purpose



This document defines the engineering principles, architectural rules, documentation standards, and long-term development philosophy of Favorite CMS.



Every contributor, developer, AI coding assistant, and future maintainer must follow these principles.



These rules are considered mandatory unless explicitly replaced by a newer version of this document.



\---



\# 2. Project Principles



Favorite CMS is developed according to the following principles.



\- Documentation First

\- Architecture First

\- Core First

\- Plugin First Expansion

\- Theme Driven Presentation

\- API First Communication

\- Security First

\- Stability Before Features

\- Simplicity Before Complexity

\- Long-Term Maintainability



These principles apply to every module developed for the platform.



\---



\# 3. Design Philosophy



The project is designed for long-term growth.



The objective is not to build the fastest CMS.



The objective is to build a stable platform that can continue evolving for many years without requiring major architectural redesign.



Every architectural decision should prioritize maintainability over short-term convenience.



\---



\# 4. Project Scope



Favorite CMS is intended to become a universal website platform.



The platform should be capable of supporting multiple industries using the same Core.



Examples include:



\- Blogs

\- News Portals

\- Business Websites

\- Streaming Platforms

\- Movie Platforms

\- Music Platforms

\- E-commerce

\- Membership Platforms

\- Educational Platforms

\- Company Websites



No industry-specific functionality belongs inside the Core.







\---



\# 5. Core Principles



The Core is the foundation of the platform.



The Core must remain:



\- Lightweight

\- Stable

\- Independent

\- Secure

\- Backward Compatible

\- Extensible



The Core must never include business-specific functionality.



Every new feature request must first be evaluated to determine whether it belongs in the Core or should be implemented as a Plugin.



If uncertainty exists, the default decision is to implement the feature as a Plugin.



\---



\# 6. Theme Principles



Themes control presentation only.



Themes must never contain:



\- Business Logic

\- Authentication Logic

\- Payment Logic

\- Database Queries

\- Plugin Implementations



Themes should remain replaceable without affecting application functionality.



Changing a Theme must never require changes to the Core.



\---



\# 7. Plugin Principles



Plugins extend the platform without modifying the Core.



Every Plugin should be:



\- Independent

\- Reusable

\- Versioned

\- Documented

\- Testable



Plugins should expose public APIs whenever integration with other Plugins is required.



Direct communication between Plugins should be avoided whenever possible.



\---



\# 8. API Principles



Every system component communicates through documented APIs.



Internal implementation details must never be accessed directly.



Public APIs must remain stable across compatible versions.



Breaking changes require a new major version.



All APIs must be documented before implementation begins.





\---



\# 9. Documentation Principles



Documentation is the single source of truth for the entire project.



Every architectural decision must be documented before implementation.



Documentation must always be updated before code changes are accepted.



Every document should have:



\- Document ID

\- Version

\- Status

\- Dependencies

\- Next Document

\- Acceptance Criteria



Documentation should describe architecture, responsibilities, and expected behavior.



Documentation should never depend on implementation details unless the document is specifically intended for implementation.



\---



\# 10. AI Development Principles



Artificial Intelligence is a development assistant.



Artificial Intelligence is not the project architect.



AI assistants must:



\- Follow documentation exactly.

\- Respect architectural boundaries.

\- Generate maintainable code.

\- Write production-quality implementations.

\- Generate tests when requested.

\- Explain implementation decisions when necessary.



AI assistants must never:



\- Invent new architecture.

\- Change project philosophy.

\- Ignore documented requirements.

\- Introduce undocumented dependencies.

\- Modify unrelated modules.



All generated code must follow the official project documentation.



\---



\# 11. Development Principles



Development should always follow the same lifecycle.



Requirement



↓



Documentation



↓



Architecture Review



↓



Implementation



↓



Testing



↓



Review



↓



Release



Skipping documentation or architecture review is not allowed.



Every completed module must satisfy its documented acceptance criteria before being considered complete.



\---



\# 12. Versioning Principles



The project follows semantic versioning.



Major versions introduce architectural or incompatible changes.



Minor versions introduce new compatible functionality.



Patch versions contain bug fixes, security improvements, and maintenance updates.



Documentation versions should evolve together with implementation whenever architectural changes occur.



\---



\## Acceptance Criteria



\- \[x] Project principles defined.

\- \[x] Architecture principles documented.

\- \[x] Core responsibilities clarified.

\- \[x] Plugin principles established.

\- \[x] Theme principles established.

\- \[x] Long-term development principles documented.



\---



End of Document



Next Document:

004-technology-stack.md

