# Favorite CMS



Document ID: 027



Title: Storage Engine



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



Next Document:

028-localization-engine.md



---



# 1. Purpose



This document defines the architecture, responsibilities, boundaries, and public interfaces of the Favorite CMS Storage Engine.



The Storage Engine provides a controlled abstraction for storing, retrieving, moving, copying, and deleting approved file-based platform data.



The Storage Engine must separate platform functionality from storage-provider-specific implementation.



Engines and Plugins must interact with storage through approved Storage Engine interfaces rather than directly depending on a specific local or remote storage provider.



---



# 2. Storage Engine Objectives



The Storage Engine must provide a foundation for:



* Storage Provider Abstraction

* File Storage

* File Retrieval

* File Deletion

* File Copying

* File Moving

* Storage Path Resolution

* Storage Metadata

* Storage Scope Isolation

* Media Storage Integration

* Plugin Storage Integration

* Storage Validation

* Storage Failure Handling

* Storage Provider Migration



The exact storage provider must remain behind approved Storage Engine interfaces.



---



# 3. Storage Resource



A Storage Resource represents an approved file or object managed through the Storage Engine.



A Storage Resource may represent:



* Uploaded file

* Media file

* Generated file

* Plugin-owned file

* Theme-related generated asset

* Exported file

* Other explicitly supported stored object



The Storage Engine owns storage coordination.



It does not automatically own the business resource associated with the stored file.



---



# 4. Storage Identifier



Every managed Storage Resource must have a stable reference that can be used by approved platform components.



The reference may identify:



* Storage Resource

* Storage Provider

* Storage Scope

* Internal storage location

* Approved metadata



Consumers should use the approved Storage reference instead of depending directly on provider-specific filesystem or object-storage paths.



---



# 5. Storage Provider



A Storage Provider is an implementation capable of storing and retrieving Storage Resources.



A Provider may represent:



* Local storage

* Remote object storage

* S3-compatible storage

* Other explicitly supported storage implementation



The Storage Engine must normalize Provider behavior through a common public contract.



The platform must not require unrelated Engines or Plugins to know Provider-specific APIs.



---



# 6. Storage Provider Contract



Every Storage Provider must implement the approved Storage contract.



The Provider contract may include operations for:



* Store

* Retrieve

* Delete

* Copy

* Move

* Check existence

* Resolve approved metadata

* Other explicitly supported operations



Provider-specific behavior must remain inside the Provider implementation.



---



# 7. Storage Scope



Storage Resources must belong to an approved Storage Scope.



Possible scopes may include:



* Media

* Plugin

* Theme-generated data

* Export

* Temporary storage

* Other explicitly approved scopes



A Storage Scope must provide isolation between unrelated resource owners.



Plugin-private files must not become accessible to unrelated Plugins merely because they use the same Storage Provider.



---



# 8. Storage Path Boundary



The Storage Engine may internally use paths, keys, object identifiers, or equivalent Provider-specific locations.



These internal locations must remain behind the Storage Engine contract.



Consumers should not construct Provider-specific paths when an approved Storage operation exists.



The Storage Engine must validate storage destinations before performing write operations.



---



# 9. Storage Ownership Boundary



The Storage Engine owns storage operations and Storage Resource references.



It does not own the business resource represented by the stored file.



Therefore:



Media Engine

→ Owns Media Resource lifecycle.



Plugin

→ Owns Plugin business data.



Theme Engine

→ Owns Theme package resources.



Update Engine

→ Owns update coordination.



Storage Engine

→ Owns storage-provider abstraction and file operations.



Deleting a business resource and deleting its stored file are separate operations that must be coordinated by the owning Engine.



---



# 10. Provider Independence



Favorite CMS must remain capable of changing supported Storage Providers without forcing unrelated Engines or Plugins to rewrite their business logic.



The preferred architecture is:



Owning Engine or Plugin

→ Storage Engine

→ Storage Provider



not:



Owning Engine or Plugin

→ Provider-specific SDK or filesystem implementation



Provider independence is required for development-to-production portability.



---



## Acceptance Criteria



* [x] Storage Engine purpose defined.

* [x] Storage Engine objectives defined.

* [x] Storage Resource defined.

* [x] Storage Identifier defined.

* [x] Storage Provider defined.

* [x] Storage Provider contract defined.

* [x] Storage Scope defined.

* [x] Storage path boundary defined.

* [x] Storage ownership boundary defined.

* [x] Provider independence defined.



---









---



# 11. File Storage



The Storage Engine must provide an approved interface for storing supported files or objects.



The general storage flow is:



Storage Request

→ Validate Input

→ Resolve Storage Scope

→ Resolve Storage Provider

→ Resolve Internal Storage Location

→ Store Resource

→ Return Normalized Storage Reference



The owning Engine or Plugin remains responsible for the business meaning of the stored resource.



---



# 12. Storage Validation



Before storing a Resource, the Storage Engine must validate the applicable storage request.



Validation may include:



* Storage Scope

* Resource identity

* File or object availability

* Allowed size when defined

* Allowed type when defined

* Destination validity

* Provider availability

* Other explicitly defined storage requirements



Invalid storage input must not be written.



---



# 13. Storage Write Result



A successful storage operation must return a normalized result.



The result may include:



* Storage Identifier

* Storage Scope

* Provider reference

* Approved metadata

* Internal object reference

* Other explicitly supported storage information



Provider-specific implementation details should remain hidden unless explicitly required by another contract.



---



# 14. File Retrieval



The Storage Engine must provide an approved interface for retrieving an existing Storage Resource.



The general retrieval flow is:



Storage Reference

→ Validate Reference

→ Resolve Storage Provider

→ Resolve Internal Resource Location

→ Retrieve Resource

→ Return Normalized Result



Retrieval must respect applicable access and ownership boundaries.



---



# 15. Storage Existence Check



The Storage Engine may support checking whether a Storage Resource exists.



An existence check must operate through the public Storage contract.



Consumers must not directly inspect Provider-specific filesystem paths or object-storage locations when an approved existence interface exists.



A missing Storage Resource must return a controlled result.



---



# 16. File Deletion



The Storage Engine must support controlled deletion of approved Storage Resources.



Deletion must:



* Validate the Storage Reference.

* Resolve the correct Provider.

* Verify applicable authorization or ownership requirements.

* Delete only the intended Storage Resource.

* Return a normalized deletion result.



Deleting a stored file must not automatically delete the associated business Resource.



---



# 17. Deletion Safety



Storage deletion must be explicit and scoped.



The Storage Engine must prevent accidental deletion of:



* Unrelated Storage Resources

* Another Plugin's private files

* Another User's protected files

* Theme package files outside the approved operation

* Core files

* Provider-level data outside the approved Storage Scope



A failed deletion must not be reported as successful.



---



# 18. File Copy



The Storage Engine may support copying a Storage Resource.



The copy process may include:



Source Reference

→ Validate Source

→ Resolve Destination Scope

→ Resolve Destination Provider

→ Copy Resource

→ Return New Storage Reference



The copied Storage Resource must receive its own valid reference when required by the Storage contract.



Copying must not change ownership of the source business Resource automatically.



---



# 19. File Move



The Storage Engine may support moving a Storage Resource.



The move process may include:



Source Reference

→ Validate Source

→ Validate Destination

→ Move Resource

→ Update Storage Reference when required

→ Return Normalized Result



A failed move must not silently lose the valid source Resource.



Where the Provider cannot guarantee an atomic move, the implementation must use an approved safe strategy.



---



# 20. Storage Metadata



The Storage Engine may maintain approved metadata about a Storage Resource.



Storage Metadata may include:



* Storage Identifier

* Provider reference

* Scope

* Size

* Type

* Created information

* Updated information

* Other explicitly supported storage metadata



Business metadata remains owned by the applicable Engine or Plugin.



Storage Metadata must not become a replacement for Media or Content metadata.



---



## Acceptance Criteria



* [x] File storage defined.

* [x] Storage validation defined.

* [x] Storage write result defined.

* [x] File retrieval defined.

* [x] Storage existence check defined.

* [x] File deletion defined.

* [x] Deletion safety defined.

* [x] File copy defined.

* [x] File move defined.

* [x] Storage metadata defined.



---









---



# 21. Storage and Media Engine



The Media Engine may use the Storage Engine for approved Media file storage.



The preferred boundary is:



Media Engine

→ Owns Media Resource lifecycle and Media metadata.



Storage Engine

→ Stores and retrieves the underlying file or object.



Storage Provider

→ Performs Provider-specific storage operations.



The Storage Engine must not become the owner of Media behavior.



---



# 22. Media Storage Reference



A Media Resource may reference a Storage Resource through an approved Storage Identifier or equivalent public reference.



The Media Engine may associate:



Media Resource

→ Storage Reference



The Storage Engine must not require the Media Engine to persist Provider-specific paths or SDK-specific identifiers when a normalized Storage Reference can be used.



Changing Storage Provider must not require rewriting Media business logic.



---



# 23. Storage and Plugin Engine



Plugins may use approved Storage Engine interfaces for Plugin-owned files.



A Plugin may:



* Store approved files.

* Retrieve its own stored files.

* Delete its own stored files.

* Use an approved Plugin Storage Scope.

* Request copy or move operations when supported.



A Plugin must not:



* Modify Storage Engine internals.

* Access another Plugin's private Storage Scope.

* Access Core files through Plugin storage operations.

* Depend directly on Provider-specific APIs.

* Delete unrelated Storage Resources.



---



# 24. Plugin Storage Isolation



Plugin Storage must remain isolated by ownership and scope.



For example:



Plugin A Storage

→ Must not expose Plugin B private files.



Plugin B deletion request

→ Must not delete Plugin A resources.



Disabled Plugin

→ Must not corrupt another Plugin's Storage Resources.



Plugin storage isolation must remain intact even when multiple Plugins use the same underlying Storage Provider.



---



# 25. Storage and Theme Engine



Theme package resources and runtime-generated Theme data must remain clearly separated.



Theme package files are managed according to the Theme and Update contracts.



If a Theme produces approved runtime-generated files, those files may use the Storage Engine.



The Storage Engine must not allow normal Theme runtime operations to modify protected Core or unrelated Theme package files.



---



# 26. Storage and Update Engine



The Update Engine may require controlled file operations while installing or recovering supported components.



Update-related file operations must follow the Update Engine contract.



The Storage Engine may provide approved storage or file-operation capabilities when applicable.



The Update Engine remains responsible for:



* Update validation

* Candidate installation

* Activation

* Recovery

* Rollback coordination



The Storage Engine must not decide whether an Update Package is valid.



---



# 27. Storage and Settings Engine



The Settings Engine may store configuration required to select or configure an approved Storage Provider.



Examples may include:



* Active Provider selection

* Storage Scope configuration

* Provider-specific approved configuration

* Other explicitly defined Storage Settings



Sensitive Provider credentials must not be exposed as ordinary public Settings.



The Settings Engine manages configuration.



The Storage Engine manages storage behavior.



---



# 28. Storage and Permission Engine



Protected storage operations must respect applicable authorization rules.



Permission checks may apply to:



* Uploading files

* Retrieving protected files

* Deleting files

* Copying files

* Moving files

* Accessing User-specific storage

* Accessing Plugin-private storage

* Administrative Storage operations



The Permission Engine remains responsible for authorization decisions.



The Storage Engine must not treat possession of a Storage Identifier as automatic permission to access the Resource.



---



# 29. Storage and Authentication Engine



Authentication Context may be required for User-specific or protected storage operations.



The preferred boundary is:



Authentication Engine

→ Resolves identity.



Permission Engine

→ Evaluates access.



Storage Engine

→ Performs the approved storage operation.



Authentication alone must not grant unrestricted storage access.



---



# 30. Storage and API Engine



The API Engine may expose approved Storage-backed operations through HTTP interfaces when explicitly defined.



Possible API operations may include approved file upload or retrieval workflows.



The API Engine must not directly access Provider-specific storage internals.



Preferred flow:



API Request

→ Authentication and Permission checks

→ Owning Engine or approved Storage operation

→ Storage Engine

→ Storage Provider



The exact public Storage API must be defined by an approved API contract.



---



# 31. Storage and Event Engine



The Storage Engine may publish approved Events for meaningful Storage lifecycle changes.



Conceptual occurrences may include:



* Storage Resource created

* Storage Resource deleted

* Storage Resource moved

* Storage Provider operation failed



Exact Event Names must be explicitly defined before implementation.



Storage Events must not expose sensitive Provider credentials or private storage details.



---



# 32. Storage and Cache Engine



The Cache Engine may cache approved Storage metadata or derived storage information.



Storage cache entries may require invalidation when:



* A Storage Resource changes.

* A Storage Resource moves.

* A Storage Resource is deleted.

* Storage metadata changes.

* Provider-related resolution changes.



The Storage Engine remains authoritative for managed Storage Resources.



The Cache Engine must not become the Storage Resource source of truth.



---



# 33. Storage Resource Integrity



The Storage Engine must preserve Storage Resource integrity during supported operations.



It must prevent or safely handle:



* Invalid Storage References

* Invalid destination scopes

* Conflicting object identifiers

* Unsupported cross-scope operations

* Provider inconsistencies

* Incomplete copy operations

* Incomplete move operations

* Unexpected overwrite attempts



A failed operation must not silently corrupt an existing valid Storage Resource.



---



# 34. Storage Isolation



Storage operations must remain isolated between unrelated owners and scopes.



For example:



Media Storage

→ Must not expose Plugin-private Storage.



Plugin Storage

→ Must not modify Core files.



User-specific Storage

→ Must not expose another User's protected files.



Temporary Storage

→ Must not silently replace permanent Storage.



Storage isolation is required regardless of the underlying Provider.



---



## Acceptance Criteria



* [x] Media Engine integration defined.

* [x] Media Storage Reference defined.

* [x] Plugin Engine integration defined.

* [x] Plugin Storage isolation defined.

* [x] Theme Engine boundary defined.

* [x] Update Engine integration defined.

* [x] Settings Engine integration defined.

* [x] Permission Engine integration defined.

* [x] Authentication Engine integration defined.

* [x] API Engine integration defined.

* [x] Event Engine integration defined.

* [x] Cache Engine integration defined.

* [x] Storage Resource integrity defined.

* [x] Storage isolation defined.



---









---



# 35. Storage Security Boundary



The Storage Engine is responsible for enforcing storage-access boundaries through approved platform contracts.



Storage operations must not expose:



* Private Storage Provider credentials

* Internal Provider secrets

* Unapproved filesystem paths

* Private object-storage keys

* Protected User files

* Private Plugin files

* Core files outside approved operations

* Other protected Storage Resources



Security requirements must apply regardless of the active Storage Provider.



---



# 36. Storage Authorization



Protected Storage operations may require authorization.



Authorization may apply to:



* Creating Storage Resources

* Retrieving protected Storage Resources

* Deleting Storage Resources

* Copying Storage Resources

* Moving Storage Resources

* Managing Storage Providers

* Managing Storage configuration

* Accessing another User's protected files

* Administrative Storage operations



The Permission Engine remains responsible for authorization decisions.



The Storage Engine must not treat knowledge of a Storage Identifier as sufficient authorization.



---



# 37. Storage Provider Credentials



Provider credentials and sensitive Provider configuration must remain protected.



Sensitive Provider information must not be exposed through:



* Public APIs

* Theme resources

* Rendering Context

* Events

* Notifications

* Logs

* Diagnostics

* Plugin configuration without explicit authorization



The exact secure storage mechanism for Provider credentials must follow the approved security and configuration architecture.



---



# 38. Storage Provider Availability



A Storage Provider may become temporarily unavailable.



Possible causes may include:



* Local storage failure

* Remote Provider outage

* Network failure

* Invalid Provider configuration

* Provider authentication failure

* Other infrastructure failures



Provider unavailability must return a controlled Storage failure.



The Storage Engine must not report an unavailable Resource as successfully stored or retrieved.



---



# 39. Storage Failure Handling



Possible Storage failures include:



* Invalid Storage Reference

* Invalid Storage Scope

* Provider unavailable

* Store failure

* Retrieval failure

* Delete failure

* Copy failure

* Move failure

* Permission failure

* Provider configuration failure

* Resource integrity failure



Storage failures must return normalized controlled results.



Raw Provider errors must not be exposed directly to unrelated consumers.



---



# 40. Storage Failure Isolation



Storage failures must remain isolated from unrelated resources and platform components.



For example:



Failed Plugin Storage operation

→ Must not corrupt Media Storage.



Failed Media upload

→ Must not corrupt existing Media Resources.



Provider failure

→ Must not modify unrelated Settings.



Failed deletion

→ Must not delete another Resource.



Storage failure isolation must preserve ownership and scope boundaries.



---



# 41. Storage Provider Migration



Favorite CMS may support migration from one Storage Provider to another.



Provider migration must be treated as an explicit controlled operation.



A migration may include:



* Reading existing Storage Resources

* Writing equivalent Resources to the destination Provider

* Verifying copied Resources

* Updating approved Storage references

* Preserving resource ownership

* Preserving required metadata

* Removing old copies only when explicitly approved



Migration must not silently invalidate existing business Resources.



---



# 42. Storage Migration Validation



Before completing a Storage Provider migration, the Storage Engine must verify that required Resources are available in the destination Provider.



Validation may include:



* Resource existence

* Resource integrity

* Metadata consistency

* Scope consistency

* Reference consistency

* Other explicitly required checks



A migration must not be reported as complete when required Resources failed to migrate.



---



# 43. Storage Migration Failure



A Storage migration failure must enter a controlled recovery state.



The Storage Engine must avoid replacing valid existing Storage references with invalid destination references.



When migration partially succeeds:



* Existing valid source data should remain preserved when possible.

* Failed Resources must be identifiable.

* The migration must not be marked fully completed.

* Recovery must follow the approved migration contract.



The exact migration execution strategy remains implementation-specific.



---



# 44. Storage Provider Switching



Changing the active Storage Provider and migrating existing Resources are separate operations.



Provider switching may affect future Storage operations.



Migration affects existing stored Resources.



The platform must not assume that changing Provider configuration automatically migrates existing data.



Any automatic migration behavior must be explicitly defined by a future approved contract.



---



# 45. Storage Observability



The Storage Engine may expose controlled operational information such as:



* Resource stored

* Resource retrieved

* Resource deleted

* Resource copied

* Resource moved

* Provider unavailable

* Provider changed

* Migration started

* Migration completed

* Migration failed

* Storage validation failed



Operational information must not expose Provider secrets or protected Resource contents unnecessarily.



---



# 46. Storage Compatibility



Changes to the internal Storage Engine implementation must preserve the public Storage contract when the change is non-breaking.



Existing Media, Plugin, Theme, Update, API, Settings, and other approved consumers must remain compatible with supported Storage Engine versions.



Breaking changes must follow the project's versioning and migration rules.



---



# 47. Storage Engine Non-Goals



The Storage Engine does not own:



* Media business logic

* Content Resources

* User identity

* Plugin business logic

* Theme presentation

* Update validation

* Permission rules

* Authentication verification

* API routing

* Cache behavior

* Event delivery

* Business metadata



The Storage Engine is responsible for Storage Provider abstraction, Storage Resource operations, scope isolation, Provider independence, storage safety, and controlled Provider migration.



---



## Acceptance Criteria



* [x] Storage security boundary defined.

* [x] Storage authorization defined.

* [x] Provider credential protection defined.

* [x] Provider availability handling defined.

* [x] Storage failure handling defined.

* [x] Storage failure isolation defined.

* [x] Storage Provider migration defined.

* [x] Migration validation defined.

* [x] Migration failure handling defined.

* [x] Provider switching boundary defined.

* [x] Storage observability defined.

* [x] Storage compatibility defined.

* [x] Storage Engine non-goals defined.



---









---



# 48. Final Storage Resolution Rules



The Storage Engine must process Storage operations through approved public interfaces.



The general Storage operation flow is:



1\. Receive the Storage request.

2\. Resolve the Storage Scope.

3\. Validate the requested operation.

4\. Resolve the applicable Storage Provider.

5\. Resolve the Storage Resource or destination.

6\. Evaluate required authorization.

7\. Execute the Provider operation.

8\. Validate the Provider result.

9\. Build the normalized Storage result.

10\. Return the result to the owning Engine or Plugin.



The Storage Engine must preserve provider independence throughout the operation.



---



# 49. Storage Resource Contract



Every managed Storage Resource must follow an approved Storage contract.



The contract must define:



* Storage Resource identity

* Storage Scope

* Owning component

* Applicable Provider

* Required metadata

* Supported operations

* Access requirements

* Lifecycle requirements

* Compatibility requirements



Consumers must not depend on undocumented Provider-specific behavior.



---



# 50. Storage Provider Contract



Every supported Storage Provider must implement the normalized Storage Engine interface.



A Provider must support only the operations declared by its approved contract.



Provider behavior must be translated into normalized Storage results.



A Provider must not require unrelated Engines or Plugins to depend directly on:



* Provider SDKs

* Provider-specific paths

* Provider-specific object identifiers

* Provider-specific authentication mechanisms

* Provider-specific error formats



Provider-specific implementation must remain isolated behind the Storage Engine.



---



# 51. Storage Scope Contract



Storage Scope must remain explicit and isolated.



Every Storage Resource must belong to an approved Scope.



The Storage Engine must prevent unrelated scopes from silently sharing protected Resources.



The preferred boundary is:



Resource Owner

→ Approved Storage Scope

→ Storage Engine

→ Storage Provider



Cross-scope operations must be explicitly supported and authorized.



---



# 52. Media Storage Contract



The Media Engine may use the Storage Engine for underlying Media files.



The required ownership boundary is:



Media Engine

→ Owns Media Resource lifecycle and Media metadata.



Storage Engine

→ Owns storage coordination.



Storage Provider

→ Owns Provider-specific file or object handling.



A Storage Provider change must not require rewriting Media business logic.



---



# 53. Plugin Storage Contract



Plugins may use Storage only through approved interfaces.



A Plugin must:



* Use an approved Plugin Storage Scope.

* Access only authorized Storage Resources.

* Preserve Storage Resource ownership boundaries.

* Use normalized Storage references.

* Handle Storage failures safely.



A Plugin must not:



* Access another Plugin's private Storage Scope.

* Depend directly on Provider-specific APIs.

* Modify Core files.

* Delete unrelated Resources.

* Bypass Permission rules.

* Expose Provider credentials.



---



# 54. Storage Deletion Contract



Storage deletion must be explicit, validated, and scoped.



Before deletion, the Storage Engine must:



1\. Resolve the Storage Resource.

2\. Resolve the correct Provider.

3\. Resolve the applicable Scope.

4\. Evaluate authorization when required.

5\. Confirm that the requested operation targets the intended Resource.

6\. Perform the deletion.

7\. Return a normalized result.



Deleting a Storage Resource must not automatically delete its associated Content, Media, User, or Plugin business Resource.



The owning component remains responsible for coordinating business-resource lifecycle.



---



# 55. Storage Move and Copy Contract



Copy and Move operations must preserve Storage Resource integrity.



A Copy operation must not modify the original Resource unless explicitly defined.



A Move operation must not silently lose a valid source Resource when the destination operation fails.



When Provider capabilities differ, the Storage Engine must use an approved safe implementation while preserving the public Storage contract.



---



# 56. Provider Migration Contract



Storage Provider migration must be explicit and recoverable where the migration contract supports recovery.



The preferred migration flow is:



Source Provider

→ Resolve Existing Resources

→ Copy to Destination Provider

→ Validate Destination Resources

→ Update Approved References

→ Confirm Migration

→ Remove Source Copies only when explicitly approved



The Storage Engine must not mark migration as complete until required validation succeeds.



Provider switching alone must not be treated as completed data migration.



---



# 57. Storage Security Contract



Storage operations must preserve platform security boundaries.



The Storage Engine must not expose:



* Provider credentials

* Provider secrets

* Protected filesystem paths

* Private object keys

* Another User's protected Resources

* Another Plugin's private Resources

* Core files outside approved operations



Authentication identifies the requester.



Permission evaluation determines whether protected Storage access is allowed.



Storage references alone do not grant authorization.



---



# 58. Storage Failure Contract



Storage operations must fail safely.



A Storage failure must not automatically:



* Corrupt Media metadata.

* Corrupt Content.

* Corrupt User data.

* Corrupt another Plugin.

* Delete unrelated Storage Resources.

* Replace valid references with invalid references.

* Expose Provider credentials.

* Report failed writes as successful.

* Report failed migration as complete.

* Crash Core.

* Crash the Admin environment.

* Crash the public site.



Controlled failure results must be returned whenever possible.



---



# 59. Codex Implementation Rules



When implementing the Storage Engine, Codex must:



* Follow the frozen architecture from Documents 001–026.

* Follow the defined folder structure.

* Use approved public interfaces.

* Preserve Storage Provider abstraction.

* Preserve Storage Scope isolation.

* Preserve Media Engine ownership.

* Preserve Plugin isolation.

* Preserve Theme Engine boundaries.

* Preserve Update Engine boundaries.

* Preserve Settings Engine boundaries.

* Preserve Permission Engine boundaries.

* Preserve Authentication Engine boundaries.

* Preserve API Engine boundaries.

* Preserve Cache Engine boundaries.

* Preserve Event Engine boundaries.

* Use normalized Storage references.

* Keep Provider-specific logic inside Provider implementations.

* Validate write, move, copy, and delete operations.

* Preserve valid source data when a Move or migration fails where possible.

* Keep Provider switching separate from Resource migration.

* Never treat possession of a Storage Identifier as authorization.

* Never expose Provider credentials through public APIs, logs, Events, Notifications, Themes, or Rendering Context.

* Never allow Plugins to access another Plugin's private Storage Scope.

* Never allow normal Storage operations to modify Core files.

* Never hard-code one Storage Provider as the only architectural option.

* Never require unrelated Engines or Plugins to use Provider-specific SDKs directly.

* Never invent undocumented automatic migration behavior.

* Never report partial Provider migration as complete.



If an implementation detail is not defined by this document, Codex must not silently introduce a conflicting Storage architecture.



---



# 60. Final Acceptance Criteria



* [x] Storage Engine purpose defined.

* [x] Storage Resource defined.

* [x] Storage Identifier defined.

* [x] Storage Provider defined.

* [x] Storage Provider contract defined.

* [x] Storage Scope defined.

* [x] Storage path boundary defined.

* [x] Provider independence defined.

* [x] File storage defined.

* [x] Storage validation defined.

* [x] Storage write result defined.

* [x] File retrieval defined.

* [x] Storage existence check defined.

* [x] File deletion defined.

* [x] Deletion safety defined.

* [x] File copy defined.

* [x] File move defined.

* [x] Storage metadata defined.

* [x] Media Engine integration defined.

* [x] Media Storage Reference defined.

* [x] Plugin Engine integration defined.

* [x] Plugin Storage isolation defined.

* [x] Theme Engine boundary defined.

* [x] Update Engine integration defined.

* [x] Settings Engine integration defined.

* [x] Permission Engine integration defined.

* [x] Authentication Engine integration defined.

* [x] API Engine integration defined.

* [x] Event Engine integration defined.

* [x] Cache Engine integration defined.

* [x] Storage Resource integrity defined.

* [x] Storage isolation defined.

* [x] Storage security boundary defined.

* [x] Storage authorization defined.

* [x] Provider credential protection defined.

* [x] Provider availability handling defined.

* [x] Storage failure handling defined.

* [x] Storage failure isolation defined.

* [x] Storage Provider migration defined.

* [x] Migration validation defined.

* [x] Migration failure handling defined.

* [x] Provider switching boundary defined.

* [x] Storage observability defined.

* [x] Storage compatibility defined.

* [x] Storage Resource contract defined.

* [x] Storage Scope contract defined.

* [x] Media Storage contract defined.

* [x] Plugin Storage contract defined.

* [x] Storage deletion contract defined.

* [x] Move and Copy contract defined.

* [x] Provider migration contract defined.

* [x] Storage security contract defined.

* [x] Storage failure contract defined.

* [x] Codex implementation rules defined.



---



# 61. Document Status



This document defines the Storage Engine specification for Favorite CMS.



The Storage Engine must be implemented according to this document and the frozen architecture established by Documents 001–026.



The Storage Engine provides controlled Storage Provider abstraction, Resource storage, retrieval, deletion, copy, move, scope isolation, provider independence, security, failure handling, and Provider migration coordination.



The Storage Engine must remain separate from business-resource ownership.



Media, Plugins, Themes, and other platform systems may use Storage through approved interfaces without depending directly on Provider-specific implementation.



Local development storage and production object storage may use different Provider implementations while preserving the same Storage Engine contract.



No single Storage Provider, object-storage vendor, SDK, filesystem implementation, external storage service, or Provider-specific technology is required by this document unless another approved architecture specification explicitly defines one.



Any future breaking change to the Storage Engine must follow the project's versioning and migration rules.



---



End of Document



Next Document:



028-localization-engine.md



