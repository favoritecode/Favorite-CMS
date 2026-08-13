# Favorite CMS



Document ID: 021



Title: Settings Engine



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



Next Document:

022-menu-engine.md



---



# 1. Purpose



This document defines the architecture, responsibilities, boundaries, and public interfaces of the Favorite CMS Settings Engine.



The Settings Engine provides controlled storage, retrieval, validation, and management of platform configuration values that may change without modifying application source code.



The Settings Engine must keep settings ownership and configuration boundaries explicit.



---



# 2. Settings Engine Objectives



The Settings Engine must provide a foundation for:



* Setting Definition

* Setting Registration

* Setting Retrieval

* Setting Update

* Setting Validation

* Setting Scope

* Setting Defaults

* Setting Isolation

* Plugin Settings Integration

* Theme Settings Integration

* User Settings Integration

* Controlled Settings Failure Handling



The exact persistence mechanism remains behind approved Settings Engine interfaces.



---



# 3. Setting



A Setting represents an approved configurable value.



A Setting may control:



* Platform behavior

* Engine behavior

* Theme configuration

* Plugin configuration

* User preferences

* Other explicitly approved configurable behavior



A Setting must have a defined owner and scope.



---



# 4. Setting Key



Every Setting must have a stable Setting Key.



The Setting Key identifies the configurable value within its applicable scope.



Setting Keys must:



* Be deterministic.

* Follow approved naming conventions.

* Avoid collisions across unrelated scopes.

* Remain stable across compatible versions where possible.



The exact internal key format is implementation-specific unless defined by another architecture document.



---



# 5. Setting Value



A Setting Value contains the configured value associated with a Setting Key.



A Setting Value may represent an approved data type such as:



* Boolean

* String

* Number

* Structured data

* Other explicitly supported value types



Every Setting Value must comply with the validation contract defined for that Setting.



---



# 6. Setting Definition



A Setting Definition describes how a Setting is expected to behave.



A Setting Definition may include:



* Setting Key

* Setting purpose

* Owner

* Scope

* Expected value type

* Default value

* Validation requirements

* Visibility rules

* Mutability rules



Consumers must not depend on undocumented Setting behavior.



---



# 7. Setting Registration



Engines, Themes, and Plugins may register approved Settings through public Settings Engine interfaces.



Registration must define enough information for the Settings Engine to validate and resolve the Setting correctly.



A registered Setting must not overwrite an unrelated Setting from another scope.



---



# 8. Setting Scope



A Setting must belong to an explicit scope.



Possible scopes may include:



* Platform

* Engine

* Theme

* Plugin

* User

* Other explicitly approved scope



The exact scope model must remain deterministic and isolated.



A Setting from one scope must not unintentionally override an unrelated Setting from another scope.



---



# 9. Settings Ownership Boundary



The Settings Engine manages configurable values.



It does not own the business functionality controlled by those values.



Therefore:



Theme Engine

→ Owns Theme behavior.



Plugin

→ Owns Plugin business logic.



User Engine

→ Owns User state.



Notification Engine

→ Owns Notification behavior.



Settings Engine

→ Stores and resolves approved configuration values.



The Settings Engine must not become a replacement for the owning Engine or Plugin.



---



## Acceptance Criteria



* [x] Settings Engine purpose defined.

* [x] Settings Engine objectives defined.

* [x] Setting defined.

* [x] Setting Key defined.

* [x] Setting Value defined.

* [x] Setting Definition defined.

* [x] Setting Registration defined.

* [x] Setting Scope defined.

* [x] Settings ownership boundary defined.



---









---



# 10. Setting Retrieval



The Settings Engine must provide a public interface for retrieving approved Setting Values.



Retrieval must:



1\. Identify the Setting Key.

2\. Determine the applicable Setting Scope.

3\. Resolve the stored value.

4\. Apply the approved default when required.

5\. Return a normalized Setting result.



Consumers must not access internal persistence directly.



---



# 11. Setting Update



Approved Settings may be updated through the public Settings Engine interface.



An update operation must:



* Resolve the Setting Definition.

* Validate the new value.

* Verify applicable authorization.

* Preserve the correct Setting Scope.

* Store the approved value.

* Return a normalized update result.



Invalid values must not replace a valid Setting Value.



---



# 12. Setting Validation



Every configurable Setting must follow its defined validation rules.



Validation may verify:



* Value type

* Required value

* Allowed range

* Allowed structure

* Approved format

* Other explicitly defined constraints



The Settings Engine must not silently accept an invalid value.



---



# 13. Default Values



A Setting Definition may provide an approved Default Value.



A Default Value may be used when:



* No stored value exists.

* The Setting has not been customized.

* An explicitly supported reset operation restores the Setting.



Default Values must be defined by the Setting owner or approved platform contract.



The Settings Engine must not invent defaults for undocumented Settings.



---



# 14. Setting Resolution



The Settings Engine must resolve a Setting deterministically.



The general resolution flow is:



Setting Request

→ Resolve Key

→ Resolve Scope

→ Resolve Registered Definition

→ Retrieve Stored Value

→ Validate Value

→ Apply Approved Default if Required

→ Return Result



The exact persistence mechanism must remain hidden from consumers.



---



# 15. Missing Setting



A requested Setting may be unavailable because:



* The Setting is not registered.

* The applicable scope does not exist.

* No stored value exists.

* No Default Value is defined.

* The Setting is unavailable for the current context.



A missing Setting must return a controlled result.



The Settings Engine must not invent an undocumented value.



---



# 16. Invalid Stored Value



If a stored Setting Value no longer satisfies its active Setting Definition, the Settings Engine must not silently treat that value as valid.



The Engine may:



* Reject the invalid value.

* Use an approved Default Value where permitted.

* Report a controlled configuration error.

* Trigger another explicitly defined recovery path.



The exact recovery policy must be defined by the applicable Setting contract.



---



# 17. Reset Setting



The Settings Engine may support resetting an approved Setting.



A reset operation may:



* Remove the customized value.

* Restore the approved Default Value.

* Return the Setting to its defined initial state.



Resetting a Setting must not affect unrelated Settings.



---



# 18. Setting Mutation Boundary



Changing a Setting changes configuration state.



It must not directly modify unrelated business resources.



For example:



Theme Setting Update

→ May change Theme configuration.



Plugin Setting Update

→ May change Plugin configuration.



Notification Setting Update

→ May change Notification behavior.



But:



Setting Update

→ Must not directly rewrite unrelated Content or Media resources unless the owning Engine explicitly performs an approved operation.



---



## Acceptance Criteria



* [x] Setting retrieval defined.

* [x] Setting update defined.

* [x] Setting validation defined.

* [x] Default values defined.

* [x] Setting resolution defined.

* [x] Missing Setting behavior defined.

* [x] Invalid stored value handling defined.

* [x] Setting reset defined.

* [x] Setting mutation boundary defined.



---









---



# 19. Platform Settings



Platform Settings apply to the CMS platform as a whole.



They may control approved global behavior such as:



* Site-wide configuration

* Default platform behavior

* Global feature configuration

* Other explicitly approved platform options



Platform Settings must not silently override Engine-, Plugin-, Theme-, or User-specific Settings unless the resolution contract explicitly permits it.



---



# 20. Engine Settings



An Engine may register Settings required for its configurable behavior.



Engine Settings must:



* Belong to the owning Engine.

* Use approved Setting Keys.

* Define validation requirements.

* Define applicable defaults.

* Remain accessible through the Settings Engine public interface.



An Engine must not store configurable values by bypassing the Settings Engine when those values are defined as managed Settings.



---



# 21. Plugin Settings



Plugins may register Settings through approved Settings Engine interfaces.



Plugin Settings must remain isolated by Plugin ownership.



A Plugin may define:



* Plugin configuration

* Feature options

* Integration configuration

* Other approved Plugin-specific Settings



A Plugin must not:



* Overwrite another Plugin's private Settings.

* Modify unrelated Engine Settings.

* Access protected Settings without authorization.

* Depend directly on Settings persistence internals.



---



# 22. Theme Settings



Themes may register approved presentation-related Settings.



Theme Settings may control:



* Presentation options

* Layout-related configuration

* Theme feature configuration

* Other approved Theme customization values



Theme Settings must remain separate from Theme source files where configuration persistence is required.



Updating or replacing Theme files must not automatically destroy approved stored Theme Settings.



---



# 23. Theme Update Safety



Theme configuration must remain isolated from Theme package updates where possible.



The preferred boundary is:



Theme Package

→ Defines supported Settings.



Settings Engine

→ Stores approved customized values.



Theme Update

→ Updates Theme files.



Stored Theme Settings

→ Remain preserved when still compatible.



If a Theme update makes a Setting incompatible, the conflict must be handled through an explicit compatibility or migration process.



---



# 24. User Settings



User-specific preferences may be stored through the Settings Engine when defined by the platform contract.



User Settings must remain isolated by User context.



One User's private Settings must not be returned as another User's Settings.



The User Engine remains responsible for User identity.



The Settings Engine remains responsible for approved configurable User values.



---



# 25. Notification Settings Integration



The Notification Engine may use approved Settings for configurable Notification behavior.



Examples may include:



* User Notification preferences

* Allowed delivery preferences

* Other approved Notification configuration



The Settings Engine stores and resolves the configuration.



The Notification Engine remains responsible for Notification behavior.



---



# 26. Settings and Permission Engine



Reading or modifying protected Settings may require authorization.



The Permission Engine remains responsible for authorization decisions.



The Settings Engine must not assume that access to one Setting automatically grants access to:



* Other Settings

* Other scopes

* Other Users' Settings

* Plugin-private Settings

* Administrative Settings



Authorization must follow the applicable Setting operation and scope.



---



# 27. Settings and Cache Engine



The Cache Engine may cache approved resolved Setting Values.



When a Setting changes, affected cached Setting representations must be invalidated when required.



The Settings Engine remains the source of truth for managed Setting Values.



The Cache Engine must not become the authoritative Settings store.



---



# 28. Settings and Event Engine



The Settings Engine may publish approved Events when relevant Setting changes occur.



An approved Settings-related Event may allow other Engines or Plugins to react to configuration changes.



The Event Engine only communicates the occurrence.



The Settings Engine remains responsible for Setting state.



The exact Event types must be explicitly defined before implementation.



---



## Acceptance Criteria



* [x] Platform Settings boundary defined.

* [x] Engine Settings boundary defined.

* [x] Plugin Settings boundary defined.

* [x] Theme Settings boundary defined.

* [x] Theme update safety defined.

* [x] User Settings boundary defined.

* [x] Notification Settings integration defined.

* [x] Permission integration defined.

* [x] Cache integration defined.

* [x] Event integration defined.



---









---



# 29. Settings Security Boundary



The Settings Engine must treat protected configuration as controlled platform data.



Protected Settings may include:



* Administrative configuration

* Private Plugin configuration

* User-specific preferences

* Integration configuration

* Sensitive operational values



The Settings Engine must not expose protected Setting Values to unauthorized consumers.



---



# 30. Sensitive Settings



Some Settings may contain sensitive values.



Sensitive Settings must:



* Use restricted access rules.

* Avoid unnecessary exposure through APIs.

* Avoid exposure through logs or diagnostics.

* Remain isolated from public presentation data.

* Be returned only to authorized consumers when required.



A Setting must not be treated as public merely because it is configurable.



---



# 31. Settings Authorization



Setting operations may require authorization.



Authorization may apply to:



* Reading protected Settings

* Creating or registering Settings

* Updating Settings

* Resetting Settings

* Managing another User's Settings

* Managing Theme or Plugin configuration

* Administrative configuration



The Permission Engine remains responsible for authorization decisions.



---



# 32. Settings Isolation



Settings must remain isolated according to their defined scope and owner.



Examples:



Platform Settings

→ Must not be silently overwritten by Plugin Settings.



Plugin A Settings

→ Must not overwrite Plugin B Settings.



User A Settings

→ Must not be exposed as User B Settings.



Theme Settings

→ Must not overwrite unrelated Platform Settings.



Scope isolation must remain deterministic.



---



# 33. Settings Lifecycle



The general Setting lifecycle is:



Register Definition

→ Resolve Default

→ Store or Retrieve Value

→ Validate Value

→ Update when approved

→ Reset when approved

→ Migrate or remove when required



Removing a Setting Definition must not silently corrupt unrelated Settings.



---



# 34. Setting Removal



A Setting Definition may be removed when the owning Engine, Theme, Plugin, or platform no longer supports it.



Removal behavior must be explicitly controlled.



Possible handling may include:



* Removing the active Setting registration

* Preserving stored data for migration

* Removing stored data when explicitly approved

* Marking the Setting as unsupported



The Settings Engine must not automatically delete unrelated configuration.



---



# 35. Settings Migration



A Setting may require migration when its contract changes between compatible or breaking versions.



Migration may include:



* Key migration

* Value format migration

* Scope migration

* Default-value changes

* Validation-rule changes



A migration must preserve valid User configuration where possible.



Breaking Setting changes must follow the project's versioning and migration rules.



---



# 36. Settings Observability



The Settings Engine may expose controlled operational information such as:



* Setting Registered

* Setting Updated

* Setting Reset

* Setting Validation Failed

* Setting Migration Failed

* Setting Resolution Failed



Operational information must not expose protected Setting Values unnecessarily.



---



# 37. Settings Failure Handling



Possible Settings failures include:



* Unknown Setting Key

* Invalid Setting Value

* Scope resolution failure

* Persistence failure

* Authorization failure

* Migration failure

* Registration conflict



A Settings failure must return a controlled result.



A failed Setting operation must not silently modify unrelated Settings.



---



# 38. Settings Failure Isolation



A failure within one Setting scope must remain isolated from unrelated scopes where possible.



For example:



Plugin Setting failure

→ Must not corrupt Platform Settings.



Theme Setting failure

→ Must not corrupt User Settings.



User Setting failure

→ Must not corrupt another User's Settings.



Settings isolation must remain intact during failure handling.



---



# 39. Settings Compatibility



Changes to the internal Settings Engine implementation must preserve the public Settings contract when the change is non-breaking.



Existing Engines, Themes, Plugins, and User-setting consumers must remain compatible with supported Settings Engine versions.



Breaking changes must follow the project's versioning and migration rules.



---



# 40. Settings Engine Non-Goals



The Settings Engine does not own:



* Content Resources

* Media Resources

* User identity

* Permission rules

* Theme rendering

* Plugin business logic

* Notification delivery

* Search Indexes

* Cache Entries

* Event delivery

* Queue Jobs



The Settings Engine is responsible for approved configuration definition, storage, validation, resolution, and management.



---



## Acceptance Criteria



* [x] Settings security boundary defined.

* [x] Sensitive Settings defined.

* [x] Settings authorization defined.

* [x] Settings isolation defined.

* [x] Settings lifecycle defined.

* [x] Setting removal defined.

* [x] Settings migration defined.

* [x] Settings observability defined.

* [x] Settings failure handling defined.

* [x] Settings failure isolation defined.

* [x] Settings compatibility defined.

* [x] Settings Engine non-goals defined.



---









---



# 41. Final Settings Resolution Rules



The Settings Engine must resolve Settings through approved public interfaces.



The general Setting resolution flow is:



1\. Receive the Setting request.

2\. Identify the Setting Key.

3\. Determine the applicable Setting Scope.

4\. Resolve the registered Setting Definition.

5\. Retrieve the stored Setting Value.

6\. Validate the stored value.

7\. Apply the approved Default Value when required.

8\. Evaluate applicable authorization.

9\. Return the normalized Setting result.



The Settings Engine must not invent undocumented configuration values.



---



# 42. Setting Contract



Every managed Setting must follow an approved Setting contract.



The contract must define:



* Setting Key

* Setting purpose

* Setting owner

* Setting Scope

* Expected value type

* Default Value when applicable

* Validation requirements

* Visibility requirements

* Authorization requirements when applicable

* Mutability rules

* Compatibility requirements



Consumers must not depend on Setting behavior that is outside the approved contract.



---



# 43. Setting Update Contract



An approved Setting update must:



1\. Resolve the correct Setting Definition.

2\. Resolve the applicable Scope.

3\. Evaluate required authorization.

4\. Validate the proposed value.

5\. Store the approved value.

6\. Invalidate affected cached representations when required.

7\. Publish an approved Setting-change Event when explicitly defined.

8\. Return a normalized result.



A failed update must not replace the previous valid value unless an explicit recovery or migration contract requires it.



---



# 44. Scope Resolution Contract



Setting Scope must remain deterministic.



The Settings Engine must not silently merge or override unrelated scopes.



Examples:



Platform Scope

→ Platform-wide configuration.



Engine Scope

→ Configuration owned by an Engine.



Theme Scope

→ Configuration owned by a Theme.



Plugin Scope

→ Configuration owned by a Plugin.



User Scope

→ Configuration associated with a User.



Cross-scope behavior must be explicitly defined before implementation.



---



# 45. Theme Configuration Contract



Theme configuration must remain separate from Theme package files when persistent customization is required.



The preferred model is:



Theme

→ Declares supported Settings.



Settings Engine

→ Stores customized values.



Theme Engine

→ Resolves the active Theme.



Rendering Engine

→ Uses the resolved Theme configuration.



Theme updates must preserve compatible customized Settings where possible.



A Theme package must not require users to directly modify Theme source files for normal configurable options.



---



# 46. Plugin Configuration Contract



Plugin configuration must remain isolated by Plugin ownership.



A Plugin must:



* Register Settings through approved interfaces.

* Use its own approved Setting scope.

* Define validation requirements.

* Define defaults where applicable.

* Access protected Settings only when authorized.



A Plugin must not:



* Modify Settings Engine internals.

* Overwrite another Plugin's private Settings.

* Overwrite unrelated Platform Settings.

* Access another User's private Settings without authorization.

* Depend directly on the internal persistence implementation.



---



# 47. User Settings Contract



User-specific Settings must remain isolated by User identity.



The Settings Engine must ensure that:



* User A Settings are not returned as User B Settings.

* User-specific updates affect only the approved User scope.

* Protected User Settings require applicable authorization.

* User identity remains owned by the User Engine.



The Settings Engine owns configuration management, not User identity.



---



# 48. Sensitive Configuration Contract



Sensitive Settings require stronger protection than ordinary presentation configuration.



Sensitive values must not be exposed through:



* Public APIs

* Public rendering context

* Client-side configuration without explicit approval

* Logs

* Diagnostics

* Event Payloads

* Notification Payloads



unless the applicable contract explicitly permits the exposure.



Sensitive configuration must remain behind authorized interfaces.



---



# 49. Settings Failure Contract



Settings operations must fail safely.



A Settings failure must not automatically:



* Corrupt unrelated Settings.

* Corrupt another scope.

* Corrupt User data.

* Corrupt Theme files.

* Corrupt Plugin files.

* Modify unrelated Content or Media.

* Expose protected Setting Values.

* Replace a valid value with an invalid value.



The Settings Engine must provide controlled failure results.



---



# 50. Codex Implementation Rules



When implementing the Settings Engine, Codex must:



* Follow the frozen architecture from Documents 001–020.

* Follow the defined folder structure.

* Use approved public interfaces.

* Preserve Setting ownership.

* Preserve Setting Scope isolation.

* Preserve User isolation.

* Preserve Theme Engine boundaries.

* Preserve Plugin Engine boundaries.

* Preserve Permission Engine boundaries.

* Preserve Cache Engine boundaries.

* Preserve Event Engine boundaries.

* Preserve Notification Engine boundaries.

* Keep Theme customization separate from Theme source files where persistent configuration is required.

* Keep Plugin Settings isolated by Plugin ownership.

* Keep Setting validation contract-driven.

* Never invent undocumented Setting Keys.

* Never invent undocumented default values.

* Never silently merge unrelated Setting scopes.

* Never expose sensitive Settings through public interfaces without explicit approval.

* Never introduce a specific Settings database, key-value service, configuration provider, secrets manager, or external configuration service as an architectural requirement unless another document explicitly defines one.



If an implementation detail is not defined by this document, Codex must not silently introduce a conflicting Settings architecture.



---



# 51. Final Acceptance Criteria



* [x] Settings Engine purpose defined.

* [x] Setting defined.

* [x] Setting Key defined.

* [x] Setting Value defined.

* [x] Setting Definition defined.

* [x] Setting Registration defined.

* [x] Setting Scope defined.

* [x] Setting Retrieval defined.

* [x] Setting Update defined.

* [x] Setting Validation defined.

* [x] Default Values defined.

* [x] Setting Resolution defined.

* [x] Missing Setting behavior defined.

* [x] Invalid Setting handling defined.

* [x] Setting Reset defined.

* [x] Platform Settings defined.

* [x] Engine Settings defined.

* [x] Plugin Settings defined.

* [x] Theme Settings defined.

* [x] Theme update safety defined.

* [x] User Settings defined.

* [x] Notification Settings integration defined.

* [x] Permission integration defined.

* [x] Cache integration defined.

* [x] Event integration defined.

* [x] Sensitive Settings defined.

* [x] Settings authorization defined.

* [x] Settings isolation defined.

* [x] Settings lifecycle defined.

* [x] Setting removal defined.

* [x] Settings migration defined.

* [x] Settings observability defined.

* [x] Settings failure handling defined.

* [x] Settings failure isolation defined.

* [x] Settings compatibility defined.

* [x] Theme configuration contract defined.

* [x] Plugin configuration contract defined.

* [x] User Settings contract defined.

* [x] Sensitive configuration contract defined.

* [x] Codex implementation rules defined.



---



# 52. Document Status



This document defines the Settings Engine specification for Favorite CMS.



The Settings Engine must be implemented according to this document and the frozen architecture established by Documents 001–020.



The Settings Engine provides controlled definition, storage, validation, resolution, update, reset, isolation, and lifecycle management for approved configuration values.



The Settings Engine must not become the owner of the business functionality controlled by those values.



Theme customization, Plugin configuration, User preferences, Engine configuration, and Platform configuration must remain isolated according to their approved scopes.



No specific Settings database, key-value storage engine, configuration provider, secrets manager, external configuration platform, or persistence technology is required by this document unless a future architecture document explicitly defines one.



Any future breaking change to the Settings Engine must follow the project's versioning and migration rules.



---



End of Document



Next Document:



022-menu-engine.md



