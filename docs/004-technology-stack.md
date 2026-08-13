\# Favorite CMS



Document ID: 004



Title: Technology Stack



Version: 0.1.0



Status: Draft



Author: Favorite CMS



Created: 2026-08-07



Last Updated: 2026-08-07



Depends On:

001-project-overview.md

002-system-architecture.md

003-project-principles.md



Next Document:

005-folder-structure.md



\---



\# 1. Purpose



This document defines the official technology stack used throughout the Favorite CMS project.



The purpose of this document is to standardize all implementation technologies, development tools, programming languages, frameworks, databases, testing tools, and deployment targets.



Unless officially updated, every implementation must follow the technologies defined in this document.



\---



\# 2. Technology Selection Principles



Technology decisions are based on the following priorities:



\- Long-term maintainability

\- Stability

\- Developer productivity

\- AI-assisted development

\- Strong community support

\- Open-source ecosystem

\- Performance

\- Scalability

\- Simplicity



Technology is selected for long-term sustainability rather than short-term popularity.



\---



\# 3. Backend Technology



Primary Language



Python



Primary Framework



FastAPI



Reasons:



\- Modern architecture

\- Excellent API support

\- High performance

\- Excellent AI code generation

\- Strong typing support

\- Scalable modular architecture

\- Easy testing

\- Rich ecosystem



The Backend is responsible for all business logic, APIs, authentication, database operations, plugin management, and system services.



\---



\# 4. Frontend Technology



Primary Language



TypeScript



Primary Framework



React



Rendering Framework



Next.js



Reasons:



\- Component architecture

\- Excellent developer experience

\- Strong ecosystem

\- Type safety

\- Server-side rendering support

\- Modern UI development



The Frontend is responsible only for user interface rendering.





\---



\# 5. Database Technology



Development Database



SQLite



Production Database



PostgreSQL



Object Relational Mapper (ORM)



SQLAlchemy



Reasons:



\- SQLite enables simple local development.

\- PostgreSQL provides enterprise-grade reliability.

\- SQLAlchemy abstracts database operations.

\- Future database migration becomes easier.

\- Development and production environments remain consistent.



The application must never depend on database-specific features whenever a portable solution exists.



\---



\# 6. Authentication



Authentication Standard



JWT (JSON Web Token)



Session Support



Optional



Supported Authentication Methods



\- Email and Password

\- Google Authentication

\- GitHub Authentication

\- Future Plugin-based Providers



Reasons:



\- Stateless authentication

\- API-friendly architecture

\- Easy frontend integration

\- Mobile application compatibility



Authentication must always be handled by the Core.



\---



\# 7. Frontend Styling



Primary Styling Framework



Tailwind CSS



Reasons:



\- Utility-first workflow

\- Fast UI development

\- Easy customization

\- Small production bundle

\- Responsive design support



Themes may extend Tailwind but must never modify the Core styling system.



\---



\# 8. Storage



Development



Local Storage



Production



Cloudflare R2



Supported Future Providers



\- Amazon S3

\- MinIO

\- Compatible Object Storage



Reasons:



\- Easy local development

\- Scalable cloud storage

\- CDN compatibility

\- Cost-effective media storage



Storage providers should remain interchangeable through the Storage API.





\---



\# 9. Media Technologies



Media Player



React-based Player



Supported Technologies



\- HTML5 Video

\- HTML5 Audio

\- HLS.js

\- Media Session API

\- Picture-in-Picture API

\- Fullscreen API



The media layer must support multiple providers without changing the Core.



Media providers should be extendable through Plugins.



\---



\# 10. Development Tools



Primary Code Editor



Visual Studio Code



Version Control



Git



Repository Hosting



GitHub



Package Managers



Python



pip



Frontend



npm



These tools are considered the official development environment.



\---



\# 11. Testing



Backend Testing



Pytest



Frontend Testing



Playwright



Testing Principles



\- Every Core module should be testable.

\- Plugins should be tested independently.

\- Themes should be tested independently.

\- Integration testing should be performed before production releases.



\---



\# 12. Deployment



Development



Local Environment



Production



Self-hosted VPS



Alternative Deployment Targets



\- Docker

\- Railway

\- Render

\- Hostinger VPS



The deployment platform must never influence system architecture.



Deployment remains an implementation concern rather than an architectural concern.



\---



\# 13. Technology Rules



Only officially approved technologies should be introduced into the project.



Introducing a new framework, runtime, dependency, or database requires updating this document first.



Technology changes must never be introduced directly into implementation without documentation updates.



Consistency is considered more valuable than following technology trends.



\---



\## Acceptance Criteria



\- \[x] Official backend technologies defined.

\- \[x] Official frontend technologies defined.

\- \[x] Database technologies documented.

\- \[x] Authentication strategy documented.

\- \[x] Styling framework documented.

\- \[x] Storage technologies documented.

\- \[x] Media technologies documented.

\- \[x] Development tools documented.

\- \[x] Testing strategy documented.

\- \[x] Deployment strategy documented.

\- \[x] Technology governance documented.



\---



End of Document



Next Document:

005-folder-structure.md

