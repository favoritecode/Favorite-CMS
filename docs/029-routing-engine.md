# Favorite CMS



Document ID: 029



Title: Routing Engine



Version: 1.0.0



Status: Draft



Author: Favorite CMS



Created: 2026-08-11



Last Updated: 2026-08-11



Depends On:



* 001-project-overview.md

* 002-system-architecture.md

* 003-project-principles.md

* 004-technology-stack.md

* 005-folder-structure.md

* 006-development-workflow.md

* 007-core-engine.md

* 008-extension-system.md

* 009-theme-engine.md

* 010-plugin-engine.md

* 011-rendering-engine.md

* 012-content-engine.md

* 013-media-engine.md

* 014-search-engine.md

* 015-user-engine.md

* 016-permission-engine.md

* 017-cache-engine.md

* 018-event-engine.md

* 019-queue-engine.md

* 020-notification-engine.md

* 021-settings-engine.md

* 022-menu-engine.md

* 023-seo-engine.md

* 024-update-engine.md

* 025-authentication-engine.md

* 026-api-engine.md

* 027-storage-engine.md

* 028-localization-engine.md



Next Document:

030-logging-engine.md



---



# 1. Purpose



This document defines the architecture, responsibilities, boundaries, and public interfaces of the Favorite CMS Routing Engine.



The Routing Engine provides controlled route registration and route resolution for supported application requests.



It determines which approved platform component owns a matched route and provides normalized route context for downstream processing.



The Routing Engine must remain separate from business logic, rendering logic, Authentication policy, Permission policy, and resource ownership.



---



# 2. Routing Engine Objectives



The Routing Engine must provide a foundation for:



* Route Registration

* Route Discovery

* Route Matching

* Route Parameter Resolution

* Route Ownership

* Route Priority

* Route Conflict Detection

* Route Context Creation

* Plugin Route Integration

* Theme Route Boundary

* API Route Coordination

* Rendering Handoff

* Route Security Boundaries

* Route Failure Handling



The exact router library or framework-specific routing implementation remains implementation-specific unless another approved specification defines one.



---



# 3. Route



A Route represents an approved mapping between an incoming request pattern and an owning platform operation.



A Route may define:



* Route identifier

* Path pattern

* Supported request method when applicable

* Route owner

* Route parameters

* Route type

* Authentication requirement

* Permission requirement

* Target operation

* Compatibility information

* Other explicitly supported route metadata



A Route must have a clear owner and responsibility.



---



# 4. Route Identifier



Every registered Route should have a stable identifier when required by the applicable contract.



A Route Identifier may be used for:



* Internal route references

* Menu destinations

* Redirect targets

* Plugin integration

* Rendering coordination

* Diagnostics

* Other approved platform behavior



A stable Route Identifier should not depend unnecessarily on visible URL text.



---



# 5. Route Owner



Every Route must have an explicit owner.



Possible Route owners include:



* Platform Engine

* API Engine

* Plugin

* Approved platform service

* Other explicitly supported component



The Route owner remains responsible for the operation associated with the Route.



The Routing Engine only coordinates route registration and resolution.



---



# 6. Route Registration



Routes must be registered through approved public interfaces.



Route registration may be performed by:



* Platform Engines

* API Engine

* Plugins

* Other approved platform components



Route registration must not require modification of private Routing Engine internals.



A Plugin must be able to register approved Routes without modifying Core source code.



---



# 7. Route Discovery



The Routing Engine must maintain a controlled registry of active Routes.



Route discovery may expose approved information such as:



* Route Identifier

* Path pattern

* Route owner

* Route type

* Supported request method

* Other explicitly approved metadata



Route discovery must not expose private implementation details or sensitive configuration.



---



# 8. Route Matching



The Routing Engine must match incoming request information against registered Routes.



The general route matching flow is:



Incoming Request

→ Normalize Routing Input

→ Evaluate Registered Routes

→ Resolve Matching Route

→ Resolve Route Parameters

→ Build Route Context

→ Handoff to Owning Component



Route matching must remain deterministic.



---



# 9. Route Parameters



A Route may define dynamic parameters.



Route parameters must be:



* Defined by the Route contract

* Parsed through approved routing logic

* Validated before use

* Included in normalized Route Context

* Passed only to supported downstream operations



Invalid Route parameters must produce controlled failure behavior.



---



# 10. Route Context



The Routing Engine must produce a normalized Route Context after successful resolution.



Route Context may include:



* Route Identifier

* Route owner

* Route type

* Matched path

* Route parameters

* Request method when applicable

* Authentication requirement

* Permission requirement

* Approved routing metadata

* Other explicitly supported context



Route Context must not contain unnecessary sensitive request data.



---



# 11. Routing Ownership Boundary



The Routing Engine owns:



* Route registration

* Route registry

* Route matching

* Route conflict detection

* Route parameter resolution

* Route Context creation



It does not own:



* Content business logic

* Media business logic

* Plugin business logic

* Authentication verification

* Permission decisions

* Rendering composition

* API response normalization

* User state

* Storage Resources



Routing must remain an infrastructure capability.



---



## Acceptance Criteria



* [x] Routing Engine purpose defined.

* [x] Routing Engine objectives defined.

* [x] Route defined.

* [x] Route Identifier defined.

* [x] Route Owner defined.

* [x] Route registration defined.

* [x] Route discovery defined.

* [x] Route matching defined.

* [x] Route parameters defined.

* [x] Route Context defined.

* [x] Routing ownership boundary defined.

* [x] Router implementation remains provider-neutral.



---









---



# 12. Route Resolution



The Routing Engine must resolve an incoming request to one approved Route.



The general resolution flow is:



Incoming Request

→ Normalize Routing Input

→ Match Registered Route

→ Validate Route Parameters

→ Resolve Route Owner

→ Build Route Context

→ Handoff to the Owning Component



Route resolution must be deterministic.



The same valid routing input must not unpredictably resolve to different unrelated Routes.



---



# 13. Route Priority



When multiple registered Routes could potentially match the same request, resolution priority must follow an explicit routing contract.



Priority may consider:



* Route specificity

* Route type

* Explicitly declared priority

* Registration rules

* Other approved routing metadata



The exact priority algorithm must be defined by the Routing implementation contract.



Codex must not invent undocumented priority behavior.



---



# 14. Route Conflict Detection



The Routing Engine must detect incompatible Route registrations.



A Route conflict may include:



* Same request method

* Same path pattern

* Same Route type

* Different unrelated owners

* Ambiguous matching behavior

* Incompatible Route definitions



A conflicting Route must not silently replace an existing Route.



The Routing Engine must return a controlled registration failure unless an approved override contract explicitly permits replacement.



---



# 15. Route Override Boundary



Route overriding must be explicitly supported.



A component must not override another component's Route merely because it registers later.



Any approved override contract must define:



* Original Route owner

* Override owner

* Eligible Route type

* Priority behavior

* Compatibility requirements

* Activation conditions



Core Routes must not be replaced by Plugins without an explicitly approved platform contract.



---



# 16. Static Route



A Static Route represents a Route with a fixed path pattern.



Conceptual example:



/about



A Static Route does not require dynamic path parameters.



Static Routes must still preserve:



* Route ownership

* Authentication requirements

* Permission requirements

* Route type

* Target operation



Static does not mean unrestricted.



---



# 17. Dynamic Route



A Dynamic Route contains one or more declared path parameters.



Conceptual example:



/content/{identifier}



Dynamic parameters must be explicitly declared in the Route contract.



The Routing Engine must not infer arbitrary parameters from unmatched path segments.



Dynamic Route values must be validated before downstream use.



---



# 18. Route Parameter Normalization



The Routing Engine may normalize declared Route parameters before placing them in Route Context.



Normalization may include:



* Parameter extraction

* Basic format validation

* Supported type conversion

* Approved canonicalization

* Other explicitly defined transport-level behavior



Business validation remains the responsibility of the owning Engine or Plugin.



---



# 19. Query Parameter Boundary



Query parameters may accompany a resolved Route.



The Routing Engine may make approved query information available to downstream request handling.



The Routing Engine must not automatically assign business meaning to arbitrary query parameters.



Query validation and business behavior must follow the applicable API, Engine, or Plugin contract.



---



# 20. Route Method Boundary



Routes may support one or more explicitly defined request methods.



The Routing Engine must reject unsupported methods for a resolved path according to the applicable routing contract.



A Route registered for one method must not automatically authorize unrelated methods.



Method handling must remain deterministic.



---



# 21. Route Type



A Route may belong to an approved Route Type.



Route Types may conceptually distinguish:



* Public presentation Route

* API Route

* Admin Route

* Plugin Route

* Other explicitly supported routing contexts



Route Type must not replace ownership or security requirements.



The exact Route Type registry must be explicitly defined before implementation.



---



# 22. Route Activation State



A registered Route may have an activation state when required.



A Route may become unavailable when:



* Its owning Plugin is disabled.

* Its owning component fails validation.

* Its dependency is unavailable.

* It is explicitly deactivated.

* Other approved conditions apply.



An inactive Route must not continue dispatching requests to an unavailable owner.



---



# 23. Route Registration Lifecycle



Route registration must follow the lifecycle of the owning component.



Conceptually:



Platform Bootstrap

→ Register Platform Routes

→ Register Engine Routes

→ Register Plugin Routes

→ Validate Route Registry

→ Activate Eligible Routes



When an owning component is disabled or unloaded, its Routes must be removed or deactivated according to the approved lifecycle contract.



---



## Acceptance Criteria



* [x] Route resolution defined.

* [x] Route priority boundary defined.

* [x] Route conflict detection defined.

* [x] Route override boundary defined.

* [x] Static Route defined.

* [x] Dynamic Route defined.

* [x] Route parameter normalization defined.

* [x] Query parameter boundary defined.

* [x] Route method boundary defined.

* [x] Route Type defined.

* [x] Route activation state defined.

* [x] Route registration lifecycle defined.



---









---



# 24. Routing and API Engine



The API Engine may register and consume API Routes through approved Routing Engine interfaces.



Preferred flow:



Incoming API Request

→ Routing Engine

→ Resolve API Route

→ Build Route Context

→ API Engine

→ Authentication and Permission checks

→ Owning Engine or Plugin



The Routing Engine owns route resolution.



The API Engine owns HTTP-facing API coordination.



The Routing Engine must not normalize API Responses or API Errors.



---



# 25. Routing and Rendering Engine



Public presentation Routes may hand off resolved Route Context to the Rendering Engine.



Preferred flow:



Incoming Request

→ Routing Engine

→ Resolve Presentation Route

→ Route Context

→ Owning Engine or Plugin

→ Render Context

→ Rendering Engine

→ Theme Output



The Routing Engine must not render Themes, Templates, Components, or Widgets.



---



# 26. Routing and Authentication Engine



A Route may declare that Authentication is required.



The Routing Engine may expose this requirement through Route Context.



The Authentication Engine remains responsible for identity verification.



Preferred boundary:



Resolved Route

→ Authentication Requirement

→ Authentication Engine

→ Authentication Context



The Routing Engine must not verify Credentials itself.



---



# 27. Routing and Permission Engine



A Route may declare one or more approved authorization requirements.



The Routing Engine may provide those requirements to downstream request handling.



The Permission Engine remains responsible for authorization decisions.



The Routing Engine must not:



* Approve protected access.

* Override Permission denial.

* Treat Route matching as authorization.

* Infer undocumented permissions from URL structure.



---



# 28. Routing and Plugin Engine



Plugins may register Plugin-owned Routes through approved public interfaces.



A Plugin Route must:



* Declare ownership.

* Use an approved Route contract.

* Preserve Plugin isolation.

* Define applicable security requirements.

* Follow route conflict rules.

* Follow Plugin lifecycle state.



A disabled or invalid Plugin must not leave active Routes that dispatch into unavailable Plugin code.



---



# 29. Plugin Route Isolation



Plugin Routes must remain isolated from unrelated Routes.



A Plugin must not:



* Silently replace another Plugin's Route.

* Silently replace a Core Route.

* Access another Plugin's private Route handler.

* Bypass Authentication requirements.

* Bypass Permission requirements.

* Modify Routing Engine internals.



A broken Plugin Route must not crash unrelated routing behavior.



---



# 30. Routing and Theme Engine



Themes may participate in presentation routing only through explicitly approved Theme contracts.



Themes primarily own presentation.



The Routing Engine owns Route resolution.



A Theme must not silently redefine platform or Plugin business Routes.



Theme switching must not corrupt the underlying Route registry.



Theme-specific presentation mapping may be supported only through approved Routing and Theme interfaces.



---



# 31. Routing and Menu Engine



The Menu Engine may reference stable Route Identifiers or approved destinations.



Preferred flow:



Menu Item

→ Route Identifier or Destination

→ Routing Engine

→ Resolve Approved Route

→ Generate or resolve navigation destination



The Menu Engine owns menu structure.



The Routing Engine owns route resolution.



Visible Menu labels must not be used as Route Identifiers.



---



# 32. Routing and Localization Engine



Routing may receive approved Locale context when localized routing behavior is explicitly supported.



The Localization Engine owns Locale resolution.



The Routing Engine must not infer Language or Locale from arbitrary path segments unless the routing contract explicitly defines that behavior.



If localized Routes are supported, the applicable Route contract must define:



* Locale-related path behavior

* Route identity behavior

* Fallback behavior

* Compatibility behavior



Codex must not invent localized URL rules.



---



# 33. Routing and Content Engine



Content-facing Routes may resolve to approved Content Engine operations.



The Routing Engine must not become the owner of Content lookup or Content lifecycle.



Preferred boundary:



Route Context

→ Content Engine

→ Resolve Content Resource

→ Rendering or API flow



A Route parameter such as a slug or identifier remains routing input until the Content Engine validates and resolves it as a Content Resource.



---



# 34. Routing and Search Engine



Search Routes may dispatch to the Search Engine through approved interfaces.



The Routing Engine may resolve:



* Search Route

* Route parameters

* Approved query input



The Search Engine remains responsible for:



* Search query interpretation

* Search filtering

* Search ordering

* Search ranking

* Search result construction



The Routing Engine must not implement Search logic.



---



# 35. Routing and Settings Engine



Routing configuration may be stored through the Settings Engine when explicitly supported.



Settings may include:



* Route-related platform configuration

* Approved redirect configuration

* Optional routing behavior

* Other explicitly defined routing settings



The Settings Engine owns configuration persistence.



The Routing Engine owns route registration and resolution behavior.



Invalid routing configuration must fail safely.



---



# 36. Routing and Cache Engine



The Cache Engine may cache approved routing metadata or derived route-resolution data.



Cacheable data may include:



* Route registry metadata

* Resolved stable route information

* Other explicitly approved routing data



Routing cache entries may require invalidation when:



* Routes are registered.

* Routes are removed.

* Plugin lifecycle changes.

* Route configuration changes.

* Approved overrides change.



The Routing Engine remains authoritative for active Route state.



---



# 37. Routing and Event Engine



The Routing Engine may publish approved Events for meaningful route lifecycle changes.



Conceptual occurrences may include:



* Route registered

* Route removed

* Route conflict detected

* Route activation changed

* Route resolution failed



Exact Event Names and payload contracts must be explicitly defined before implementation.



Routing Events must not expose sensitive request data unnecessarily.



---



## Acceptance Criteria



* [x] API Engine integration defined.

* [x] Rendering Engine integration defined.

* [x] Authentication Engine integration defined.

* [x] Permission Engine integration defined.

* [x] Plugin Engine integration defined.

* [x] Plugin Route isolation defined.

* [x] Theme Engine boundary defined.

* [x] Menu Engine integration defined.

* [x] Localization Engine integration defined.

* [x] Content Engine integration defined.

* [x] Search Engine integration defined.

* [x] Settings Engine integration defined.

* [x] Cache Engine integration defined.

* [x] Event Engine integration defined.



---









---



# 38. Routing Security Boundary



The Routing Engine is a security-sensitive infrastructure component.



Routing behavior must not allow request paths, parameters, or registration order to bypass:



* Authentication requirements

* Permission requirements

* Plugin isolation

* Route ownership

* Administrative boundaries

* API boundaries

* Protected resource boundaries



Matching a Route only determines where a request should be processed.



Route resolution does not grant authorization.



---



# 39. Routing Input Safety



Routing input must be treated as untrusted until normalized and validated.



Routing input may include:



* Request path

* Request method

* Declared path parameters

* Approved routing metadata

* Other explicitly supported routing information



Invalid routing input must not:



* Access arbitrary internal handlers

* Escape approved Route boundaries

* Invoke private Plugin operations

* Access protected filesystem paths

* Modify the Route registry

* Execute undocumented operations



---



# 40. Route Handler Boundary



A resolved Route must dispatch only to an approved target or public interface.



The Routing Engine must not allow arbitrary handler execution based on client-controlled values.



Preferred flow:



Resolved Route

→ Approved Route Target

→ Owning Engine or Plugin Public Interface



not:



Client-controlled value

→ Arbitrary internal callable



Route targets must originate from trusted registration.



---



# 41. Administrative Route Boundary



Administrative Routes must remain clearly separated from ordinary public presentation Routes.



Administrative Route registration must define applicable security requirements.



The Routing Engine must not treat an Admin Route as public merely because its URL can be resolved.



Authentication and Permission requirements remain controlled by their owning Engines.



---



# 42. Redirect Boundary



The Routing Engine may support controlled redirects when explicitly registered or configured.



A redirect definition may include:



* Source Route or path

* Approved destination

* Redirect behavior

* Activation state

* Compatibility information

* Other explicitly supported metadata



Redirect processing must not allow arbitrary unsafe destinations when the applicable contract restricts destination behavior.



The exact redirect model must be defined by an approved routing contract.



---



# 43. Redirect Resolution



When a redirect is supported, the Routing Engine must resolve it before dispatching an incompatible target operation.



Conceptually:



Incoming Request

→ Resolve Route or Redirect

→ Validate Redirect

→ Resolve Approved Destination

→ Return Redirect Result



Redirect behavior must remain deterministic.



The Routing Engine must avoid uncontrolled redirect loops.



---



# 44. Middleware Boundary



Request middleware may execute before or after Route resolution when supported by the platform implementation.



The Routing Engine may provide routing context to approved middleware.



Middleware must not silently change Route ownership or bypass security contracts.



The exact middleware execution model remains implementation-specific unless another approved specification defines it.



---



# 45. Routing Failure Handling



Possible Routing failures include:



* No matching Route

* Invalid Route parameters

* Unsupported request method

* Route conflict

* Inactive Route

* Route owner unavailable

* Invalid Route registration

* Invalid redirect

* Routing configuration failure

* Internal routing failure



Routing failures must produce controlled results.



Raw internal exceptions must not be exposed directly to public clients.



---



# 46. Route Not Found Boundary



When no registered Route matches the request, the Routing Engine must return a controlled unresolved result.



The downstream platform may convert that result into:



* Public not-found presentation

* API error response

* Administrative error response

* Other approved behavior



The Routing Engine must not fabricate a matching Route.



---



# 47. Route Owner Failure



A Route may remain structurally valid while its owner becomes unavailable.



Examples may include:



* Plugin disabled

* Plugin failed activation

* Engine unavailable

* Dependency unavailable

* Component removed



The Routing Engine must not continue dispatching into an unavailable owner.



The affected Route must fail safely or become inactive according to the applicable lifecycle contract.



---



# 48. Routing Failure Isolation



Routing failures must remain isolated from unrelated Routes and components.



For example:



Broken Plugin Route

→ Must not crash Core Routes.



Invalid Admin Route request

→ Must not affect public Routes.



Route conflict

→ Must not silently corrupt the active Route registry.



Invalid redirect

→ Must not break unrelated navigation.



One routing failure must not destabilize the entire application.



---



# 49. Routing Observability



The Routing Engine may expose controlled operational information such as:



* Route registered

* Route removed

* Route activated

* Route deactivated

* Route matched

* Route unresolved

* Route conflict detected

* Invalid Route registration

* Route owner unavailable

* Redirect resolved

* Routing failure occurred



Observability data must not unnecessarily expose:



* Authentication Credentials

* Sensitive query data

* Private User information

* Private Plugin state

* Protected configuration

* Other sensitive request data



---



# 50. Routing Cache Safety



If route metadata or route-resolution information is cached, the cache must preserve active Route state.



Routing cache entries must not cause:



* Removed Routes to remain active.

* Disabled Plugin Routes to remain active.

* Old Route ownership to persist after replacement.

* Incorrect redirect behavior.

* Cross-context Route leakage.



Applicable routing cache must be invalidated when Route state changes.



---



# 51. Routing Compatibility



Internal Routing Engine changes must preserve supported public routing contracts when non-breaking.



Existing:



* API integrations

* Theme integrations

* Plugin Routes

* Menu destinations

* Content Routes

* Search Routes

* Localization-aware integrations



must remain compatible with supported Routing Engine versions.



Breaking Route contract changes must follow the project's versioning and migration rules.



---



# 52. Route Stability



Stable Route Identifiers should remain compatible across non-breaking updates.



Visible URL changes and stable internal Route identity are separate concerns.



Where Route paths change, migration or redirect behavior must follow an explicitly approved contract.



Codex must not silently change public Route paths during unrelated implementation work.



---



# 53. Routing Engine Non-Goals



The Routing Engine does not own:



* Business logic

* Content resolution rules

* Media behavior

* Search behavior

* Authentication verification

* Permission policy

* API response normalization

* Theme rendering

* Plugin business logic

* User state

* Localization rules

* Cache storage

* Event delivery

* Storage Provider behavior



The Routing Engine is responsible for Route registration, matching, parameter resolution, ownership coordination, conflict detection, Route Context creation, lifecycle coordination, and routing failure safety.



---



## Acceptance Criteria



* [x] Routing security boundary defined.

* [x] Routing input safety defined.

* [x] Route handler boundary defined.

* [x] Administrative Route boundary defined.

* [x] Redirect boundary defined.

* [x] Redirect resolution defined.

* [x] Middleware boundary defined.

* [x] Routing failure handling defined.

* [x] Route-not-found boundary defined.

* [x] Route owner failure defined.

* [x] Routing failure isolation defined.

* [x] Routing observability defined.

* [x] Routing cache safety defined.

* [x] Routing compatibility defined.

* [x] Route stability defined.

* [x] Routing Engine non-goals defined.



---









---



# 54. Final Route Resolution Rules



The Routing Engine must resolve requests through approved routing contracts.



The general route-resolution flow is:



1\. Receive normalized routing input.

2\. Resolve the applicable request method and path.

3\. Match against active registered Routes.

4\. Detect invalid or ambiguous matches.

5\. Resolve declared Route parameters.

6\. Resolve the Route owner.

7\. Build normalized Route Context.

8\. Expose Authentication and Permission requirements.

9\. Handoff to the approved owning component.

10\. Return a controlled unresolved result when no valid Route exists.



Route resolution must remain deterministic and ownership-aware.



---



# 55. Route Contract



Every registered Route must follow an approved Route contract.



The contract must define:



* Route Identifier when applicable

* Route owner

* Route type

* Path pattern

* Supported request method or methods

* Declared Route parameters

* Authentication requirement

* Permission requirement

* Approved target operation

* Activation state

* Compatibility requirements

* Other explicitly supported routing metadata



Routes must not rely on undocumented registration behavior.



---



# 56. Route Ownership Contract



Every active Route must have one clearly resolved owner.



The Route owner is responsible for:



* Target operation

* Business behavior

* Domain validation

* Applicable dependencies

* Route-specific lifecycle behavior



The Routing Engine remains responsible for:



* Registration

* Matching

* Conflict detection

* Parameter resolution

* Route Context

* Route lifecycle coordination



Route ownership must not become ambiguous because multiple components use similar URL patterns.



---



# 57. Route Conflict Contract



Conflicting Route definitions must fail safely.



The Routing Engine must not silently resolve conflicts using:



* Registration timing

* Plugin load order

* Theme activation order

* Arbitrary implementation order

* Undocumented framework behavior



Where an approved override contract exists, the override must be explicit and deterministic.



Without an approved override contract, incompatible registrations must fail.



---



# 58. Plugin Routing Contract



Plugins may extend routing only through approved public interfaces.



A Plugin Route must:



* Declare ownership.

* Follow Route registration rules.

* Preserve Route isolation.

* Respect Authentication requirements.

* Respect Permission requirements.

* Follow Plugin lifecycle state.

* Use approved public targets.



A Plugin must not:



* Modify private Routing Engine internals.

* Silently replace Core Routes.

* Silently replace another Plugin's Routes.

* Dispatch to another Plugin's private handlers.

* Leave active Routes after becoming unavailable.

* Use routing behavior to bypass platform security.



---



# 59. Theme Routing Contract



Themes primarily control presentation.



Theme activation must not silently redefine platform business routing.



A Theme may participate in routing only through explicitly approved Theme and Routing contracts.



Theme switching must preserve:



* Stable Route ownership

* Plugin Route integrity

* API Route integrity

* Authentication boundaries

* Permission boundaries

* Menu destination integrity



Presentation changes must remain separate from business Route ownership.



---



# 60. API Routing Contract



API Routes must coordinate with the API Engine.



Preferred boundary:



Request

→ Routing Engine

→ API Route Context

→ API Engine

→ Authentication

→ Permission

→ Owning Engine or Plugin

→ API Response



The Routing Engine must not:



* Perform API business logic.

* Normalize API payloads.

* Generate API business errors.

* Replace API authorization behavior.



The API Engine remains responsible for HTTP-facing API coordination.



---



# 61. Rendering Routing Contract



Presentation Routes may hand off to the Rendering Engine after the applicable resource or operation is resolved.



Preferred boundary:



Request

→ Routing Engine

→ Route Context

→ Owning Engine or Plugin

→ Render Context

→ Rendering Engine

→ Theme Output



The Routing Engine must not:



* Select arbitrary Templates.

* Render Components.

* Render Widgets.

* Own Theme presentation.



Routing resolves destination.



Rendering composes presentation.



---



# 62. Authentication and Permission Routing Contract



A Route may declare security requirements.



The required boundary is:



Route Resolution

→ Authentication Requirement

→ Authentication Engine

→ Permission Requirement

→ Permission Engine

→ Approved Operation



The Routing Engine must never interpret:



Route matched

→ Access allowed



Route matching and authorization are separate operations.



---



# 63. Route Parameter Contract



Route parameters must originate from declared Route patterns.



The Routing Engine may perform transport-level normalization and validation.



The owning Engine or Plugin remains responsible for business validation.



For example:



Routing Engine

→ Confirms parameter exists and satisfies supported route structure.



Content Engine

→ Determines whether the identifier resolves to a valid Content Resource.



Route parameters must not be treated automatically as trusted business Resources.



---



# 64. Redirect Contract



Redirect behavior must remain explicit and controlled.



A redirect contract must define the applicable source and approved destination behavior.



Redirect resolution must:



* Validate redirect configuration.

* Avoid uncontrolled redirect loops.

* Preserve security boundaries.

* Return a controlled redirect result.

* Avoid inventing undocumented destinations.



Redirect configuration must not silently become arbitrary request forwarding.



---



# 65. Routing Security Contract



The Routing Engine must preserve infrastructure security boundaries.



It must prevent routing behavior from bypassing:



* Authentication

* Permission evaluation

* Admin boundaries

* API boundaries

* Plugin isolation

* Route ownership

* Protected operation boundaries



Client-controlled routing input must never directly select arbitrary private handlers.



---



# 66. Routing Failure Contract



Routing operations must fail safely.



A routing failure must not automatically:



* Crash Core.

* Crash the Admin environment.

* Crash the public site.

* Corrupt the Route registry.

* Activate disabled Plugin Routes.

* Replace valid Routes silently.

* Bypass Authentication.

* Bypass Permission rules.

* Execute arbitrary handlers.

* Expose private Plugin internals.

* Expose sensitive request information.



Controlled routing failures must be returned whenever possible.



---



# 67. Codex Implementation Rules



When implementing the Routing Engine, Codex must:



* Follow the frozen architecture from Documents 001–028.

* Follow the defined folder structure.

* Use approved public interfaces.

* Preserve stable Route ownership.

* Preserve API Engine boundaries.

* Preserve Rendering Engine boundaries.

* Preserve Authentication Engine boundaries.

* Preserve Permission Engine boundaries.

* Preserve Plugin isolation.

* Preserve Theme presentation boundaries.

* Preserve Content Engine ownership.

* Preserve Search Engine ownership.

* Preserve Menu Engine ownership.

* Preserve Localization Engine boundaries.

* Preserve Settings Engine boundaries.

* Preserve Cache Engine boundaries.

* Preserve Event Engine boundaries.

* Validate Route registrations.

* Detect conflicting Routes.

* Validate declared Route parameters.

* Build normalized Route Context.

* Keep Route matching deterministic.

* Deactivate or remove Routes whose owners become unavailable.

* Keep routing failures isolated.

* Treat client routing input as untrusted.

* Never allow arbitrary handler execution from client-controlled input.

* Never silently resolve Route conflicts based on registration order.

* Never silently replace Core Routes with Plugin Routes.

* Never allow disabled Plugins to retain active executable Routes.

* Never treat Route matching as authorization.

* Never infer undocumented Permissions from URL structure.

* Never invent undocumented localized URL behavior.

* Never invent undocumented Route priority rules.

* Never change public Route paths during unrelated implementation work.

* Never require one router library or framework-specific routing implementation as a permanent architectural dependency.



If an implementation detail is not defined by this document, Codex must not silently introduce a conflicting routing architecture.



---



# 68. Final Acceptance Criteria



* [x] Routing Engine purpose defined.

* [x] Routing Engine objectives defined.

* [x] Route defined.

* [x] Route Identifier defined.

* [x] Route Owner defined.

* [x] Route registration defined.

* [x] Route discovery defined.

* [x] Route matching defined.

* [x] Route parameters defined.

* [x] Route Context defined.

* [x] Routing ownership boundary defined.

* [x] Route resolution defined.

* [x] Route priority boundary defined.

* [x] Route conflict detection defined.

* [x] Route override boundary defined.

* [x] Static Route defined.

* [x] Dynamic Route defined.

* [x] Route parameter normalization defined.

* [x] Query parameter boundary defined.

* [x] Route method boundary defined.

* [x] Route Type defined.

* [x] Route activation state defined.

* [x] Route registration lifecycle defined.

* [x] API Engine integration defined.

* [x] Rendering Engine integration defined.

* [x] Authentication Engine integration defined.

* [x] Permission Engine integration defined.

* [x] Plugin Engine integration defined.

* [x] Plugin Route isolation defined.

* [x] Theme Engine boundary defined.

* [x] Menu Engine integration defined.

* [x] Localization Engine integration defined.

* [x] Content Engine integration defined.

* [x] Search Engine integration defined.

* [x] Settings Engine integration defined.

* [x] Cache Engine integration defined.

* [x] Event Engine integration defined.

* [x] Routing security boundary defined.

* [x] Routing input safety defined.

* [x] Route handler boundary defined.

* [x] Administrative Route boundary defined.

* [x] Redirect boundary defined.

* [x] Redirect resolution defined.

* [x] Middleware boundary defined.

* [x] Routing failure handling defined.

* [x] Route-not-found boundary defined.

* [x] Route owner failure defined.

* [x] Routing failure isolation defined.

* [x] Routing observability defined.

* [x] Routing cache safety defined.

* [x] Routing compatibility defined.

* [x] Route stability defined.

* [x] Route contract defined.

* [x] Route ownership contract defined.

* [x] Route conflict contract defined.

* [x] Plugin Routing contract defined.

* [x] Theme Routing contract defined.

* [x] API Routing contract defined.

* [x] Rendering Routing contract defined.

* [x] Authentication and Permission Routing contract defined.

* [x] Route Parameter contract defined.

* [x] Redirect contract defined.

* [x] Routing Security contract defined.

* [x] Routing Failure contract defined.

* [x] Codex implementation rules defined.



---



# 69. Document Status



This document defines the Routing Engine specification for Favorite CMS.



The Routing Engine must be implemented according to this document and the frozen architecture established by Documents 001–028.



The Routing Engine provides controlled Route registration, Route matching, Route ownership, Route parameter resolution, Route Context creation, conflict detection, lifecycle coordination, Plugin Route integration, API and Rendering handoff, redirect coordination, security boundaries, and routing failure isolation.



The Routing Engine must remain an infrastructure capability.



It must not become the owner of business logic, Content behavior, API response behavior, Theme rendering, Authentication verification, Permission policy, Plugin business logic, Search behavior, or Localization policy.



No specific routing library, router provider, external gateway, framework-specific router implementation, or routing service is required by this document unless another approved architecture specification explicitly defines one.



Any future breaking change to the Routing Engine must follow the project's versioning and migration rules.



---



End of Document



Next Document:



030-logging-engine.md

