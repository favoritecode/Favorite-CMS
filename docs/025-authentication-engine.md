# Favorite CMS



Document ID: 025



Title: Authentication Engine



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



Next Document:

026-api-engine.md



---



# 1. Purpose



This document defines the architecture, responsibilities, boundaries, and public interfaces of the Favorite CMS Authentication Engine.



The Authentication Engine is responsible for verifying identity and establishing an authenticated platform context.



Authentication answers:



Who is the requester?



Authentication does not answer:



What is the requester allowed to do?



Authorization remains the responsibility of the Permission Engine.



---



# 2. Authentication Engine Objectives



The Authentication Engine must provide a foundation for:



* Authentication Request Handling

* Credential Verification

* Authentication Context

* Login

* Logout

* Session or Token Handling

* Authentication State Resolution

* User Engine Integration

* Permission Engine Integration

* Plugin Authentication Integration

* Authentication Failure Handling

* Security Boundary Enforcement



The exact authentication library, token library, cryptographic implementation, or external identity provider remains behind approved Authentication Engine interfaces unless explicitly defined by the project's technology or future architecture specifications.



---



# 3. Authentication



Authentication is the process of verifying that a requester is associated with a valid platform identity.



A successful authentication result may establish an authenticated User context.



A failed authentication attempt must not establish an authenticated identity.



Authentication must remain separate from authorization.



Therefore:



Authentication

→ Determines identity.



Permission Engine

→ Determines allowed actions.



---



# 4. Authentication Identity



An Authentication Identity represents the identity resolved during authentication.



The identity may reference:



* User Identifier

* Account state

* Authentication state

* Approved authentication metadata



The User Engine remains the source of truth for the User Resource.



The Authentication Engine must not duplicate User ownership.



---



# 5. Credential



A Credential represents approved information used to prove identity.



The exact supported Credential types must be explicitly defined by the Authentication contract.



Credential handling must follow platform security requirements.



Credentials must not be exposed through:



* Public APIs

* Rendering context

* Theme data

* Plugin data without explicit authorization

* Logs

* Diagnostics

* Events

* Notifications



Sensitive credential values must remain protected.



---



# 6. Authentication Request



An Authentication Request represents an attempt to establish an authenticated identity.



An Authentication Request may contain:



* Identity reference

* Approved Credential data

* Request context

* Approved authentication metadata



The request must contain only the information required for the applicable Authentication method.



---



# 7. Authentication Result



Every Authentication attempt must return a normalized Authentication Result.



The result may identify:



* Success or failure

* Resolved User Identifier when successful

* Authentication state

* Approved session or token reference

* Failure category when unsuccessful

* Approved diagnostic metadata



A failed authentication attempt must never be reported as successful.



---



# 8. Authentication Context



An Authentication Context represents the verified identity associated with the current request or approved session.



The context may contain:



* User Identifier

* Authentication state

* Authentication method reference

* Session or token context

* Approved security metadata



The Authentication Context must contain only the information required by downstream platform contracts.



It must not expose raw Credentials.



---



# 9. Authentication Ownership Boundary



The Authentication Engine owns identity verification and authenticated-context establishment.



It does not own User Resources or authorization policy.



Therefore:



User Engine

→ Owns User identity and account data.



Authentication Engine

→ Verifies identity and establishes authenticated context.



Permission Engine

→ Evaluates authorization.



Rendering Engine

→ Uses only approved resolved User or authentication context.



Plugin

→ Uses public Authentication and Permission interfaces.



Authentication success must not automatically grant unrestricted access to platform resources.



---



## Acceptance Criteria



* [x] Authentication Engine purpose defined.

* [x] Authentication Engine objectives defined.

* [x] Authentication defined.

* [x] Authentication Identity defined.

* [x] Credential defined.

* [x] Authentication Request defined.

* [x] Authentication Result defined.

* [x] Authentication Context defined.

* [x] Authentication ownership boundary defined.

* [x] Authentication and authorization separation defined.



---









---



# 10. Login



Login is the process of establishing an authenticated User context after successful identity verification.



The general Login flow is:



Authentication Request

→ Validate Request

→ Resolve User Identity

→ Verify Credential

→ Validate Account State

→ Create Authentication Context

→ Establish Session or Token Context

→ Return Authentication Result



A failed Login attempt must not create an authenticated context.



---



# 11. Login Validation



Before Login succeeds, the Authentication Engine must validate:



* Authentication Request structure

* Required identity information

* Required Credential information

* User existence when applicable

* Account state

* Credential verification result

* Applicable authentication method requirements



An invalid or failed verification must produce a controlled Authentication failure.



---



# 12. Account State Integration



The Authentication Engine must respect the User account state defined by the User Engine.



An existing identity must not automatically mean that Login is allowed.



Account state may affect authentication eligibility.



Examples may include approved states such as:



* Active

* Inactive

* Restricted



The exact behavior for each account state must be defined by the User and Authentication contracts.



The Authentication Engine must not invent undocumented account-state rules.



---



# 13. Session or Token Context



After successful authentication, the Authentication Engine may establish an approved Session or Token Context.



The context represents authenticated continuity across supported requests.



It must be associated with:



* Verified identity

* Authentication state

* Applicable lifetime information

* Approved security metadata



The exact implementation may use the technology defined by the approved platform stack, while remaining behind the Authentication Engine's public interfaces.



---



# 14. Authentication State Resolution



The Authentication Engine must provide a controlled way to resolve whether the current request has a valid authenticated identity.



The general flow is:



Incoming Request

→ Resolve Authentication Context

→ Validate Context

→ Resolve User Identity

→ Return Authenticated or Unauthenticated State



An invalid, missing, or expired authentication context must not be treated as authenticated.



---



# 15. Authentication Lifetime



Authentication continuity may have a defined lifetime.



When the applicable Session or Token Context is no longer valid, it must not continue to establish an authenticated identity.



Lifetime behavior must follow the approved Authentication contract.



The Authentication Engine must not silently extend authentication indefinitely unless explicitly supported.



---



# 16. Logout



Logout invalidates or ends the applicable authenticated context.



The general Logout flow is:



Logout Request

→ Resolve Authentication Context

→ Invalidate Applicable Context

→ Clear Supported Authentication State

→ Return Normalized Logout Result



Logout must not delete the User Resource.



Logout ends authentication continuity only.



---



# 17. Logout Failure



A Logout operation may fail because of:



* Invalid authentication context

* Already invalidated context

* Session or Token failure

* Internal authentication-state failure

* Other explicitly defined errors



Logout failure must return a controlled result.



A failure must not expose Credential or protected authentication information.



---



# 18. Reauthentication Boundary



Certain sensitive operations may require fresh identity verification even when an authenticated context already exists.



When reauthentication is required:



Existing Authentication Context

→ Identifies the User.



Reauthentication

→ Verifies identity again according to the approved security contract.



Permission Engine

→ Still determines whether the requested action is authorized.



Reauthentication must not be treated as automatic authorization.



---



## Acceptance Criteria



* [x] Login defined.

* [x] Login validation defined.

* [x] Account-state integration defined.

* [x] Session or Token Context defined.

* [x] Authentication state resolution defined.

* [x] Authentication lifetime defined.

* [x] Logout defined.

* [x] Logout failure defined.

* [x] Reauthentication boundary defined.

* [x] Authentication remains separate from authorization.



---









---



# 19. Authentication and User Engine



The Authentication Engine must integrate with the User Engine through approved public interfaces.



The User Engine remains responsible for:



* User identity records

* User profile data

* Account state

* User lifecycle

* Stable User references



The Authentication Engine may resolve the User required for identity verification.



It must not duplicate User ownership or maintain a conflicting User model.



---



# 20. Authentication and Permission Engine



Authentication and authorization must remain strictly separated.



The preferred flow is:



Incoming Request

→ Authentication Engine resolves identity

→ Authentication Context created

→ Permission Engine evaluates requested action

→ Owning Engine performs the operation



A successful Login must not automatically grant unrestricted access.



The Permission Engine remains responsible for authorization decisions.



---



# 21. Anonymous Context



A request without a valid authenticated identity must be treated as anonymous or unauthenticated according to the applicable platform contract.



Anonymous requests may still access public resources when permitted.



Anonymous state must not be treated as an authentication failure when authentication is not required for the requested public operation.



The Permission Engine and resource owner remain responsible for deciding what anonymous access is allowed.



---



# 22. Authentication and Request Lifecycle



The Authentication Engine may participate early in the request lifecycle so downstream systems can receive a normalized authentication state.



The preferred request flow is:



Incoming Request

→ Authentication Context Resolution

→ User Context Resolution when authenticated

→ Permission Evaluation when required

→ Route or Engine Operation

→ Response



Authentication processing must not bypass normal routing, Permission, or resource ownership boundaries.



---



# 23. Authentication and Rendering Engine



The Rendering Engine may receive approved Authentication Context information required for presentation decisions.



Examples may include:



* Whether the current request is authenticated

* Approved User reference

* Approved presentation-safe User information



The Rendering Engine must not receive raw Credentials.



Themes must not perform Credential verification.



Authentication logic must remain outside Theme presentation.



---



# 24. Authentication and Menu Engine



The Menu Engine may use approved authenticated User context when resolving User-aware navigation.



Example:



Authentication Engine

→ Resolves current User identity.



Permission Engine

→ Resolves applicable access.



Menu Engine

→ Resolves visible navigation.



Theme

→ Presents the resulting Menu.



Menu visibility must not become a replacement for actual authorization.



---



# 25. Authentication and Settings Engine



The Settings Engine may store approved Authentication-related configuration.



Possible configuration may include:



* Authentication behavior

* Session or token configuration

* Login-related platform options

* Other explicitly approved Authentication Settings



Sensitive Credential values must not be stored as ordinary public Settings.



The exact handling of sensitive authentication secrets must follow approved security contracts.



---



# 26. Authentication and Cache Engine



Authentication-sensitive data must be cached only when explicitly approved.



The Cache Engine must not allow authenticated User context to leak between Users.



Cache Keys and scopes involving authenticated data must preserve the required User or authentication context.



Authentication state changes may require invalidation of affected cached representations.



---



# 27. Authentication and Event Engine



The Authentication Engine may publish approved Events for meaningful authentication lifecycle occurrences.



Conceptual occurrences may include:



* Authentication succeeded

* Authentication failed

* Logout completed

* Authentication context invalidated



Exact Event Names must be explicitly defined before implementation.



Authentication Events must not expose raw Credentials or sensitive authentication material.



---



# 28. Authentication and Plugin Boundary



Plugins may integrate with Authentication only through approved public interfaces.



A Plugin may:



* Read approved Authentication Context.

* Request supported authentication operations.

* Register approved authentication integration when explicitly supported.

* React to approved Authentication Events.



A Plugin must not:



* Read raw Credentials without an explicit security contract.

* Modify Authentication Engine internals.

* Bypass User Engine ownership.

* Bypass Permission checks.

* Treat authenticated identity as unrestricted authorization.

* Create hidden authentication mechanisms outside approved platform interfaces.



---



## Acceptance Criteria



* [x] User Engine integration defined.

* [x] Permission Engine integration defined.

* [x] Anonymous context defined.

* [x] Request lifecycle integration defined.

* [x] Rendering Engine boundary defined.

* [x] Menu Engine integration defined.

* [x] Settings Engine integration defined.

* [x] Cache Engine integration defined.

* [x] Event Engine integration defined.

* [x] Plugin authentication boundary defined.



---









---



# 29. Authentication Security Boundary



The Authentication Engine is a security-sensitive platform component.



It must protect:



* Credentials

* Authentication Context

* Session or Token data

* Authentication configuration

* Account verification state

* Approved security metadata



Sensitive authentication data must not be exposed to unauthorized systems.



---



# 30. Credential Protection



Credentials must be handled through approved Authentication Engine interfaces.



The platform must not:



* Log raw Credentials.

* Expose raw Credentials through Events.

* Expose raw Credentials through Notifications.

* Expose raw Credentials to Themes.

* Expose raw Credentials through Rendering Context.

* Expose raw Credentials to unrelated Plugins.

* Store raw Credentials in public Settings.



Credential handling must follow the approved security and technology contracts.



---



# 31. Authentication Failure Handling



Authentication failures must return controlled results.



Possible failures may include:



* Invalid Authentication Request

* Unknown identity

* Invalid Credential

* Invalid Authentication Context

* Expired authentication state

* Restricted account state

* Internal authentication failure

* Unsupported authentication method



Failure responses must not expose unnecessary information that could reveal protected authentication details.



---



# 32. Authentication Failure Isolation



Authentication failure must remain isolated from unrelated platform resources.



For example:



Failed Login

→ Must not modify Content.



Invalid Session or Token

→ Must not corrupt User data.



Plugin authentication failure

→ Must not corrupt another Plugin.



Authentication Engine failure

→ Must not silently grant access.



A failed authentication path must default to an unauthenticated state when identity cannot be verified safely.



---



# 33. Authentication Context Invalidation



An Authentication Context may need to be invalidated when it is no longer trusted or valid.



Possible reasons may include:



* Logout

* Expiration

* Account state change

* Credential-related security action

* Explicit administrative invalidation

* Other approved security condition



Invalidation must prevent the affected context from continuing to establish authenticated identity.



---



# 34. Account State Change Handling



When User account state changes, affected Authentication Contexts may require reevaluation or invalidation.



Examples may include:



Active

→ Restricted



Active

→ Inactive



The exact invalidation behavior must follow the approved User and Authentication contracts.



The Authentication Engine must not invent undocumented account-state behavior.



---



# 35. Authentication Observability



The Authentication Engine may expose controlled operational information such as:



* Authentication attempt

* Authentication success

* Authentication failure

* Login completed

* Logout completed

* Context invalidated

* Authentication method unavailable

* Internal Authentication failure



Operational information must not expose:



* Raw Credentials

* Sensitive token values

* Private session values

* Protected secrets



---



# 36. Authentication Rate and Abuse Boundary



The Authentication Engine must support protection against abusive authentication behavior where required by the approved security architecture.



Such protection may apply to:



* Repeated failed Login attempts

* Excessive authentication requests

* Repeated invalid Credential submission

* Other explicitly defined abuse conditions



The exact throttling, rate-limit, lockout, or abuse-prevention mechanism remains implementation-specific unless defined by another approved specification.



Codex must not invent permanent account-locking rules without documentation.



---



# 37. Authentication Method Extensibility



The Authentication Engine may support multiple approved Authentication methods through public contracts.



Any additional Authentication method must:



* Register through approved interfaces.

* Follow the Authentication Result contract.

* Produce normalized Authentication Context.

* Preserve User Engine ownership.

* Preserve Permission Engine boundaries.

* Protect sensitive authentication data.



A new Authentication method must not require unrelated Engines to change their internal architecture.



---



# 38. External Identity Provider Boundary



The Authentication Engine may support external identity providers only through explicitly approved adapters or integration contracts.



An external identity provider must not become a direct dependency of unrelated Engines, Themes, or Plugins.



The Authentication Engine must normalize external identity results into the platform's approved Authentication Context.



No specific external identity provider is required by this document.



---



# 39. Authentication Compatibility



Changes to the internal Authentication Engine implementation must preserve the public Authentication contract when the change is non-breaking.



Existing User, Permission, Plugin, Rendering, Menu, Settings, Cache, and Event integrations must remain compatible with supported Authentication Engine versions.



Breaking changes must follow the project's versioning and migration rules.



---



# 40. Authentication Engine Non-Goals



The Authentication Engine does not own:



* User profile data

* User lifecycle

* Permission rules

* Content Resources

* Media Resources

* Theme presentation

* Menu authorization

* Plugin business logic

* Notification delivery

* Settings persistence internals

* Cache storage

* External identity-provider accounts



The Authentication Engine is responsible for identity verification, Login, Logout, Authentication Context, and authentication-state management.



---



## Acceptance Criteria



* [x] Authentication security boundary defined.

* [x] Credential protection defined.

* [x] Authentication failure handling defined.

* [x] Authentication failure isolation defined.

* [x] Authentication Context invalidation defined.

* [x] Account-state change handling defined.

* [x] Authentication observability defined.

* [x] Abuse-protection boundary defined.

* [x] Authentication method extensibility defined.

* [x] External identity-provider boundary defined.

* [x] Authentication compatibility defined.

* [x] Authentication Engine non-goals defined.



---









---



# 41. Final Authentication Resolution Rules



The Authentication Engine must resolve identity through approved public interfaces.



The general authentication flow is:



1\. Receive the Authentication Request.

2\. Validate the request structure.

3\. Resolve the applicable authentication method.

4\. Resolve the User identity when applicable.

5\. Verify the approved Credential or identity proof.

6\. Validate applicable User account state.

7\. Create a normalized Authentication Result.

8\. Establish an Authentication Context when successful.

9\. Establish supported Session or Token Context when required.

10\. Return authenticated or unauthenticated state to downstream platform systems.



A failed identity-verification step must not produce an authenticated state.



---



# 42. Authentication Contract



Every supported Authentication method must follow an approved Authentication contract.



The contract must define:



* Authentication method

* Required request structure

* Required identity information

* Required Credential or identity proof

* Validation requirements

* User resolution requirements

* Authentication Result structure

* Authentication Context requirements

* Lifetime behavior when applicable

* Invalidation behavior

* Security requirements

* Compatibility requirements



Consumers must not depend on undocumented Authentication behavior.



---



# 43. Login Contract



Login must establish authenticated identity only after successful verification.



The Login contract must ensure that:



* Required input is validated.

* Credentials are verified.

* User account state is evaluated.

* Authentication Context is created only after successful verification.

* Session or Token Context is established only when supported and valid.

* Failed Login attempts return controlled failure results.



Login success does not grant unrestricted platform access.



Authorization remains the responsibility of the Permission Engine.



---



# 44. Logout Contract



Logout must invalidate the applicable authenticated context according to the supported Authentication contract.



Logout must:



* Resolve the applicable Authentication Context.

* Invalidate the supported Session or Token Context.

* Prevent the invalidated context from continuing to authenticate requests.

* Return a normalized result.



Logout must not:



* Delete the User Resource.

* Delete User-owned Content.

* Modify User permissions.

* Modify unrelated Sessions or Tokens without an approved contract.



---



# 45. Authentication Context Contract



An Authentication Context must contain only approved information required to represent verified identity.



It may include:



* User Identifier

* Authentication state

* Authentication method reference

* Session or Token context

* Approved security metadata



It must not include raw Credentials.



Downstream Engines and Plugins must consume Authentication Context only through approved interfaces.



---



# 46. Authentication and Authorization Contract



Authentication and authorization are separate platform responsibilities.



The required boundary is:



Authentication Engine

→ Determines verified identity.



Permission Engine

→ Determines allowed action.



Owning Engine

→ Executes the protected operation.



Therefore:



Authenticated User

→ Is not automatically authorized.



Unauthenticated User

→ May still access explicitly public resources.



Authentication state alone must never replace Permission evaluation where authorization is required.



---



# 47. Credential Security Contract



Credential processing must remain within approved security boundaries.



Credentials must not be exposed through:



* Theme resources

* Rendering Context

* Public APIs unless explicitly required by the Authentication endpoint

* Events

* Notifications

* Logs

* Diagnostics

* Cache entries

* Plugin interfaces without an explicit security contract



Credential verification implementation must remain behind approved Authentication Engine interfaces.



---



# 48. Session or Token Security Contract



Session or Token Context must be treated as sensitive authentication state.



The Authentication Engine must ensure that:



* Invalid contexts are rejected.

* Expired contexts are rejected.

* Invalidated contexts are rejected.

* Contexts remain associated with the correct authenticated identity.

* Sensitive values are not exposed unnecessarily.

* Authentication state does not leak between Users.



The exact Session or Token implementation must remain behind the approved Authentication contract.



---



# 49. Plugin Authentication Contract



Plugins may integrate with Authentication through public interfaces only.



A Plugin may:



* Read approved Authentication Context.

* Request supported Authentication operations.

* Register approved authentication integration when supported.

* React to approved Authentication Events.



A Plugin must not:



* Modify Authentication Engine internals.

* Bypass User Engine ownership.

* Bypass Permission Engine authorization.

* Treat authentication success as unrestricted access.

* Read raw Credentials without an explicit approved contract.

* Store hidden independent authentication state that conflicts with platform Authentication Context.

* Expose sensitive Authentication information through Plugin output.



---



# 50. Authentication Failure Contract



Authentication processing must fail safely.



An Authentication failure must not automatically:



* Authenticate an unknown identity.

* Grant protected access.

* Corrupt User data.

* Modify Permission rules.

* Corrupt Content or Media.

* Corrupt unrelated Plugins.

* Expose raw Credentials.

* Expose sensitive Session or Token data.

* Crash the public site.

* Crash the Admin environment.



When identity cannot be verified safely, the request must remain unauthenticated.



---



# 51. Codex Implementation Rules



When implementing the Authentication Engine, Codex must:



* Follow the frozen architecture from Documents 001–024.

* Follow the defined folder structure.

* Use approved public interfaces.

* Preserve User Engine ownership.

* Preserve Permission Engine authorization boundaries.

* Preserve Settings Engine boundaries.

* Preserve Cache Engine boundaries.

* Preserve Event Engine boundaries.

* Preserve Menu Engine boundaries.

* Preserve Rendering Engine boundaries.

* Preserve Plugin isolation.

* Keep Authentication separate from authorization.

* Keep raw Credentials out of Rendering, Theme, Event, Notification, logging, and diagnostics contexts.

* Normalize Authentication Result and Authentication Context.

* Treat invalid, expired, or invalidated authentication state as unauthenticated.

* Respect User account state.

* Keep Session or Token implementation behind approved interfaces.

* Never invent undocumented account-locking rules.

* Never invent undocumented authentication methods.

* Never invent undocumented Credential types.

* Never silently grant Permission based only on successful authentication.

* Never expose sensitive authentication material to unrelated Plugins.

* Never hard-code a specific external identity provider as an architectural requirement unless another approved specification explicitly defines one.



If an implementation detail is not defined by this document, Codex must not silently introduce a conflicting Authentication architecture.



---



# 52. Final Acceptance Criteria



* [x] Authentication Engine purpose defined.

* [x] Authentication defined.

* [x] Authentication Identity defined.

* [x] Credential defined.

* [x] Authentication Request defined.

* [x] Authentication Result defined.

* [x] Authentication Context defined.

* [x] Login defined.

* [x] Login validation defined.

* [x] Account-state integration defined.

* [x] Session or Token Context defined.

* [x] Authentication-state resolution defined.

* [x] Authentication lifetime defined.

* [x] Logout defined.

* [x] Logout failure defined.

* [x] Reauthentication boundary defined.

* [x] User Engine integration defined.

* [x] Permission Engine integration defined.

* [x] Anonymous context defined.

* [x] Request lifecycle integration defined.

* [x] Rendering Engine boundary defined.

* [x] Menu Engine integration defined.

* [x] Settings Engine integration defined.

* [x] Cache Engine integration defined.

* [x] Event Engine integration defined.

* [x] Plugin authentication boundary defined.

* [x] Authentication security boundary defined.

* [x] Credential protection defined.

* [x] Authentication failure handling defined.

* [x] Authentication failure isolation defined.

* [x] Authentication Context invalidation defined.

* [x] Account-state change handling defined.

* [x] Authentication observability defined.

* [x] Abuse-protection boundary defined.

* [x] Authentication-method extensibility defined.

* [x] External identity-provider boundary defined.

* [x] Authentication compatibility defined.

* [x] Authentication and authorization contract defined.

* [x] Credential security contract defined.

* [x] Session or Token security contract defined.

* [x] Plugin Authentication contract defined.

* [x] Authentication failure contract defined.

* [x] Codex implementation rules defined.



---



# 53. Document Status



This document defines the Authentication Engine specification for Favorite CMS.



The Authentication Engine must be implemented according to this document and the frozen architecture established by Documents 001–024.



The Authentication Engine provides controlled identity verification, Login, Logout, Authentication Context resolution, Session or Token Context management, authentication-state validation, and authentication failure handling.



The Authentication Engine must remain separate from:



* User ownership

* Permission evaluation

* Content ownership

* Media ownership

* Theme presentation

* Rendering composition

* Menu authorization

* Plugin business logic



Authentication establishes identity.



Authorization determines allowed actions.



No specific external identity provider, authentication service, token library, session provider, cryptographic library, or external authentication platform is required by this document unless another approved architecture specification explicitly defines one.



Any future breaking change to the Authentication Engine must follow the project's versioning and migration rules.



---



End of Document



Next Document:



026-api-engine.md

