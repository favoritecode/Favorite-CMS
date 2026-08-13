\# Favorite CMS



Document ID: 006



Title: Development Workflow



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



Next Document:

007-core-engine.md



\---



\# 1. Purpose



This document defines the official software development workflow of Favorite CMS.



It establishes how new features, bug fixes, architectural changes, documentation, implementation, testing, and releases are performed.



Every contributor, including AI coding assistants, must follow this workflow.



No implementation should begin without following the process described in this document.



\---



\# 2. Development Philosophy



Favorite CMS follows an \*\*Architecture First\*\* development model.



The project is designed before it is implemented.



The implementation follows the documentation.



Documentation always has higher priority than source code.



Whenever documentation and implementation conflict, the documentation must be reviewed first.



\---



\# 3. Official Development Workflow



Every new feature follows the same lifecycle.



```text

Idea



↓



Discussion



↓



Documentation



↓



Architecture Review



↓



Approval



↓



Implementation



↓



Testing



↓



Review



↓



Optimization



↓



Release

```



No step should be skipped.



Each stage must be completed before moving to the next stage.



\---



\# 4. Documentation Workflow



Every module begins with documentation.



Documentation should define:



\- Purpose

\- Scope

\- Responsibilities

\- Architecture

\- Rules

\- Folder Structure

\- APIs

\- Acceptance Criteria



Implementation starts only after documentation is approved.



Documentation is considered the official specification of every module.







\---



\# 5. Project Roles



Favorite CMS defines clear responsibilities for every participant involved in development.



\---



\## Product Owner



The Product Owner defines:



\- Product vision

\- Business requirements

\- Feature priorities

\- Final approval

\- Project roadmap



The Product Owner is responsible for deciding what should be built.



\---



\## Software Architect



The Software Architect is responsible for:



\- Designing the system architecture

\- Defining module boundaries

\- Creating technical specifications

\- Maintaining documentation

\- Reviewing architectural decisions



The Software Architect decides how the system should be built.



\---



\## AI Coding Assistant



AI coding assistants are implementation partners.



Responsibilities include:



\- Reading official documentation

\- Generating production-ready code

\- Refactoring existing modules

\- Writing automated tests

\- Explaining generated code

\- Assisting during debugging



AI assistants must never introduce undocumented architecture or modify system design without approval.



\---



\# 6. AI Development Rules



Before generating code, every AI assistant must:



1\. Read the relevant documentation.

2\. Follow the documented architecture.

3\. Respect module boundaries.

4\. Avoid modifying unrelated files.

5\. Keep changes limited to the requested module.



If documentation is incomplete, implementation should stop until the documentation is updated.



\---



\# 7. Module Development Process



Every module follows the same development process.



```text

Requirement

&#x20;   │

&#x20;   ▼

Documentation

&#x20;   │

&#x20;   ▼

Architecture Review

&#x20;   │

&#x20;   ▼

Implementation

&#x20;   │

&#x20;   ▼

Unit Testing

&#x20;   │

&#x20;   ▼

Integration Testing

&#x20;   │

&#x20;   ▼

Code Review

&#x20;   │

&#x20;   ▼

Release

```



Each stage must be completed before moving to the next stage.



\---



\# 8. Documentation Standards



Every technical document should include:



\- Document ID

\- Title

\- Version

\- Status

\- Dependencies

\- Next Document

\- Purpose

\- Technical Specification

\- Acceptance Criteria



Documentation must remain synchronized with the implementation throughout the lifetime of the project.







\---



\# 9. Coding Standards



All source code must follow the official project standards.



Requirements:



\- Write clean and readable code.

\- Follow consistent naming conventions.

\- Keep functions small and focused.

\- Keep classes modular.

\- Avoid duplicated logic.

\- Prefer composition over inheritance when appropriate.

\- Write meaningful comments only when necessary.



Every module should remain easy to understand and maintain.



\---



\# 10. Git Workflow



Every implementation should follow a consistent Git workflow.



Recommended process:



```text

Documentation



↓



Implementation



↓



Local Testing



↓



Commit



↓



Review



↓



Merge

```



Commits should remain small and focused.



Each commit should represent a single logical change.



Large unrelated changes must be split into multiple commits.



\---



\# 11. Testing Workflow



Testing is mandatory before merging any module.



Testing stages:



\- Unit Testing

\- Integration Testing

\- API Testing

\- End-to-End Testing

\- Manual Verification



Every bug fix should include an appropriate regression test whenever practical.



No module should be considered complete without successful testing.



\---



\# 12. Bug Fix Policy



Bug fixes must follow a structured process.



```text

Bug Report



↓



Reproduce



↓



Identify Root Cause



↓



Implement Fix



↓



Run Tests



↓



Review



↓



Release

```



Temporary fixes should be avoided.



Every fix should address the root cause whenever possible.



Bug fixes must never introduce unrelated architectural changes.



\---



\# 13. Code Review Policy



Every completed module should be reviewed before being accepted.



The review should verify:



\- Documentation compliance

\- Architecture compliance

\- Code quality

\- Security

\- Performance

\- Maintainability

\- Test coverage



Code that violates documented architecture should not be accepted until corrected.







\---



\# 14. Release Workflow



Every release should follow the same process.



```text

Planning

&#x20;   │

&#x20;   ▼

Documentation Review

&#x20;   │

&#x20;   ▼

Implementation Complete

&#x20;   │

&#x20;   ▼

Testing Complete

&#x20;   │

&#x20;   ▼

Bug Fixes

&#x20;   │

&#x20;   ▼

Version Update

&#x20;   │

&#x20;   ▼

Release

```



A release must never skip documentation review or testing.



\---



\# 15. Change Management



All significant changes must be documented before implementation.



Examples include:



\- New Core functionality

\- New Engine

\- New Plugin API

\- Database schema changes

\- Authentication changes

\- Public API changes



Small bug fixes may not require new documentation unless they modify system behavior.



\---



\# 16. Module Completion Criteria



A module is considered complete only when all of the following conditions are satisfied:



\- Documentation is complete.

\- Implementation follows the documentation.

\- Automated tests pass.

\- Manual verification is complete.

\- Code review is complete.

\- No critical issues remain.



Completing implementation alone does not mark a module as finished.



\---



\# 17. Long-Term Maintenance



Favorite CMS is designed as a long-term platform.



Development decisions should prioritize:



\- Stability

\- Maintainability

\- Security

\- Backward compatibility

\- Documentation quality

\- Modular expansion



Short-term convenience must never compromise long-term architecture.



\---



\# 18. Workflow Principles



The following principles govern all development activities.



\- Documentation before implementation.

\- Architecture before coding.

\- Review before release.

\- Testing before deployment.

\- Stability before features.

\- Plugins before Core modifications.

\- Themes before customization.

\- Small incremental improvements over large risky changes.



These principles apply throughout the lifetime of the project.



\---



\## Acceptance Criteria



\- \[x] Development workflow defined.

\- \[x] Project roles documented.

\- \[x] AI development rules established.

\- \[x] Documentation workflow defined.

\- \[x] Git workflow documented.

\- \[x] Testing workflow documented.

\- \[x] Bug fix policy documented.

\- \[x] Release workflow documented.

\- \[x] Change management policy defined.

\- \[x] Module completion criteria documented.



\---



End of Document



Next Document:

007-core-engine.md

