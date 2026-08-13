# Favorite CMS



Document ID: 028



Title: Localization Engine



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



Next Document:

029-routing-engine.md



---



# 1. Purpose



This document defines the architecture, responsibilities, boundaries, and public interfaces of the Favorite CMS Localization Engine.



The Localization Engine provides controlled language and locale resolution for platform interfaces, Themes, Plugins, and other approved components.



It must provide a consistent way to resolve localized text and locale-aware presentation without requiring unrelated components to implement independent localization systems.



The Localization Engine must remain separate from Content ownership and Theme presentation ownership.



---



# 2. Localization Engine Objectives



The Localization Engine must provide a foundation for:



* Language Registration

* Locale Registration

* Active Locale Resolution

* Translation Resource Registration

* Translation Key Resolution

* Translation Fallback

* Theme Translation Integration

* Plugin Translation Integration

* User Locale Preferences

* Request Locale Resolution

* Locale-aware Rendering Context

* Translation Validation

* Localization Cache Integration

* Localization Failure Handling



The exact translation library or external localization provider must remain implementation-specific unless another approved specification defines one.



---



# 3. Language



A Language represents an approved human language available to the platform.



A Language may include:



* Stable identifier

* Display name

* Native display name

* Associated locale information

* Direction information when required

* Availability state

* Other explicitly supported metadata



Language metadata must be registered through approved localization interfaces.



---



# 4. Locale



A Locale represents an approved regional or language-specific presentation context.



A Locale may influence:



* Language selection

* Translation selection

* Number presentation

* Date and time presentation

* Other explicitly defined locale-aware formatting



The Localization Engine must not assume that one Language always maps to only one Locale.



---



# 5. Locale Identifier



Every registered Locale must have a stable identifier.



The identifier must be suitable for use through public platform contracts.



Consumers must not depend on undocumented internal localization implementation details.



Locale identifiers must be validated before becoming active platform context.



---



# 6. Active Locale



The Active Locale represents the locale selected for the current supported context.



An Active Locale may be resolved from approved sources such as:



* Request context

* Authenticated User preference

* Explicit client selection

* Site configuration

* Platform default



The exact resolution precedence must be explicitly defined by the applicable localization configuration.



Codex must not invent additional precedence rules.



---



# 7. Default Locale



Favorite CMS must support an approved Default Locale.



The Default Locale acts as a controlled fallback when no more specific supported Locale can be resolved.



The Default Locale must be configured through approved Settings or platform configuration.



A missing optional translation must not automatically make the entire application unavailable.



---



# 8. Translation Resource



A Translation Resource contains localized values registered for an approved component or namespace.



Translation Resources may be provided by:



* Platform Engines

* Plugins

* Themes

* Other explicitly supported components



A Translation Resource must remain associated with its owning component or approved namespace.



---



# 9. Translation Key



A Translation Key is a stable identifier used to resolve localized text.



Preferred architecture:



Component

→ Translation Key

→ Localization Engine

→ Active Locale

→ Translation Resource

→ Resolved Value



Components should not scatter duplicated hard-coded localized text when an approved Translation Key exists.



---



# 10. Translation Ownership



Translation ownership must remain explicit.



Platform Engine

→ Owns translations for its platform-facing messages.



Plugin

→ Owns translations for Plugin-specific functionality.



Theme

→ Owns translations for Theme-specific presentation.



Localization Engine

→ Owns registration, locale resolution, translation lookup, and fallback coordination.



The Localization Engine must not rewrite business meaning or presentation copy owned by another component.



---



# 11. Localization Boundary



The Localization Engine coordinates localization.



It does not own:



* Content Resources

* Media Resources

* User identity

* Authentication

* Permission policy

* Theme layouts

* Plugin business logic

* SEO business rules

* Menu structure

* Storage Resources



Localization must remain a supporting platform capability rather than a replacement for resource ownership.



---



## Acceptance Criteria



* [x] Localization Engine purpose defined.

* [x] Localization Engine objectives defined.

* [x] Language defined.

* [x] Locale defined.

* [x] Locale Identifier defined.

* [x] Active Locale defined.

* [x] Default Locale defined.

* [x] Translation Resource defined.

* [x] Translation Key defined.

* [x] Translation ownership defined.

* [x] Localization boundary defined.

* [x] Provider and library independence preserved.



---









---



# 12. Locale Resolution



The Localization Engine must resolve the Active Locale through approved platform inputs.



Locale resolution may consider:



* Explicit request locale

* Authenticated User preference

* Approved client preference

* Site configuration

* Platform Default Locale



The exact precedence must be defined by configuration or another approved contract.



The Localization Engine must not guess unsupported Locale values.



---



# 13. Request Locale Integration



The API Engine or request-handling layer may provide approved locale information through the Request Context.



Preferred flow:



Incoming Request

→ Request Context

→ Localization Engine

→ Active Locale

→ Downstream Engines, Plugins, or Rendering



Raw request data must not become trusted locale state without validation.



---



# 14. User Locale Preference



The User Engine may associate an approved Locale preference with a User.



The Localization Engine may use that preference during Active Locale resolution.



The User Engine owns User preference data.



The Localization Engine owns Locale resolution behavior.



A missing User preference must fall back according to the approved Locale resolution contract.



---



# 15. Locale Validation



Before a Locale becomes active, the Localization Engine must verify that it is registered and supported.



Validation may include:



* Locale identifier format

* Locale registration state

* Availability state

* Applicable component support

* Other explicitly defined constraints



Unsupported Locale values must produce controlled fallback or controlled failure according to the applicable contract.



---



# 16. Translation Registration



Approved components may register Translation Resources through public localization interfaces.



Registration must define:



* Resource owner

* Locale

* Namespace or equivalent ownership boundary

* Translation entries

* Compatibility information when applicable



A component must not silently overwrite another component's private Translation Resource.



---



# 17. Translation Namespace



Translation Resources should use explicit ownership boundaries.



A namespace may identify:



* Platform Engine

* Plugin

* Theme

* Other approved component



Preferred conceptual structure:



Owner

→ Namespace

→ Locale

→ Translation Key

→ Translation Value



The exact internal storage format remains implementation-specific.



---



# 18. Translation Resolution



Translation resolution must use the Active Locale and approved Translation Resource ownership.



Preferred flow:



Translation Request

→ Resolve Owner or Namespace

→ Resolve Active Locale

→ Find Translation Key

→ Return Localized Value

→ Apply Approved Fallback when required



The Localization Engine must not return unrelated component translations merely because the same key name exists elsewhere.



---



# 19. Translation Fallback



The Localization Engine must support controlled fallback when a Translation Key is unavailable for the Active Locale.



Fallback may include:



* Approved fallback Locale

* Platform Default Locale

* Approved source value

* Other explicitly configured fallback



The exact fallback order must be defined by configuration or component contract.



Codex must not invent fallback chains.



---



# 20. Missing Translation



A missing optional Translation should not crash the platform.



The Localization Engine must return a controlled result.



The system may:



* Apply an approved fallback.

* Return a safe unresolved result.

* Record a controlled diagnostic.

* Use other explicitly defined behavior.



A missing Translation must not expose internal implementation details.



---



# 21. Translation Value Boundary



A Translation Value represents localized presentation text or other explicitly supported localized presentation data.



Translation Values must not be used as hidden business configuration.



Business rules, permissions, resource identifiers, or workflow decisions must not depend on human-readable Translation Values when stable internal identifiers are available.



---



# 22. Translation Key Stability



Translation Keys should remain stable across non-breaking updates.



Changing visible text must not require changing a stable Translation Key.



Plugins and Themes should depend on approved Translation Keys rather than copied platform strings.



Breaking Translation contract changes must follow applicable versioning rules.



---



## Acceptance Criteria



* [x] Locale resolution defined.

* [x] Request Locale integration defined.

* [x] User Locale preference boundary defined.

* [x] Locale validation defined.

* [x] Translation registration defined.

* [x] Translation namespace defined.

* [x] Translation resolution defined.

* [x] Translation fallback defined.

* [x] Missing Translation behavior defined.

* [x] Translation Value boundary defined.

* [x] Translation Key stability defined.



---









---



# 23. Localization and Rendering Engine



The Rendering Engine may consume the Active Locale and resolved Translation Values through approved localization interfaces.



Preferred flow:



Request

→ Active Locale

→ Rendering Context

→ Theme or Plugin presentation

→ Localization Engine

→ Resolved Translation

→ Rendered Output



The Rendering Engine must not become the owner of Translation Resources.



---



# 24. Localization and Theme Engine



Themes may provide Theme-specific Translation Resources.



A Theme may:



* Register Theme-owned Translation Keys.

* Provide supported localized presentation text.

* Consume platform and Plugin Translation Keys through approved interfaces.

* Adapt presentation for locale-aware output.



A Theme must not:



* Modify platform Translation Resources directly.

* Modify Plugin-owned Translation Resources directly.

* Replace business identifiers with translated strings.

* Require Core modification for localization.



Theme localization must remain presentation-focused.



---



# 25. Theme Translation Override Boundary



A Theme may override presentation resources only where an approved Theme override contract permits it.



Translation override behavior must remain explicit.



A Theme must not silently replace unrelated platform or Plugin Translation Resources.



Where localization overrides are supported, ownership and precedence must be deterministic.



The exact override precedence must be defined by the applicable Theme or Localization contract.



---



# 26. Localization and Plugin Engine



Plugins may register Plugin-owned Translation Resources.



A Plugin may:



* Register supported Locales.

* Register Plugin-specific Translation Keys.

* Resolve localized values through the Localization Engine.

* Use the Active Locale.

* Provide localized Admin or public presentation text.



A Plugin must not:



* Modify Localization Engine internals.

* Override unrelated Plugin translations.

* Depend on private localization implementation.

* Bypass Translation ownership boundaries.



---



# 27. Plugin Translation Isolation



Plugin Translation Resources must remain isolated by ownership or namespace.



For example:



Plugin A Translation Key

→ Must not resolve from Plugin B private Translation Resource unless explicitly shared.



Plugin B update

→ Must not silently replace Plugin A translations.



Broken Plugin Translation Resource

→ Must not crash unrelated localization behavior.



Localization isolation must remain intact across installed Plugins.



---



# 28. Localization and Settings Engine



Localization configuration may be managed through the Settings Engine.



Settings may include:



* Default Locale

* Enabled Locales

* Locale-related platform preferences

* Other explicitly approved localization configuration



The Settings Engine owns configuration persistence.



The Localization Engine owns localization resolution behavior.



Invalid localization configuration must fail safely.



---



# 29. Localization and Menu Engine



The Menu Engine may use Translation Keys or localized labels where supported.



The Menu Engine remains responsible for:



* Menu structure

* Menu hierarchy

* Menu destination

* Menu visibility



The Localization Engine remains responsible for resolving localized presentation values.



A translated Menu label must not become the authoritative Menu Identifier.



---



# 30. Localization and SEO Engine



The SEO Engine may consume locale-aware presentation values when explicitly supported.



Possible localized SEO data may include:



* Title

* Description

* Other approved presentation metadata



The SEO Engine remains responsible for SEO metadata resolution.



The Localization Engine remains responsible for language and Translation resolution.



Localization must not invent SEO business rules.



---



# 31. Localization and Notification Engine



Notifications may use Localization services when localized delivery content is supported.



Preferred flow:



Notification Context

→ Resolve Recipient Locale

→ Resolve Approved Translation Resources

→ Notification Engine

→ Delivery Adapter



The Notification Engine owns Notification behavior.



The Localization Engine owns Translation resolution.



The exact Notification localization contract must be explicitly defined before implementation.



---



# 32. Localization and Search Engine



The Search Engine may receive Locale context when search behavior explicitly supports localization.



The Localization Engine does not own:



* Search ranking

* Search indexing

* Search filtering

* Search result relevance



If locale-aware search behavior is required, it must be defined by the Search Engine contract.



The Localization Engine must not invent locale-specific ranking rules.



---



# 33. Localization and Cache Engine



The Cache Engine may cache approved localization data.



Cacheable localization data may include:



* Registered Locale metadata

* Translation Resource resolution

* Translation lookup results

* Other explicitly approved derived localization data



Localization cache entries may require invalidation when:



* Translation Resources change.

* Enabled Locales change.

* Default Locale changes.

* Localization configuration changes.



The Localization Engine remains authoritative for localization behavior.



---



# 34. Localization and Event Engine



The Localization Engine may publish approved Events for meaningful localization changes.



Conceptual occurrences may include:



* Locale registered

* Locale configuration changed

* Translation Resource registered

* Translation Resource updated



Exact Event Names and payload contracts must be defined explicitly before implementation.



Localization Events must not expose sensitive configuration or unrelated private component data.



---



## Acceptance Criteria



* [x] Rendering Engine integration defined.

* [x] Theme Engine integration defined.

* [x] Theme Translation override boundary defined.

* [x] Plugin Engine integration defined.

* [x] Plugin Translation isolation defined.

* [x] Settings Engine integration defined.

* [x] Menu Engine integration defined.

* [x] SEO Engine integration defined.

* [x] Notification Engine integration defined.

* [x] Search Engine boundary defined.

* [x] Cache Engine integration defined.

* [x] Event Engine integration defined.



---









---



# 35. Localization Security Boundary



The Localization Engine must preserve component ownership and application security boundaries.



Localization operations must not expose:



* Private User data

* Authentication Credentials

* Permission internals

* Sensitive Settings

* Private Plugin configuration

* Internal stack traces

* Other protected platform data



Translation Resources must contain only data appropriate for their intended presentation context.



---



# 36. Localization Input Safety



Locale identifiers, Translation Keys, namespaces, and related localization input must be validated before use.



Invalid localization input must not:



* Access arbitrary files

* Access unrelated namespaces

* Access another Plugin's private resources

* Modify protected Translation Resources

* Alter application configuration unexpectedly



The Localization Engine must treat externally supplied locale data as untrusted until validated.



---



# 37. Translation Resource Integrity



Translation Resources must preserve ownership and structural integrity.



The Localization Engine must safely handle:



* Invalid Translation Resource structure

* Duplicate registrations

* Invalid Locale identifiers

* Invalid Translation Keys

* Conflicting ownership

* Missing required metadata

* Unsupported values



An invalid Translation Resource must not corrupt previously valid localization data.



---



# 38. Translation Conflict Handling



Conflicting Translation registrations must not be resolved silently when ownership is ambiguous.



A conflict may include:



* Same namespace and Translation Key

* Same Locale

* Different unrelated owners

* Incompatible resource definitions



The Localization Engine must return a controlled registration failure unless an approved override contract explicitly permits the operation.



---



# 39. Localization Failure Handling



Possible Localization failures include:



* Unsupported Locale

* Missing Translation Key

* Invalid Translation Resource

* Translation registration failure

* Namespace conflict

* Invalid localization configuration

* Localization cache failure

* Component Translation Resource unavailable

* Internal localization failure



Failures must produce controlled behavior.



The Localization Engine must not expose raw internal exceptions to public consumers.



---



# 40. Localization Failure Isolation



Localization failures must remain isolated from unrelated components.



For example:



Broken Plugin Translation Resource

→ Must not break platform translations.



Broken Theme Translation Resource

→ Must not crash Core.



Missing optional Translation

→ Must not crash the public site.



Invalid User Locale preference

→ Must not corrupt the User Resource.



Localization failure isolation must preserve a usable fallback path where an approved fallback exists.



---



# 41. Localization Fallback Safety



Fallback behavior must remain deterministic.



Fallback must not silently:



* Cross unrelated namespaces

* Use another Plugin's private translation

* Change business meaning

* Override Permission behavior

* Replace stable identifiers

* Modify stored Content



A fallback affects presentation resolution only unless another approved contract explicitly defines otherwise.



---



# 42. Localization Cache Safety



Cached localization results must preserve Locale, namespace, and ownership context.



A cached value for one Locale must not be incorrectly reused for another Locale.



A cached Plugin translation must not leak into another Plugin namespace.



Cache invalidation must occur when applicable Translation Resources or localization configuration changes.



---



# 43. Localization Observability



The Localization Engine may expose controlled operational information such as:



* Locale resolved

* Unsupported Locale requested

* Translation Resource registered

* Translation Resource rejected

* Translation Key unresolved

* Fallback applied

* Namespace conflict detected

* Localization configuration invalid

* Localization failure occurred



Operational information must not unnecessarily expose private User data or protected component information.



---



# 44. Localization Compatibility



Internal changes to the Localization Engine must preserve supported public localization contracts when non-breaking.



Existing:



* Platform Engines

* Themes

* Plugins

* Rendering integrations

* User preferences

* Menu integrations

* Notification integrations



must remain compatible with supported Localization Engine versions.



Breaking localization contract changes must follow the project's versioning and migration rules.



---



# 45. Translation Resource Updates



Updating Translation Resources must preserve stable ownership and Translation Key contracts where possible.



A Translation Resource update may change:



* Visible wording

* Localized presentation text

* Supported Locale coverage

* Other compatible presentation data



A non-breaking wording update should not require changing stable Translation Keys.



Removing or renaming supported Translation Keys may be a breaking change.



---



# 46. Localization Provider Independence



The Localization Engine must not require one specific localization library, Translation file format, external Translation service, or localization provider as a permanent architectural dependency.



Implementation details may change while preserving the public Localization contract.



Themes and Plugins must interact with localization through approved platform interfaces rather than provider-specific libraries when a platform abstraction exists.



---



# 47. Localization Engine Non-Goals



The Localization Engine does not own:



* Content translation workflows

* Automatic machine translation

* Translation marketplace behavior

* Editorial translation approval

* User identity

* Authentication policy

* Permission rules

* Theme layouts

* Plugin business logic

* SEO strategy

* Menu structure

* Notification delivery

* Search ranking

* Storage Provider behavior



Such capabilities may be implemented by other Engines, Plugins, or future approved integrations.



The Localization Engine is responsible for Locale registration, Active Locale resolution, Translation Resource registration, Translation lookup, fallback coordination, ownership isolation, and localization safety.



---



## Acceptance Criteria



* [x] Localization security boundary defined.

* [x] Localization input safety defined.

* [x] Translation Resource integrity defined.

* [x] Translation conflict handling defined.

* [x] Localization failure handling defined.

* [x] Localization failure isolation defined.

* [x] Fallback safety defined.

* [x] Localization cache safety defined.

* [x] Localization observability defined.

* [x] Localization compatibility defined.

* [x] Translation Resource update behavior defined.

* [x] Provider independence defined.

* [x] Localization Engine non-goals defined.



---









---



# 48. Final Localization Resolution Rules



The Localization Engine must resolve localization through approved public interfaces.



The general localization flow is:



1\. Receive the localization request or localization-aware context.

2\. Resolve the applicable component or namespace.

3\. Resolve the Active Locale.

4\. Validate Locale support.

5\. Resolve the requested Translation Key.

6\. Apply the approved fallback contract when required.

7\. Return the normalized localized value.

8\. Preserve ownership and namespace boundaries.



Localization resolution must remain deterministic.



---



# 49. Locale Resolution Contract



Active Locale resolution must follow an explicitly approved precedence.



The contract may consider:



* Explicit request Locale

* Authenticated User preference

* Approved client preference

* Site-level configuration

* Platform Default Locale



The exact order must be defined by configuration or another approved contract.



The Localization Engine must not invent hidden precedence rules.



---



# 50. Translation Resource Contract



Every Translation Resource must define:



* Resource owner

* Namespace or equivalent ownership boundary

* Supported Locale

* Translation Keys

* Translation Values

* Compatibility information when applicable



Translation Resources must be registered through approved public interfaces.



One component must not silently modify another component's private Translation Resource.



---



# 51. Translation Resolution Contract



Translation requests must resolve through stable Translation Keys.



Preferred flow:



Owner or Namespace

→ Translation Key

→ Active Locale

→ Translation Resource

→ Localized Value



Translation Values must not replace stable internal identifiers.



Visible text may change without requiring unnecessary changes to stable Translation Keys.



---



# 52. Fallback Contract



Translation fallback must be explicit and deterministic.



An approved fallback contract may include:



* Component-defined fallback Locale

* Platform Default Locale

* Approved source value

* Other explicitly configured fallback



Fallback must preserve:



* Component ownership

* Namespace boundaries

* Business meaning

* Permission boundaries

* Resource integrity



The Localization Engine must not search unrelated Translation Resources to find a matching key.



---



# 53. Theme Localization Contract



Themes may provide and consume localization through approved Theme and Localization interfaces.



Theme localization must remain presentation-focused.



A Theme may:



* Register Theme-specific Translation Resources.

* Resolve platform Translation Keys.

* Resolve Plugin Translation Keys when publicly available.

* Adapt layout presentation to Locale context.



A Theme must not:



* Modify Core localization internals.

* Modify private Plugin Translation Resources.

* Change business logic through translated strings.

* Make protected decisions based on visible Translation Values.



---



# 54. Plugin Localization Contract



Plugins may register and resolve Plugin-specific localization through approved interfaces.



A Plugin must:



* Preserve namespace ownership.

* Register supported Translation Resources explicitly.

* Use stable Translation Keys.

* Respect the Active Locale contract.

* Handle missing optional Translations safely.



A Plugin must not:



* Override another Plugin's private namespace.

* Bypass Localization Engine isolation.

* Depend on private localization implementation.

* Use Translation Values as authorization or business identifiers.



---



# 55. User Locale Contract



User Locale preference is User-owned data.



The User Engine remains responsible for storing and managing User preference data.



The Localization Engine may consume the approved Locale preference during resolution.



An invalid or unsupported User Locale must not corrupt the User Resource.



The Localization Engine must follow the approved fallback behavior.



---



# 56. Rendering Localization Contract



The Rendering Engine may receive approved Locale context and localized values.



Preferred boundary:



Request Context

→ Localization Engine

→ Active Locale

→ Rendering Context

→ Theme or Plugin presentation



The Rendering Engine must not independently implement a conflicting localization resolution system.



Localization Engine

→ Resolves locale and translations.



Rendering Engine

→ Composes presentation.



---



# 57. Localization Security Contract



Localization behavior must preserve platform security boundaries.



The Localization Engine must not expose:



* Authentication Credentials

* Sensitive User information

* Permission internals

* Private Settings

* Private Plugin configuration

* Internal stack traces

* Other protected platform data



Locale input, namespaces, Translation Keys, and Translation Resources must be validated before use.



---



# 58. Localization Failure Contract



Localization operations must fail safely.



A localization failure must not automatically:



* Crash Core.

* Crash the Admin environment.

* Crash the public site.

* Corrupt User preferences.

* Corrupt Translation Resources.

* Modify Permission rules.

* Change Content data.

* Modify Plugin business data.

* Expose another Plugin's private Translation Resources.

* Expose sensitive platform information.



Where an approved fallback exists, the Localization Engine should use it safely.



Otherwise, a controlled unresolved or failure result must be returned.



---



# 59. Codex Implementation Rules



When implementing the Localization Engine, Codex must:



* Follow the frozen architecture from Documents 001–027.

* Follow the defined folder structure.

* Use approved public interfaces.

* Preserve Language and Locale separation.

* Preserve stable Locale identifiers.

* Preserve Translation Resource ownership.

* Preserve Translation namespace isolation.

* Preserve Theme boundaries.

* Preserve Plugin isolation.

* Preserve User Engine ownership of User preferences.

* Preserve Rendering Engine boundaries.

* Preserve Settings Engine boundaries.

* Preserve Cache Engine boundaries.

* Preserve Event Engine boundaries.

* Validate Locale input before activation.

* Validate Translation Resources before registration.

* Use stable Translation Keys.

* Keep visible Translation Values separate from business identifiers.

* Apply only explicitly defined fallback rules.

* Keep localization failures isolated.

* Invalidate applicable localization cache entries when Translation Resources or Locale configuration changes.

* Never use Translation Values as Permission identifiers.

* Never use Translation Values as Authentication identifiers.

* Never silently cross unrelated namespaces during fallback.

* Never let one Plugin overwrite another Plugin's private Translation Resource.

* Never assume one Language maps to only one Locale.

* Never invent undocumented Locale precedence.

* Never invent undocumented Translation fallback chains.

* Never require one localization library, file format, machine-translation provider, or external localization service as a permanent architectural dependency.



If an implementation detail is not defined by this document, Codex must not silently introduce a conflicting localization architecture.



---



# 60. Final Acceptance Criteria



* [x] Localization Engine purpose defined.

* [x] Localization Engine objectives defined.

* [x] Language defined.

* [x] Locale defined.

* [x] Locale Identifier defined.

* [x] Active Locale defined.

* [x] Default Locale defined.

* [x] Translation Resource defined.

* [x] Translation Key defined.

* [x] Translation ownership defined.

* [x] Localization boundary defined.

* [x] Locale resolution defined.

* [x] Request Locale integration defined.

* [x] User Locale preference boundary defined.

* [x] Locale validation defined.

* [x] Translation registration defined.

* [x] Translation namespace defined.

* [x] Translation resolution defined.

* [x] Translation fallback defined.

* [x] Missing Translation behavior defined.

* [x] Translation Value boundary defined.

* [x] Translation Key stability defined.

* [x] Rendering Engine integration defined.

* [x] Theme Engine integration defined.

* [x] Theme Translation override boundary defined.

* [x] Plugin Engine integration defined.

* [x] Plugin Translation isolation defined.

* [x] Settings Engine integration defined.

* [x] Menu Engine integration defined.

* [x] SEO Engine integration defined.

* [x] Notification Engine integration defined.

* [x] Search Engine boundary defined.

* [x] Cache Engine integration defined.

* [x] Event Engine integration defined.

* [x] Localization security boundary defined.

* [x] Localization input safety defined.

* [x] Translation Resource integrity defined.

* [x] Translation conflict handling defined.

* [x] Localization failure handling defined.

* [x] Localization failure isolation defined.

* [x] Fallback safety defined.

* [x] Localization cache safety defined.

* [x] Localization observability defined.

* [x] Localization compatibility defined.

* [x] Translation Resource update behavior defined.

* [x] Provider independence defined.

* [x] Locale Resolution contract defined.

* [x] Translation Resource contract defined.

* [x] Translation Resolution contract defined.

* [x] Fallback contract defined.

* [x] Theme Localization contract defined.

* [x] Plugin Localization contract defined.

* [x] User Locale contract defined.

* [x] Rendering Localization contract defined.

* [x] Localization Security contract defined.

* [x] Localization Failure contract defined.

* [x] Codex implementation rules defined.



---



# 61. Document Status



This document defines the Localization Engine specification for Favorite CMS.



The Localization Engine must be implemented according to this document and the frozen architecture established by Documents 001–027.



The Localization Engine provides controlled Language and Locale registration, Active Locale resolution, Translation Resource registration, Translation lookup, fallback coordination, namespace isolation, Theme and Plugin localization integration, User Locale preference integration, caching integration, and localization failure safety.



The Localization Engine must remain a supporting platform capability.



It must not become the owner of Content, Theme presentation, Plugin business logic, User identity, Authentication, Permission policy, Search behavior, or SEO strategy.



No specific localization library, translation file format, machine-translation platform, external translation provider, or localization service is required by this document unless another approved architecture specification explicitly defines one.



Any future breaking change to the Localization Engine must follow the project's versioning and migration rules.



---



End of Document



Next Document:



029-routing-engine.md



