# Favorite CMS



Document ID: 026



Title: API Engine



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



Next Document:

027-storage-engine.md



---



# 1. Purpose



This document defines the architecture, responsibilities, boundaries, and public interfaces of the Favorite CMS API Engine.



Favorite CMS follows an API-first architecture.



The API Engine provides the controlled interface between HTTP clients and approved Favorite CMS platform capabilities.



The API Engine receives supported API requests, validates them, resolves required request context, dispatches operations to the responsible Engine or Plugin, and returns normalized API responses.



The API Engine must remain an interface and coordination layer.



It must not become the owner of business logic or platform resources.



---



# 2. API Engine Objectives

The API Engine must provide a foundation for:

* API Route Contract Definition
* API Route Registration Coordination
* Request Validation
* Request Context Resolution
* Authentication Integration
* Permission Integration
* Engine Operation Dispatch
* Plugin API Integration
* Request Data Normalization
* Response Normalization
* Error Normalization
* API Versioning
* API Security
* API Failure Isolation
* Controlled API Extensibility

The API Engine owns API-specific HTTP coordination.

The Routing Engine owns the active Route registry, Route matching, Route conflict detection, Route parameter resolution, and Route Context creation.

The exact endpoint set is defined by the applicable Engine, Plugin, or approved platform contract.

---

# 3. API Architecture Boundary



The API Engine is an interface layer between external clients and platform capabilities.



The preferred architecture is:



Client

→ API Engine

→ Request Validation

→ Authentication Context Resolution

→ Permission Evaluation when required

→ Owning Engine or Plugin

→ Normalized Result

→ API Response



The API Engine must not use the following architecture:



Client

→ API Route

→ Embedded Business Logic

→ Private Engine Internals

→ Direct Storage Mutation



Business logic must remain inside the responsible Engine or Plugin.



---



# 4. API Route



An API Route represents an approved HTTP-accessible platform operation.



An API Route may define:



* HTTP method

* Route path

* Request contract

* Request parameters

* Authentication requirement

* Permission requirement

* Owning Engine or Plugin

* Response contract

* Error behavior



Every Route must have a clearly defined responsibility.



A Route must not become a container for unrelated business operations.



---



# 5. Route Registration

The API Engine may define API Route contracts and coordinate their registration through approved Routing Engine interfaces.

API Route definitions may originate from:

* Platform Engines
* Approved platform services
* Plugins
* Other explicitly supported components

The Routing Engine owns:

* Active Route registration
* Route registry
* Route matching
* Route conflict detection
* Route parameter resolution
* Route Context creation

The API Engine must not maintain a competing global Route registry.

API Route registration must not require modification of private API Engine or Routing Engine internals.

A Plugin must be able to expose approved API capabilities through the Plugin, API, and Routing public contracts without modifying Core source code.

---

# 6. API Request



An API Request represents incoming client data associated with an approved Route.



Request data may include:



* Path parameters

* Query parameters

* Request body

* Approved headers

* Authentication information

* Request metadata

* Other explicitly supported input



The API Engine must process only data required by the applicable Route contract.



Unexpected or unsupported input must not silently change platform behavior.



---



# 7. Request Validation



The API Engine must validate incoming API Requests before dispatching protected or state-changing operations.



Validation may include:



* Required fields

* Expected data types

* Allowed values

* Request body structure

* Path parameter validity

* Query parameter validity

* Required authentication state

* Other explicitly defined constraints



Invalid requests must return a controlled API error.



Invalid client input must not be forwarded blindly into Engine or Plugin internals.



---



# 8. Request Context



The API Engine must establish or receive a normalized Request Context for downstream operations.



The Request Context may include:



* Request identity

* Route information

* Authentication state

* User reference

* Locale when applicable

* Request metadata

* Approved client context

* Other explicitly supported contextual information



The Request Context must contain only information required by downstream contracts.



Raw Credentials must not be exposed through the general Request Context.



---



# 9. API Ownership Boundary



The API Engine owns HTTP-facing request and response coordination.



It does not own the resources manipulated through API operations.



Therefore:



Content Engine

→ Owns Content operations.



Media Engine

→ Owns Media operations.



User Engine

→ Owns User Resources.



Search Engine

→ Owns Search behavior.



Authentication Engine

→ Owns identity verification.



Permission Engine

→ Owns authorization decisions.



Settings Engine

→ Owns managed Settings.



Menu Engine

→ Owns navigation structure.



SEO Engine

→ Owns SEO metadata resolution.



Plugin

→ Owns Plugin business logic.



API Engine

→ Validates requests, dispatches approved operations, and builds normalized HTTP responses.



Creating an API endpoint must not transfer resource ownership or business responsibility to the API Engine.



---



# 10. Public Interface Rule



Engines and Plugins must expose API-accessible functionality through approved public contracts.



The API Engine must not:



* Call private Engine implementation details.

* Access private Plugin internals.

* Modify database records directly when an owning Engine contract exists.

* Bypass Permission checks.

* Bypass Authentication requirements.

* Duplicate business validation already owned by another Engine.



The API Engine may validate transport-level request structure.



The owning Engine or Plugin remains responsible for domain-level business validation.



---



## Acceptance Criteria



* [x] API Engine purpose defined.

* [x] API-first responsibility defined.

* [x] API Engine objectives defined.

* [x] API architecture boundary defined.

* [x] API Route defined.

* [x] API Route registration coordination defined.

* [x] API Request defined.

* [x] Request validation defined.

* [x] Request Context defined.

* [x] API ownership boundary defined.

* [x] Public interface rule defined.

* [x] Business logic separation defined.



---









---



# 11. Authentication Integration



The API Engine must integrate with the Authentication Engine through approved public interfaces.



When a Route requires authentication, the API Engine must:



1\. Resolve the incoming authentication information.

2\. Request Authentication Context resolution.

3\. Reject invalid or expired authentication state.

4\. Attach only the approved Authentication Context to the Request Context.

5\. Continue request processing only when the Route contract permits it.



The API Engine must not perform Credential verification itself.



---



# 12. Permission Integration



Protected API operations must use the Permission Engine for authorization decisions.



The preferred flow is:



API Request

→ Authentication Context

→ Permission Context

→ Permission Engine

→ Allowed or Denied

→ Owning Engine operation



The API Engine must not treat successful authentication as automatic authorization.



A protected Route must not bypass Permission evaluation when authorization is required.



---



# 13. Public API Access



Some API Routes may be explicitly public.



A public Route may accept unauthenticated requests when the applicable contract permits it.



Public access must still respect:



* Request validation

* Resource visibility

* Route constraints

* Rate or abuse controls when applicable

* Owning Engine rules



Public does not mean unrestricted internal access.



---



# 14. API Dispatch



After request validation and applicable security checks succeed, the API Engine must dispatch the request to the responsible public interface.



The general dispatch flow is:



Validated Request

→ Resolve Owning Engine or Plugin

→ Build Approved Operation Input

→ Call Public Interface

→ Receive Normalized Result

→ Build API Response



The API Engine must not dispatch directly to private implementation classes when a public contract exists.



---



# 15. Engine API Integration



Platform Engines may expose approved capabilities through the API Engine.



Examples may include:



* Content operations

* Media operations

* Search operations

* User operations

* Settings operations

* Menu operations

* Other explicitly approved Engine capabilities



The owning Engine remains responsible for business rules and resource state.



The API Engine handles transport-level coordination only.



---



# 16. Plugin API Integration

Plugins may define Plugin-owned API capabilities through approved Plugin and API contracts.

Applicable API Route definitions must be registered through approved Routing Engine interfaces.

A Plugin may:

* Define Plugin-owned API Route contracts.
* Define request contracts.
* Define response contracts.
* Use Authentication Context when approved.
* Use Permission evaluation when required.
* Call public platform Engine interfaces.

A Plugin must not:

* Modify API Engine internals.
* Modify Routing Engine internals.
* Maintain a competing global Route registry.
* Override unrelated Routes without an approved Routing contract.
* Access another Plugin's private API implementation.
* Bypass Authentication.
* Bypass Permission checks.
* Directly modify Core internals.

---

# 17. Route Ownership

Every API Route must have an explicit business or operation owner.

Possible API Route owners include:

* Platform Engine
* Approved platform service
* Plugin
* Other explicitly registered component

The Route owner remains responsible for:

* Business operation
* Domain validation
* Resource state
* Route-specific behavior
* Compatibility requirements

The Routing Engine remains responsible for active Route registration, matching, conflict detection, parameter resolution, and Route Context creation.

The API Engine remains responsible for HTTP-facing API coordination, request validation, dispatch coordination, response normalization, and error normalization.

Route ownership must not transfer Routing Engine responsibilities to the API Engine.

---

# 18. Route Conflict Handling

Two unrelated components must not silently register conflicting API Routes.

A Route conflict may involve:

* Same HTTP method
* Same route path
* Conflicting ownership
* Incompatible Route contract

Route conflict detection and registry-level conflict handling belong to the Routing Engine.

When the Routing Engine rejects a conflicting API Route, the API Engine must preserve and surface a controlled registration failure to the applicable component.

The API Engine must not silently replace an existing Route based on registration order.

The API Engine must not implement a separate conflict-resolution algorithm that competes with the Routing Engine.

---

# 19. Request Data Normalization



The API Engine may normalize transport-level request data before passing it to the owning component.



Normalization may include:



* Parsed path parameters

* Parsed query parameters

* Validated request body

* Approved header values

* Authentication Context

* Request metadata



Normalization must not alter business meaning without an explicit Route contract.



---



# 20. Domain Validation Boundary



Transport validation and business validation are separate responsibilities.



API Engine

→ Validates transport structure.



Owning Engine or Plugin

→ Validates business rules.



For example:



API Engine

→ Confirms required field exists and uses expected type.



Owning Engine

→ Determines whether that value is valid for the requested business operation.



The API Engine must not duplicate or replace domain validation owned by another component.



---



## Acceptance Criteria



* [x] Authentication integration defined.

* [x] Permission integration defined.

* [x] Public API access defined.

* [x] API dispatch defined.

* [x] Engine API integration defined.

* [x] Plugin API integration defined.

* [x] Route ownership defined.

* [x] Route conflict delegation defined.

* [x] Request data normalization defined.

* [x] Domain validation boundary defined.



---









---



# 21. API Response



The API Engine must return normalized responses for supported API operations.



An API Response may contain:



* Operation result

* Resource data

* Pagination data when applicable

* Approved metadata

* Error information

* Other explicitly supported response data



The response must follow the applicable Route contract.



The API Engine must not expose private Engine or Plugin implementation details.



---



# 22. Response Normalization



The API Engine must normalize results returned by Engines or Plugins into a consistent HTTP-facing structure.



Normalization may include:



* Success status

* Response payload

* Error payload

* Pagination metadata

* Request-related metadata

* Other approved response information



Normalization must preserve the business meaning of the owning component's result.



---



# 23. HTTP Status Boundary



The API Engine may map normalized operation results to appropriate HTTP status behavior.



The exact status mapping must follow the approved API contract.



The API Engine must not report:



Failed operation

→ As successful.



Unauthorized operation

→ As authorized.



Missing resource

→ As successfully resolved.



Invalid request

→ As valid input.



Status handling must remain deterministic.



---



# 24. API Error



An API Error represents a controlled failure returned through the API interface.



An API Error may describe:



* Request validation failure

* Authentication failure

* Permission denial

* Resource not found

* Business operation failure

* Route unavailable

* Plugin unavailable

* Internal controlled failure

* Other explicitly supported error categories



Errors must not expose sensitive internal implementation details.



---



# 25. Error Normalization



Errors from Engines, Plugins, Authentication, Permission, or other approved systems must be converted into normalized API errors.



The preferred flow is:



Internal Controlled Error

→ API Engine

→ Normalize Error

→ Select Approved HTTP Response

→ Return Safe Error Payload



The API Engine must not return raw internal exceptions directly to clients.



---



# 26. Validation Error Response



Request validation failures must produce controlled validation responses.



A validation response may identify:



* Invalid field

* Missing required field

* Unsupported value

* Invalid structure

* Other approved validation information



Validation responses must provide enough information for supported clients to correct the request without exposing internal implementation details.



---



# 27. Authentication Error Boundary



Authentication-related API failures must originate from the Authentication contract.



The API Engine may translate them into an approved API response.



The API Engine must not expose:



* Raw Credentials

* Sensitive Token values

* Private Session information

* Internal authentication secrets



Authentication failure must not be confused with Permission denial.



---



# 28. Permission Error Boundary



Authorization failures must originate from the Permission Engine or approved authorization contract.



The API Engine may return the applicable normalized API response.



The API Engine must not modify Permission rules to make a Route succeed.



Authentication success must not override a Permission denial.



---



# 29. Resource Error Boundary



Resource-related errors remain owned by the responsible Engine or Plugin.



Examples may include:



Content Engine

→ Content resource unavailable.



Media Engine

→ Media resource unavailable.



Plugin

→ Plugin resource unavailable.



API Engine

→ Converts the normalized resource failure into an approved API response.



The API Engine must not fabricate missing resources.



---



# 30. API Pagination



API Routes that expose collections may support pagination through an approved contract.



Pagination may include:



* Requested page or position

* Result limit

* Continuation information

* Total-result information when supported

* Other explicitly defined pagination metadata



The exact pagination model must be defined by the applicable API contract.



Codex must not assume one pagination model for every Route.



---



# 31. API Filtering



Collection Routes may support explicitly defined filtering.



Filters must be:



* Registered by the owning Engine or Plugin.

* Validated by the API Engine.

* Passed through approved operation input.

* Applied by the responsible resource owner.



The API Engine must not invent undocumented filters.



---



# 32. API Sorting



Collection Routes may support approved sorting behavior.



Sorting options must be explicitly defined by the applicable Route or resource contract.



The API Engine may validate requested sorting options.



The owning Engine or Plugin remains responsible for executing the sorting behavior.



Unsupported sorting requests must fail safely.



---



## Acceptance Criteria



* [x] API Response defined.

* [x] Response normalization defined.

* [x] HTTP status boundary defined.

* [x] API Error defined.

* [x] Error normalization defined.

* [x] Validation error response defined.

* [x] Authentication error boundary defined.

* [x] Permission error boundary defined.

* [x] Resource error boundary defined.

* [x] API pagination boundary defined.

* [x] API filtering boundary defined.

* [x] API sorting boundary defined.



---









---



# 33. API Versioning



The API Engine may support versioned public contracts.



API versioning must protect clients from unexpected breaking changes.



Versioning may apply to:



* Route structure

* Request contracts

* Response contracts

* Error contracts

* Authentication requirements

* Other explicitly defined API behavior



The exact versioning strategy must be defined by the approved API contract.



Codex must not invent undocumented versioning behavior.



---



# 34. Backward Compatibility



Non-breaking API changes should preserve compatibility with supported clients.



Examples may include:



* Adding optional response fields

* Adding new independent Routes

* Extending supported filters without changing existing behavior

* Other explicitly compatible changes



Breaking changes must follow the project's approved versioning and migration rules.



---



# 35. API Deprecation Boundary



An API Route or API behavior may be deprecated before removal when required.



Deprecation must be explicit.



A deprecation process may identify:



* Deprecated Route or behavior

* Replacement interface when available

* Applicable compatibility period

* Planned removal version when defined



The API Engine must not silently remove supported public contracts.



---



# 36. API Security Boundary



The API Engine is a security-sensitive public interface.



It must protect platform boundaries against:



* Invalid input

* Unauthorized access

* Authentication bypass

* Permission bypass

* Private implementation exposure

* Cross-User data leakage

* Cross-Plugin data leakage

* Unsupported resource access

* Other explicitly defined API threats



Security-sensitive operations must use the appropriate Authentication and Permission contracts.



---



# 37. Sensitive Response Data



API Responses must contain only data approved by the applicable Route contract.



Sensitive information must not be exposed unnecessarily.



The API Engine must not expose:



* Raw Credentials

* Sensitive Session or Token values

* Private configuration secrets

* Internal stack traces

* Private storage details

* Private Plugin internals

* Other protected implementation data



Response filtering must preserve the applicable ownership and visibility rules.



---



# 38. API Abuse Protection Boundary



The API Engine must support protection against abusive request behavior where required by the approved security architecture.



Protection may apply to:



* Excessive API requests

* Repeated invalid requests

* Repeated Authentication attempts

* Expensive public operations

* Other explicitly defined abuse conditions



The exact rate-limiting, throttling, blocking, or abuse-prevention implementation remains implementation-specific unless another approved specification defines it.



---



# 39. API and Cache Engine



The API Engine may participate in approved cache workflows.



Cache behavior may apply to eligible API responses or resolved data when explicitly supported.



The preferred boundary is:



API Request

→ Owning Engine or approved Cache path

→ Normalized Result

→ API Response



The Cache Engine remains responsible for cache storage, retrieval, and invalidation.



The API Engine must not become the authoritative cache store.



User-specific or protected API data must not leak across cache contexts.



---



# 40. API and Event Engine



API-triggered operations may result in approved Events when the owning Engine or Plugin defines such behavior.



The API Engine itself should not invent business Events simply because a Route was called.



Preferred flow:



API Request

→ Owning Engine operation

→ Business state changes

→ Owning Engine publishes approved Event



The Event Engine remains responsible for Event delivery.



---



# 41. API and Queue Engine



An API operation may submit approved deferred work through the owning Engine or Plugin.



The preferred boundary is:



API Request

→ Owning Engine or Plugin

→ Queue Job submitted when required

→ API receives normalized operation result



The API Engine must not place arbitrary business operations into the Queue without an approved Job contract.



---



# 42. API and Notification Engine



An API-triggered business operation may result in an approved Notification workflow.



The API Engine must not directly invent Notification business rules.



Preferred flow:



API Request

→ Owning Engine or Plugin

→ Approved business operation

→ Notification Engine invoked when defined



The Notification Engine remains responsible for Notification coordination and delivery.



---



# 43. API Observability



The API Engine may expose controlled operational information such as:



* Route requested

* Request validated

* Request rejected

* Authentication failure

* Permission denial

* Route dispatch completed

* API error returned

* Plugin Route unavailable

* Internal API failure



Operational information must not expose sensitive request or response data unnecessarily.



---



# 44. API Failure Handling



Possible API failures include:



* Route not found

* Invalid request

* Authentication failure

* Permission denial

* Owning Engine unavailable

* Plugin unavailable

* Business operation failure

* Response normalization failure

* Internal API failure



All failures must produce controlled behavior.



Raw internal exceptions must not be exposed directly to clients.



---



# 45. API Failure Isolation



API failures must remain isolated from unrelated platform components wherever possible.



For example:



Broken Plugin Route

→ Must not crash unrelated API Routes.



Invalid Content request

→ Must not corrupt Content.



Authentication failure

→ Must not affect another User.



Response normalization failure

→ Must not expose internal data.



A single API failure must not destabilize Core or unrelated Engines.



---



# 46. API Compatibility



Changes to the internal API Engine implementation must preserve supported public API contracts when the change is non-breaking.



Existing frontend clients, Plugins, Engines, and integrations must remain compatible with supported API versions.



Breaking API changes must follow the project's versioning and migration rules.



---



# 47. API Engine Non-Goals



The API Engine does not own:



* Content business logic

* Media business logic

* User identity

* Authentication verification logic

* Permission rules

* Search behavior

* Settings ownership

* Menu ownership

* SEO ownership

* Cache storage

* Event delivery

* Queue execution

* Notification delivery

* Plugin business logic

* Database ownership



The API Engine is responsible for HTTP-facing request validation, context resolution, dispatch coordination, response normalization, error normalization, security boundaries, and public API compatibility.



---



## Acceptance Criteria



* [x] API versioning defined.

* [x] Backward compatibility defined.

* [x] API deprecation boundary defined.

* [x] API security boundary defined.

* [x] Sensitive response-data rules defined.

* [x] API abuse-protection boundary defined.

* [x] Cache Engine integration defined.

* [x] Event Engine integration defined.

* [x] Queue Engine integration defined.

* [x] Notification Engine integration defined.

* [x] API observability defined.

* [x] API failure handling defined.

* [x] API failure isolation defined.

* [x] API compatibility defined.

* [x] API Engine non-goals defined.



---









---



# 48. Final API Resolution Rules



The API Engine must process API requests through approved public interfaces.



The general API request flow is:



1\. Receive the HTTP request.

2\. Receive the resolved API Route Context from the Routing Engine.

3\. Validate request structure.

4\. Normalize request data.

5\. Resolve Authentication Context when required.

6\. Evaluate Permission requirements when required.

7\. Resolve the owning Engine or Plugin.

8\. Dispatch the approved operation.

9\. Receive the normalized domain result.

10\. Normalize the API Response.

11\. Map controlled errors to the approved API error contract.

12\. Return the HTTP response.



The API Engine must not bypass ownership boundaries at any stage.



---



# 49. API Route Contract

Every API Route must follow an approved API Route contract.

The contract must define:

* Route owner
* HTTP method
* Route path
* Request structure
* Authentication requirements
* Permission requirements
* Transport validation requirements
* Domain operation
* Response contract
* Error contract
* Compatibility requirements

API-specific request and response behavior belongs to the API Engine contract.

Active Route registration, matching, parameter resolution, Route Context creation, and Route conflict behavior must follow the Routing Engine contract.

An API Route must not depend on undocumented API Engine or Routing Engine behavior.

---

# 50. Request Contract



Every supported API Request must follow the applicable Route contract.



The API Engine must:



* Accept only supported request input.

* Validate required transport structure.

* Normalize approved request data.

* Reject invalid input safely.

* Preserve Authentication and Permission boundaries.

* Forward only approved operation input to the owning component.



The API Engine must not convert invalid input into undocumented business behavior.



---



# 51. Response Contract



Every API operation must produce an approved HTTP-facing response.



The response contract may define:



* Success state

* Response payload

* Response metadata

* Pagination metadata when supported

* Error representation

* Applicable HTTP status behavior



Responses must contain only data approved for the applicable client context.



Private implementation details must remain hidden.



---



# 52. Error Contract



API errors must be normalized.



The API Engine must distinguish controlled error categories such as:



* Route unavailable

* Validation failure

* Authentication failure

* Permission denial

* Resource unavailable

* Business operation failure

* Plugin unavailable

* Internal controlled failure



The exact error representation must remain stable according to the supported API version.



Raw internal exceptions must not be returned directly to clients.



---



# 53. Authentication and Permission Contract



The API Engine must maintain the following security order when applicable:



Request

→ Authentication

→ Permission Evaluation

→ Business Operation



Authentication answers:



Who is making the request?



Permission evaluation answers:



Is that identity allowed to perform this operation?



The API Engine must never treat successful authentication as automatic authorization.



---



# 54. Engine API Contract



Platform Engines may expose approved functionality through API Routes.



The API Engine must call the owning Engine through public interfaces.



The owning Engine remains responsible for:



* Business logic

* Domain validation

* Resource state

* Resource lifecycle

* Business failure behavior



The API Engine remains responsible for HTTP-facing coordination.



---



# 55. Plugin API Contract



Plugins may expose approved API capabilities without modifying Core or API Engine internals.



A Plugin API integration must:



* Register through approved interfaces.

* Own its Route behavior.

* Define request and response contracts.

* Respect Authentication requirements.

* Respect Permission requirements.

* Preserve Plugin isolation.

* Use public Engine interfaces.



A Plugin API integration must not:



* Override unrelated Routes silently.

* Read another Plugin's private state.

* Modify Core internals.

* Bypass platform security boundaries.

* Expose protected data without approval.



---



# 56. API Versioning Contract



Breaking public API behavior must not be introduced silently.



Version-aware changes must preserve supported client compatibility according to the project's versioning rules.



Breaking changes may include changes to:



* Route structure

* Required request input

* Response structure

* Error structure

* Authentication behavior

* Permission requirements

* Removed supported behavior



Breaking API changes must follow explicit versioning and migration procedures.



---



# 57. API Security Contract



The API Engine must enforce public-interface safety.



It must prevent API operations from bypassing:



* Authentication

* Permission evaluation

* User isolation

* Plugin isolation

* Resource ownership

* Request validation

* Sensitive-data boundaries



The API Engine must not expose:



* Raw Credentials

* Sensitive Session or Token values

* Private configuration secrets

* Internal stack traces

* Private storage implementation details

* Private Engine internals

* Private Plugin internals



Security failures must default to controlled denial rather than uncontrolled access.



---



# 58. API Failure Contract



API processing must fail safely.



An API failure must not automatically:



* Corrupt Content.

* Corrupt Media.

* Corrupt User data.

* Modify Permission rules.

* Modify Authentication state incorrectly.

* Corrupt Plugin data.

* Expose protected information.

* Crash unrelated Routes.

* Crash unrelated Engines.

* Crash Core.

* Crash the Admin environment.

* Crash the public site.



A failed API operation must return a controlled result whenever possible.



---



# 59. Codex Implementation Rules

When implementing the API Engine, Codex must:

* Follow the frozen architecture from Documents 001–025.
* Follow the defined folder structure.
* Preserve the API-first architecture.
* Use approved public interfaces.
* Keep HTTP coordination separate from business logic.
* Preserve Routing Engine ownership of Route registry, matching, conflict detection, parameter resolution, and Route Context creation.
* Register API Route definitions through approved Routing Engine interfaces.
* Preserve Content Engine ownership.
* Preserve Media Engine ownership.
* Preserve User Engine ownership.
* Preserve Search Engine ownership.
* Preserve Authentication Engine boundaries.
* Preserve Permission Engine boundaries.
* Preserve Settings Engine boundaries.
* Preserve Menu Engine boundaries.
* Preserve SEO Engine boundaries.
* Preserve Cache Engine boundaries.
* Preserve Event Engine boundaries.
* Preserve Queue Engine boundaries.
* Preserve Notification Engine boundaries.
* Preserve Plugin isolation.
* Validate request structure before dispatch.
* Keep domain validation inside the owning Engine or Plugin.
* Normalize API Responses.
* Normalize API Errors.
* Never expose raw internal exceptions.
* Never expose raw Credentials or sensitive Token values.
* Never bypass Permission checks for protected Routes.
* Never treat Authentication success as unrestricted authorization.
* Never access private storage directly when an owning Engine public contract exists.
* Never invent undocumented API Routes.
* Never invent undocumented filters, sorting options, or pagination models.
* Never maintain a competing global Route registry inside the API Engine.
* Never implement Route matching or Route conflict resolution that competes with the Routing Engine.
* Never silently replace conflicting Routes.
* Never introduce breaking API behavior without versioning.
* Never hard-code an external API gateway, proxy provider, API management service, or third-party API platform as an architectural requirement unless another approved specification explicitly defines one.

If an implementation detail is not defined by this document, Codex must not silently introduce a conflicting API or Routing architecture.

---

# 60. Final Acceptance Criteria

* [x] API Engine purpose defined.
* [x] API-first architecture defined.
* [x] API architecture boundary defined.
* [x] API Route defined.
* [x] API Route registration coordination defined.
* [x] Routing Engine registry ownership preserved.
* [x] API Request defined.
* [x] Request validation defined.
* [x] Request Context defined.
* [x] Public-interface rule defined.
* [x] Authentication integration defined.
* [x] Permission integration defined.
* [x] Public API access defined.
* [x] API dispatch defined.
* [x] Engine API integration defined.
* [x] Plugin API integration defined.
* [x] Route ownership defined.
* [x] Route conflict delegation defined.
* [x] Request normalization defined.
* [x] Domain-validation boundary defined.
* [x] API Response defined.
* [x] Response normalization defined.
* [x] HTTP-status boundary defined.
* [x] API Error defined.
* [x] Error normalization defined.
* [x] Validation-error handling defined.
* [x] Authentication-error boundary defined.
* [x] Permission-error boundary defined.
* [x] Resource-error boundary defined.
* [x] Pagination boundary defined.
* [x] Filtering boundary defined.
* [x] Sorting boundary defined.
* [x] API versioning defined.
* [x] Backward compatibility defined.
* [x] API deprecation boundary defined.
* [x] API security boundary defined.
* [x] Sensitive-response rules defined.
* [x] API abuse-protection boundary defined.
* [x] Cache integration defined.
* [x] Event integration defined.
* [x] Queue integration defined.
* [x] Notification integration defined.
* [x] API observability defined.
* [x] API failure handling defined.
* [x] API failure isolation defined.
* [x] API compatibility defined.
* [x] Route contract defined.
* [x] Request contract defined.
* [x] Response contract defined.
* [x] Error contract defined.
* [x] Authentication and Permission contract defined.
* [x] Engine API contract defined.
* [x] Plugin API contract defined.
* [x] API versioning contract defined.
* [x] API security contract defined.
* [x] API failure contract defined.
* [x] Codex implementation rules defined.

---

# 61. Document Status

This document defines the API Engine specification for Favorite CMS.

The API Engine must be implemented according to this document and the frozen architecture established by Documents 001–025.

The API Engine provides controlled HTTP-facing request validation, context resolution, Authentication integration, Permission integration, operation dispatch, response normalization, error normalization, versioning, security, and public API compatibility.

The API Engine must remain an interface and HTTP coordination layer.

It does not own the global Route registry, Route matching, Route conflict detection, Route parameter resolution, or Route Context creation; those responsibilities belong to the Routing Engine.

It must not become the owner of business logic, resource state, Authentication policy, Permission policy, or Plugin business behavior.

No specific API gateway, proxy provider, API management platform, third-party API service, or external transport layer is required by this document unless a future architecture specification explicitly defines one.

Any future breaking change to the API Engine must follow the project's versioning and migration rules.

---

End of Document

Next Document:

027-storage-engine.md
