# Favorite CMS



Document ID: 016



Title: Permission Engine



Version: 1.0.0



Status: Draft



Author: Favorite CMS



Created: 2026-08-11



Last Updated: 2026-08-11



Depends On:

- 001-project-overview.md

- 002-system-architecture.md

- 003-project-principles.md

- 004-technology-stack.md

- 005-folder-structure.md

- 006-development-workflow.md

- 007-core-engine.md

- 008-extension-system.md

- 009-theme-engine.md

- 010-plugin-engine.md

- 011-rendering-engine.md

- 012-content-engine.md

- 013-media-engine.md

- 014-search-engine.md

- 015-user-engine.md



Next Document:

017-cache-engine.md



---



# 1. Purpose



This document defines the architecture, responsibilities, boundaries, and public interfaces of the Favorite CMS Permission Engine.



The Permission Engine is responsible for evaluating whether an authenticated User or approved system context is allowed to perform an operation on a protected resource.



The Permission Engine must remain independent from Theme-specific presentation logic.



---



# 2. Permission Engine Objectives



The Permission Engine must provide a foundation for:



- Permission Definition

- Permission Evaluation

- Role-based Access Context

- Resource Access Decisions

- Action Authorization

- Permission-aware Engine Integration

- Plugin Permission Integration

- Controlled Authorization Failures



The exact permission storage and evaluation implementation remains behind the Permission Engine's public interfaces.



---



# 3. Permission



A Permission represents an approved authorization capability.



A Permission may describe whether a User or system context may perform a particular action.



A Permission must be evaluated against an approved authorization context.



The Permission Engine must not assume that a User is authorized merely because the User exists.



---



# 4. Authorization Context



An Authorization Context represents the information required to evaluate a permission decision.



The context may include:



- User identifier

- User role information

- Requested action

- Target resource

- Resource ownership information

- Other approved authorization metadata



The Permission Engine must use only information available through approved platform contracts.



---



# 5. Permission Decision



The Permission Engine must produce a normalized authorization decision.



A decision must identify whether the requested operation is:



- Allowed

- Denied



The exact internal evaluation mechanism is implementation-specific.



A denied operation must not be treated as successful by a consuming Engine.



---



# 6. Role Boundary



The User Engine may provide User role information.



The Permission Engine is responsible for evaluating the authorization implications of that role.



Therefore:



User Engine

→ User identity and role information



Permission Engine

→ Permission evaluation



The Permission Engine must not become the owner of User profile or User identity data.



---



# 7. Resource Access



The Permission Engine may evaluate access to protected resources owned by other Engines.



Examples may include:



- Content Resources

- Media Resources

- User Resources

- Plugin resources

- Other protected platform resources



The owning Engine remains responsible for the resource itself.



The Permission Engine provides the authorization decision.



---



# 8. Action Authorization



Permission evaluation must apply to an explicit requested action.



An action may represent operations such as:



- Read

- Create

- Update

- Delete

- Manage



The supported action set must be defined by the platform contract.



A consuming Engine must not assume authorization for an action that has not been approved.



---



# 9. Permission and Engine Boundary



The Permission Engine provides authorization decisions.



The responsible Engine performs the actual resource operation.



Therefore:



Permission Engine

→ Authorization decision



Content Engine

→ Content operation



Media Engine

→ Media operation



User Engine

→ User operation



The Permission Engine must not directly take ownership of another Engine's resources.



---



## Acceptance Criteria



- [x] Permission Engine purpose defined.

- [x] Permission Engine objectives defined.

- [x] Permission defined.

- [x] Authorization Context defined.

- [x] Permission Decision defined.

- [x] Role boundary defined.

- [x] Resource access boundary defined.

- [x] Action authorization defined.

- [x] Permission and Engine boundary defined.



---









---



# 10. Permission Evaluation



The Permission Engine must evaluate an authorization request against an approved Authorization Context.



An evaluation must consider, where applicable:



- User identity

- User role

- Requested action

- Target resource

- Resource ownership

- Applicable permission rules



The evaluation must return a normalized Permission Decision.



---



# 11. Role-Based Evaluation



A User role may be used as an input to permission evaluation.



The Permission Engine must not assume that a role automatically grants every possible action.



Role capabilities must be defined through the approved permission configuration.



The User Engine remains responsible for providing User role information.



---



# 12. Resource Ownership



Resource ownership may be considered during permission evaluation.



For example, an operation may depend on whether:



- The User owns the resource.

- The User has an approved role.

- The resource is publicly accessible.

- A specific permission has been granted.



The owning Engine remains responsible for determining and maintaining resource ownership data.



The Permission Engine consumes approved ownership information for authorization evaluation.



---



# 13. Permission Checks



A protected operation must perform the applicable Permission check before the operation is executed.



The general flow is:



User / System Context

→ Permission Request

→ Permission Engine

→ Permission Decision

→ Responsible Engine

→ Resource Operation



A denied Permission Decision must stop the protected operation.



---



# 14. Read Access



The Permission Engine may evaluate whether a User or system context may read a protected resource.



A read operation must not expose protected resource information when the Permission Decision is denied.



The responsible Engine remains responsible for returning the resource after authorization succeeds.



---



# 15. Create Access



The Permission Engine may evaluate whether a User or system context may create a resource.



A successful permission decision allows the responsible Engine to continue with resource creation.



Permission approval does not itself create the resource.



The owning Engine remains responsible for:



- Validation

- Creation

- Resource state

- Resource ownership



---



# 16. Update Access



The Permission Engine may evaluate whether a User or system context may update an existing resource.



The update flow must be:



1\. Resolve the target resource.

2\. Build the Authorization Context.

3\. Evaluate the required Permission.

4\. Continue only when access is allowed.

5\. Perform the update through the owning Engine.



A denied update must not modify the resource.



---



# 17. Delete Access



The Permission Engine may evaluate whether a User or system context may delete a resource.



Deletion must not occur when the Permission Decision is denied.



The Permission Engine does not perform the deletion itself.



The owning Engine remains responsible for the resource deletion lifecycle.



---



# 18. Permission and Public Resources



A resource may be publicly accessible according to its owning Engine's resource contract.



Public visibility must not be interpreted as permission to perform every action on that resource.



For example:



Public Read

≠

Update Permission



Public visibility and action authorization must remain separate concepts.



---



## Acceptance Criteria



- [x] Permission evaluation defined.

- [x] Role-based evaluation boundary defined.

- [x] Resource ownership boundary defined.

- [x] Permission check flow defined.

- [x] Read access defined.

- [x] Create access defined.

- [x] Update access defined.

- [x] Delete access defined.

- [x] Public resource boundary defined.



---









---



# 19. Permission Inheritance



The Permission Engine may evaluate permissions using approved role and resource relationships.



Permission inheritance must be explicitly defined by the platform configuration.



The Permission Engine must not assume inheritance rules that have not been registered or approved.



An inherited permission must remain traceable to its applicable authorization rule.



---



# 20. Permission Precedence



When multiple authorization rules apply, the Permission Engine must use the platform's defined precedence rules.



If no precedence rule exists, the implementation must not silently invent one that changes the security model.



A Permission Decision must remain deterministic for the same authorization context and permission configuration.



---



# 21. Ownership-Based Authorization



Resource ownership may be used as an authorization condition.



The general boundary is:



User Engine

→ Identifies the User.



Owning Engine

→ Identifies resource ownership.



Permission Engine

→ Evaluates authorization.



The Permission Engine must not independently create ownership information.



---



# 22. Permission for User Resources



User Resources may require authorization before protected operations are performed.



The User Engine remains responsible for User Resource lifecycle.



The Permission Engine evaluates whether the requested User operation is allowed.



A permission decision must not expose private User information when access is denied.



---



# 23. Permission for Content Resources



The Content Engine may request authorization decisions before protected Content operations.



The Permission Engine evaluates the request.



The Content Engine performs the operation only after the applicable authorization check succeeds.



The Permission Engine must not directly modify Content.



---



# 24. Permission for Media Resources



The Media Engine may request authorization decisions before protected Media operations.



The Permission Engine evaluates the authorization request.



The Media Engine remains responsible for:



- Media validation

- Media storage

- Media processing

- Media lifecycle



The Permission Engine only provides the authorization decision.



---



# 25. Permission for Plugin Resources



Plugins may use the Permission Engine for protected Plugin operations.



A Plugin must provide the required Authorization Context through the approved interface.



The Permission Engine must not allow a Plugin to bypass platform-level authorization rules.



A Plugin-specific permission must remain isolated from unrelated resources unless explicitly defined otherwise.



---



# 26. Permission and Search



The Search Engine may use Permission Decisions when resolving protected Search Results.



The Search Engine must not expose a protected resource solely because it exists in the Search Index.



The Search Engine remains responsible for Search behavior.



The Permission Engine remains responsible for authorization evaluation.



---



# 27. Permission Failure Handling



Authorization failures must be controlled and explicit.



Possible failures include:



- Missing User context

- Invalid Authorization Context

- Unknown Permission

- Invalid target resource

- Denied action

- Invalid authorization state



A failed authorization check must not be interpreted as permission granted.



---



# 28. Permission Failure Isolation



A failed Permission evaluation must not modify the target resource.



A failure affecting one authorization request must not corrupt unrelated authorization rules or resource states.



For example:



Denied Content update

→ Content remains unchanged.



Denied Media deletion

→ Media remains unchanged.



Denied User update

→ User remains unchanged.



---



## Acceptance Criteria



- [x] Permission inheritance boundary defined.

- [x] Permission precedence boundary defined.

- [x] Ownership-based authorization defined.

- [x] User Resource authorization defined.

- [x] Content authorization defined.

- [x] Media authorization defined.

- [x] Plugin authorization defined.

- [x] Search authorization boundary defined.

- [x] Permission failure handling defined.

- [x] Permission failure isolation defined.



---









---



# 29. Permission Security Boundary



The Permission Engine is a security boundary for protected operations.



Permission evaluation must occur before a protected operation is executed.



A consumer must not bypass the Permission Engine by directly performing a protected operation through a private implementation path.



---



# 30. Permission Result Integrity



A Permission Decision must represent the result of the applicable authorization evaluation.



The Permission Engine must not:



- Return Allow when the authorization check failed.

- Return Allow because a resource exists.

- Return Allow because a User is authenticated.

- Expose private authorization rules through normal result responses.



Authentication and authorization remain separate concerns.



---



# 31. Permission Request Isolation



Each Permission Request must be evaluated independently against its Authorization Context.



A successful authorization decision for one request must not automatically authorize an unrelated request.



For example:



Allowed Content Read

→ Does not automatically authorize Content Delete.



Allowed Media Read

→ Does not automatically authorize Media Update.



---



# 32. Permission Configuration



Permission rules must be maintained through an approved configuration or management interface.



The exact configuration storage mechanism is implementation-specific.



Permission configuration changes must not silently alter unrelated resources.



If the platform supports permission configuration updates, those updates must follow the platform's authorization and validation rules.



---



# 33. Plugin Permission Registration



A Plugin may register approved permissions for its own protected functionality.



Plugin permissions must remain within the Plugin's approved resource and action boundaries.



A Plugin must not register a permission that bypasses platform-level security boundaries.



Plugin permission registration must use public Permission Engine interfaces.



---



# 34. Permission and User Lifecycle



When a User becomes unavailable or their authorization context becomes invalid, the Permission Engine must not continue treating that invalid context as authorized.



Permission evaluation must use the current approved User context.



The Permission Engine must not own User lifecycle operations.



---



# 35. Permission and Resource Lifecycle



The Permission Engine must not modify the lifecycle of the resource being authorized.



For example:



Permission Engine

→ Determines whether deletion is allowed.



Content Engine

→ Performs Content deletion.



Media Engine

→ Performs Media deletion.



User Engine

→ Performs User operations.



The authorization decision and resource operation must remain separate.



---



# 36. Permission Compatibility



Changes to the internal Permission Engine implementation must preserve the public Permission contract when the change is non-breaking.



Existing authorization requests must remain compatible with supported versions of the Permission Engine.



Breaking authorization changes must follow the project's versioning and migration rules.



---



# 37. Permission Engine Non-Goals



The Permission Engine does not own:



- User profile data

- User authentication credentials

- Session storage

- Content lifecycle

- Media lifecycle

- Search indexing

- Theme rendering

- Plugin business logic

- Resource storage



Those responsibilities remain with their respective Engines or platform systems.



---



## Acceptance Criteria



- [x] Permission security boundary defined.

- [x] Permission result integrity defined.

- [x] Permission request isolation defined.

- [x] Permission configuration boundary defined.

- [x] Plugin permission registration defined.

- [x] User lifecycle boundary defined.

- [x] Resource lifecycle boundary defined.

- [x] Permission compatibility defined.

- [x] Permission Engine non-goals defined.



---









---



# 38. Final Permission Resolution Rules



The Permission Engine must resolve authorization requests through approved public interfaces.



The resolution process must:



1\. Validate the Authorization Context.

2\. Identify the requested action.

3\. Identify the target resource.

4\. Evaluate applicable authorization rules.

5\. Produce a normalized Permission Decision.



The Permission Engine must not perform the protected resource operation itself.



---



# 39. Permission Decision Contract



A Permission Decision must clearly represent whether the requested operation is allowed or denied.



A denied decision must prevent the consuming Engine from continuing the protected operation.



The Permission Engine must not silently convert an authorization failure into an allowed operation.



---



# 40. Authorization Context Contract



The Authorization Context must contain only information required for authorization evaluation.



It may include:



- User identifier

- Role information

- Requested action

- Target resource

- Ownership information

- Approved authorization metadata



Private implementation details must remain outside the public Permission contract.



---



# 41. Engine Integration Contract



Protected Engines must request authorization through the Permission Engine when authorization is required.



The general integration model is:



User / System Context

→ Authorization Request

→ Permission Engine

→ Permission Decision

→ Owning Engine

→ Resource Operation



The Permission Engine remains independent from the resource implementation.



---



# 42. Plugin Integration Contract



Plugins may use the Permission Engine through approved public interfaces.



A Plugin may define approved permissions for its own functionality.



Plugin authorization must not bypass platform-level authorization boundaries.



The Permission Engine must keep Plugin-specific authorization isolated unless an explicit platform contract defines otherwise.



---



# 43. Codex Implementation Rules



When implementing the Permission Engine, Codex must:



- Follow the frozen architecture from Documents 001–015.

- Follow the defined folder structure.

- Use approved public interfaces.

- Preserve User Engine ownership boundaries.

- Preserve Content Engine ownership boundaries.

- Preserve Media Engine ownership boundaries.

- Preserve Search Engine boundaries.

- Preserve Plugin boundaries.

- Preserve Theme and Rendering boundaries.

- Never treat authentication as automatic authorization.

- Never invent an undocumented role-permission matrix.

- Never bypass authorization checks through private implementation paths.

- Keep permission evaluation separate from resource operations.

- Keep permission configuration behind approved interfaces.



If an implementation detail is not defined by this document, Codex must not silently introduce a conflicting security architecture.



---



# 44. Final Acceptance Criteria



- [x] Permission definition established.

- [x] Authorization Context established.

- [x] Permission Decision established.

- [x] Role boundary established.

- [x] Resource ownership boundary established.

- [x] Action authorization established.

- [x] Read authorization established.

- [x] Create authorization established.

- [x] Update authorization established.

- [x] Delete authorization established.

- [x] Public resource boundary established.

- [x] Permission inheritance boundary established.

- [x] Permission precedence boundary established.

- [x] User authorization boundary established.

- [x] Content authorization boundary established.

- [x] Media authorization boundary established.

- [x] Plugin authorization boundary established.

- [x] Search authorization boundary established.

- [x] Permission failure handling established.

- [x] Permission failure isolation established.

- [x] Permission security boundary established.

- [x] Permission result integrity established.

- [x] Permission request isolation established.

- [x] Permission configuration boundary established.

- [x] User lifecycle boundary established.

- [x] Resource lifecycle boundary established.

- [x] Permission compatibility established.

- [x] Codex implementation rules established.



---



# 45. Document Status



This document defines the Permission Engine specification for Favorite CMS.



The Permission Engine must be implemented according to this document and the frozen architecture established by Documents 001–015.



This document defines generic Permission Engine responsibilities.



Business-specific authorization rules must remain within the approved Permission configuration or responsible Plugin/Engine.



No specific role-permission matrix, authorization provider, permission-storage technology, or external authorization service is required by this document unless a future architecture document explicitly defines one.



Any future breaking change to the Permission Engine must follow the project's versioning and migration rules.



---



End of Document



Next Document:



017-cache-engine.md

