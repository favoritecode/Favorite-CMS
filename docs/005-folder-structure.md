\# Favorite CMS



Document ID: 005



Title: Folder Structure



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



Next Document:

006-development-workflow.md



\---



\# 1. Purpose



This document defines the official folder structure of the Favorite CMS project.



The directory layout is designed to provide:



\- Clear separation of responsibilities

\- Modular architecture

\- Independent Theme development

\- Independent Plugin development

\- Long-term maintainability

\- AI-assisted development

\- Automated testing

\- Future scalability



Every folder has a single responsibility.



The folder structure defined in this document is part of the platform architecture and must remain stable throughout the lifetime of the project.



\---



\# 2. Architecture Layers



Favorite CMS is organized into six architectural layers.



```text

Project Root

&#x20;   │

&#x20;   ├── Core Platform

&#x20;   ├── Built-in Engines

&#x20;   ├── Extensions

&#x20;   ├── Applications

&#x20;   ├── Runtime

&#x20;   └── Documentation

```



Each layer has an independent responsibility.



Communication between layers must always occur through public interfaces.



\---



\# 3. Project Root Structure



```text

favorite-cms/

│

├── backend/

├── frontend/

├── plugins/

├── themes/

├── storage/

├── docs/

├── tests/

├── scripts/

├── tools/

├── resources/

├── .github/

│

├── README.md

├── LICENSE

├── .gitignore

└── docker-compose.yml

```



\---



\# 4. Root Directory Responsibilities



\### backend/



Contains the backend application including the Core, Engines, APIs, Framework integration, and platform infrastructure.



\### frontend/



Contains the frontend application responsible for rendering the active Theme.



\### plugins/



Contains all installable business feature Plugins.



Examples:



\- Movie

\- Shop

\- Subscription

\- Music

\- Player

\- Analytics



\### themes/



Contains all installable frontend Themes.



Themes control only presentation.



\### storage/



Contains runtime-generated files.



Examples:



\- Uploads

\- Cache

\- Logs

\- Temporary Files

\- Backups



\### docs/



Contains all architecture documents, specifications, development guides, and technical documentation.



\### tests/



Contains project-wide automated tests.



\### scripts/



Contains development, deployment, maintenance, and automation scripts.



\### tools/



Contains internal development utilities.



\### resources/



Contains shared project resources.



\### .github/



Contains GitHub workflows and repository configuration.



\---



\# 5. Design Rules



\- One folder must have one responsibility.

\- Core infrastructure must remain isolated.

\- Business features belong only to Plugins.

\- Presentation belongs only to Themes.

\- Runtime files must never be mixed with source code.

\- Documentation must remain independent from implementation.

\- The folder structure should remain stable across project versions.







\---



\# 6. Backend Structure



The backend contains the entire platform infrastructure.



It is responsible for:



\- Core platform

\- Built-in Engines

\- REST APIs

\- Authentication

\- Database

\- Framework integration

\- System services



The backend never contains Theme presentation.



\---



\## Backend Directory Layout



```text

backend/

│

├── bootstrap/

├── core/

├── engines/

├── api/

├── framework/

├── database/

├── shared/

├── config/

├── storage/

├── tests/

└── main.py

```



\---



\# 7. Backend Directory Responsibilities



\## bootstrap/



Responsible for starting the application.



Responsibilities include:



\- Loading environment variables

\- Loading configuration

\- Initializing the application

\- Registering system services

\- Starting the application lifecycle



\---



\## core/



Contains the permanent infrastructure of Favorite CMS.



The Core must remain small, stable, and independent.



The Core never contains business features.



Structure:



```text

core/

│

├── kernel/

├── container/

├── contracts/

├── providers/

├── events/

├── hooks/

├── support/

├── exceptions/

└── interfaces/

```



Core responsibilities include:



\- Application Kernel

\- Dependency Injection Container

\- Event Dispatcher

\- Hook System

\- Service Registration

\- Core Contracts

\- Exception Handling



\---



\## engines/



Contains built-in CMS capabilities.



An Engine provides platform functionality rather than business functionality.



Structure:



```text

engines/

│

├── auth/

├── user/

├── content/

├── media/

├── theme/

├── plugin/

├── settings/

├── menu/

├── search/

├── seo/

├── update/

└── notification/

```



Examples:



\- Authentication Engine

\- Theme Engine

\- Plugin Engine

\- Content Engine

\- Media Library Engine



Movie management, Shop management, Subscription, Music, Live TV, and similar features are \*\*not Engines\*\*. They must always be implemented as Plugins.



\---



\## api/



Contains all public API endpoints.



The API layer communicates only with the Core and Engines.



Direct database queries inside API controllers are not allowed.



\---



\## framework/



Contains integrations with external frameworks and libraries.



Examples include:



\- FastAPI

\- SQLAlchemy

\- JWT

\- Scheduler



The rest of the platform should depend on abstractions instead of directly depending on third-party libraries.





\---



\## database/



Contains the database infrastructure.



Responsibilities include:



\- Database Connection

\- ORM Configuration

\- Database Migrations

\- Seed Data

\- Database Utilities



Business logic must never be placed inside this directory.



\---



\## shared/



Contains reusable components shared across the backend.



Examples include:



\- Constants

\- Helper Functions

\- Validators

\- Utility Classes

\- Shared Types



This directory must never contain business-specific functionality.



\---



\## config/



Contains application configuration.



Examples include:



\- Environment Configuration

\- System Configuration

\- Feature Flags

\- Default Configuration

\- Configuration Loaders



Configuration must remain separate from implementation logic.



\---



\## storage/



Contains backend runtime data.



Examples include:



\- Cache

\- Temporary Files

\- Generated Files

\- Runtime Metadata



Application source code must never be stored in this directory.



\---



\## tests/



Contains backend automated tests.



Test categories include:



\- Unit Tests

\- Integration Tests

\- API Tests

\- Performance Tests



Every Engine should include corresponding automated tests.



\---



\## main.py



The application entry point.



Responsibilities include:



\- Starting the application

\- Executing the bootstrap process

\- Initializing the Core

\- Loading active Engines

\- Starting the HTTP server



Business logic must never be implemented inside the application entry point.



\---



\# 8. Frontend Structure



The frontend is responsible only for presentation.



It renders data received from Backend APIs.



```text

frontend/

│

├── app/

├── components/

├── layouts/

├── pages/

├── services/

├── hooks/

├── contexts/

├── assets/

├── styles/

├── public/

├── utilities/

├── types/

├── config/

├── tests/

└── package.json

```



The frontend must never:



\- Access the database directly.

\- Implement business rules.

\- Bypass authentication.

\- Access internal Core services.



All communication must occur through the official Backend APIs.



\---



\# 9. Plugin Structure



Every Plugin must follow the same structure.



```text

plugins/

└── movie/

&#x20;   │

&#x20;   ├── backend/

&#x20;   ├── admin/

&#x20;   ├── client/

&#x20;   ├── database/

&#x20;   ├── routes/

&#x20;   ├── services/

&#x20;   ├── assets/

&#x20;   ├── config/

&#x20;   ├── docs/

&#x20;   ├── tests/

&#x20;   ├── plugin.json

&#x20;   └── README.md

```



Each Plugin must be installable, updateable, disableable, and removable independently.



Plugins must never modify Core source code.



\---



\# 10. Theme Structure



Every Theme must follow the same structure.



```text

themes/

└── default/

&#x20;   │

&#x20;   ├── layouts/

&#x20;   ├── pages/

&#x20;   ├── components/

&#x20;   ├── partials/

&#x20;   ├── widgets/

&#x20;   ├── assets/

&#x20;   ├── config/

&#x20;   ├── languages/

&#x20;   ├── theme.json

&#x20;   └── README.md

```



Themes are responsible only for presentation.



Themes must never contain business logic or direct database access.



\---



\# 11. Folder Structure Principles



The following rules apply to the entire project.



\- Every directory has a single responsibility.

\- Core infrastructure must remain isolated.

\- Built-in capabilities belong to Engines.

\- Business functionality belongs to Plugins.

\- Presentation belongs to Themes.

\- Runtime data must remain outside source code.

\- Documentation is the single source of truth.

\- All modules must follow the official project structure.



\---



\## Acceptance Criteria



\- \[x] Root structure defined.

\- \[x] Backend structure defined.

\- \[x] Frontend structure defined.

\- \[x] Plugin structure defined.

\- \[x] Theme structure defined.

\- \[x] Directory responsibilities documented.

\- \[x] Folder design principles established.



\---



End of Document



Next Document:

006-development-workflow.md

