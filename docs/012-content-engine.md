# Favorite CMS



Document ID: 012



Title: Content Engine



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



Next Document:

013-media-engine.md



---



# 1. Purpose



This document defines the architecture, responsibilities, lifecycle, and public interfaces of the Favorite CMS Content Engine.



The Content Engine is responsible for managing platform-level content operations and providing normalized content resources to other platform Engines.



The Content Engine must provide a consistent content contract without taking ownership of business-specific logic that belongs to individual Plugins.



---



# 2. Content Engine Objectives



The Content Engine must provide:



- Content Type Management

- Content Resource Management

- Content Creation

- Content Retrieval

- Content Update

- Content Deletion

- Content Status Management

- Content Lifecycle Management

- Content Metadata Management

- Content Resolution

- Content Validation

- Content Query Interfaces



The Content Engine must expose content through defined public interfaces.



---



# 3. Content Ownership



The Content Engine owns the generic content lifecycle and content access rules.



Business-specific behavior remains with the responsible Plugin or Engine.



For example:



- Blog-specific behavior → Blog Plugin

- Movie-specific behavior → Movie Plugin

- Shop-specific behavior → Shop Plugin



The Content Engine must not contain business-specific rules for individual domains.



The Content Engine provides the common content foundation required by those domains.



---



# 4. Content Resource



A Content Resource represents a managed piece of content that can be created, retrieved, updated, published, archived, or otherwise processed through the Content Engine.



A Content Resource may contain:



- Unique identifier

- Content type

- Title or label

- Content data

- Metadata

- Status

- Author or owner reference

- Creation information

- Update information

- Publication information



The exact fields may vary according to the registered Content Type.



---



# 5. Content Types



The Content Engine must support multiple Content Types.



A Content Type defines the structure and behavior contract required for a particular category of content.



Examples may include:



- Page

- Post

- Article

- Product

- Movie

- Episode



Domain-specific Content Types may be registered by approved Plugins.



The Content Engine must not require every Content Type to use the same business-specific fields.



---



# 6. Content Type Registration



Content Types provided by Plugins must be registered through approved public interfaces.



A Content Type registration may define:



- Content Type identifier

- Display name

- Field definitions

- Validation rules

- Status capabilities

- Query capabilities

- Metadata requirements

- Rendering information



Invalid or incomplete Content Type registrations must be rejected.



Content Type registration must not require modification of Core source code.



---



# 7. Content Lifecycle



The Content Engine must provide a predictable content lifecycle.



A typical lifecycle may include:



- Draft

- Published

- Archived



Additional lifecycle states may be supported when required by a registered Content Type.



Lifecycle transitions must follow validation and permission rules.



A Content Resource must not enter an invalid state through normal Content Engine operations.



---



# 8. Content Resolution



The Content Engine must provide a public interface for resolving Content Resources required by other Engines.



The Rendering Engine may request a Content Resource through this interface.



The Content Engine must return normalized content information to the caller.



The Content Engine must not render templates, layouts, components, or widgets.



Rendering remains the responsibility of the Rendering Engine.



---



# 9. Content and Rendering Boundary



The Content Engine provides content data.



The Rendering Engine decides how that content is presented.



Therefore:



Content Engine

→ Provides content



Rendering Engine

→ Resolves and renders presentation resources



Theme Engine

→ Provides Theme resources



Plugin Engine

→ Provides Plugin functionality



No Engine should bypass these ownership boundaries merely to simplify an implementation.



---



## Acceptance Criteria



- [x] Content Engine purpose defined.

- [x] Content Engine objectives defined.

- [x] Content ownership defined.

- [x] Content Resource defined.

- [x] Content Types defined.

- [x] Content Type registration defined.

- [x] Content lifecycle defined.

- [x] Content resolution defined.

- [x] Content and Rendering boundaries defined.



---









---



# 10. Content Validation



The Content Engine must validate a Content Resource before accepting an operation.



Validation may include:



- Content Type validation

- Required field validation

- Field type validation

- Content state validation

- Metadata validation

- Permission validation

- Content Type-specific validation rules



Validation must occur before an invalid Content Resource is persisted or transitioned into an invalid lifecycle state.



Content Type-specific validation rules must be provided through approved Content Type interfaces.



The Content Engine must not bypass registered validation rules.



---



# 11. Content Operations



The Content Engine must provide controlled operations for Content Resources.



Supported operations may include:



- Create

- Read

- Update

- Delete

- Publish

- Archive

- Resolve



Each operation must respect:



- Content Type rules

- Lifecycle rules

- Validation rules

- Permission rules

- Ownership boundaries



The implementation must not allow an operation to bypass the Content Engine's validation and lifecycle contracts.



---



# 12. Content Retrieval



The Content Engine must provide a normalized retrieval interface.



A retrieval operation may identify content by:



- Content identifier

- Content Type

- Route-resolved resource identifier

- Other approved resource identifiers



The returned Content Resource must contain only the data permitted by the caller's access context.



The Content Engine must not expose private internal storage details through its public content interface.



---



# 13. Content Query



The Content Engine may provide a query interface for retrieving multiple Content Resources.



A query may support:



- Content Type filtering

- Status filtering

- Identifier filtering

- Field-based filtering

- Ordering

- Pagination



Query behavior must be deterministic according to the defined query contract.



Plugins may provide additional domain-specific query behavior through approved interfaces without changing the generic Content Engine contract.



---



# 14. Content Update



Content updates must pass through the Content Engine's validation process.



An update must:



1\. Resolve the target Content Resource.

2\. Verify access permissions.

3\. Validate the requested changes.

4\. Validate the resulting Content Resource.

5\. Apply the update.

6\. Produce the updated Content Resource.



A failed update must not leave the Content Resource in a partially invalid state.



---



# 15. Content Deletion



Content deletion must be controlled by the Content Engine.



Before deletion, the system must verify:



- Content existence

- Content Type rules

- Permission requirements

- Lifecycle restrictions

- Required dependencies when applicable



If deletion is not permitted, the operation must fail without corrupting the Content Resource.



The Content Engine must not silently delete related resources unless such behavior is explicitly defined by the responsible contract.



---



# 16. Content Publishing



Publishing is a lifecycle transition.



A Content Resource may be published only when:



- The Content Resource exists.

- The Content Type permits publication.

- Required validation succeeds.

- Required permissions are satisfied.

- Required publication conditions are satisfied.



Publishing must produce a valid published Content Resource.



The Content Engine must not perform rendering as part of publishing.



Rendering remains the responsibility of the Rendering Engine.



---



# 17. Content Archiving



Archiving removes a Content Resource from normal active content availability without requiring the Rendering Engine to own the lifecycle operation.



An archived Content Resource must not be treated as normally published content unless the Content Type explicitly defines such behavior.



Archiving must respect Content Type and permission rules.



---



# 18. Content Metadata



The Content Engine may maintain generic metadata associated with a Content Resource.



Metadata may include:



- Creation information

- Update information

- Publication information

- Author or owner reference

- Content Type information

- Lifecycle information



Metadata must remain separate from business-specific fields unless the Content Type explicitly defines the relationship.



---



## Acceptance Criteria



- [x] Content validation defined.

- [x] Content operations defined.

- [x] Content retrieval defined.

- [x] Content query responsibilities defined.

- [x] Content update process defined.

- [x] Content deletion boundaries defined.

- [x] Content publishing defined.

- [x] Content archiving defined.

- [x] Content metadata responsibilities defined.



---









---



# 19. Content Access Control



The Content Engine must enforce access rules for Content Resources.



Access control may depend on:



- Content ownership

- Content Type

- Content lifecycle state

- User permissions

- Plugin permissions

- Resource visibility rules



A caller must receive only the Content Resource data it is authorized to access.



Access control must be applied before protected content is returned.



The Content Engine must not rely on the Rendering Engine to enforce content permissions.



---



# 20. Content State Rules



Content state must be treated as part of the Content Resource lifecycle.



A Content Resource may have states such as:



- Draft

- Published

- Archived



Only valid state transitions may be performed.



For example:



Draft

→ Published



Published

→ Archived



The exact transition rules may be extended by an approved Content Type.



An invalid transition must be rejected without modifying the existing Content Resource.



---



# 21. Content Data Integrity



The Content Engine must preserve the integrity of Content Resources.



A successful content operation must result in a valid Content Resource.



A failed operation must not leave the resource partially modified.



Content updates must be validated before the resulting state is accepted.



The Content Engine must not silently discard valid content data during an update.



---



# 22. Content Type Isolation



A registered Content Type must remain isolated from unrelated Content Types.



A Content Type may define:



- Its own fields

- Its own validation rules

- Its own lifecycle capabilities

- Its own query requirements

- Its own metadata requirements



One Content Type must not directly modify another Content Type's internal implementation.



Cross-content relationships must use approved Content Engine interfaces.



---



# 23. Plugin Integration



Plugins may extend the Content Engine by registering approved Content Types and content-related capabilities.



A Plugin may provide:



- Content Type definitions

- Field definitions

- Validation rules

- Query capabilities

- Lifecycle capabilities

- Content resolution metadata



Plugin-provided content functionality must follow the public Content Engine contract.



A Plugin must not modify Content Engine internals directly.



---



# 24. Content Resolution Contract



When another Engine requests a Content Resource, the Content Engine must return a normalized result.



The result must provide the information required by the caller without exposing private storage implementation details.



For Rendering Engine integration, the result may contain:



- Content identifier

- Content Type

- Content data

- Content metadata

- Lifecycle state

- Rendering-related content metadata when explicitly supported



The Content Engine must not return Theme or Template resources as part of content resolution.



---



# 25. Rendering Integration



The Rendering Engine may consume Content Resources from the Content Engine.



The integration boundary is:



Content Engine

→ Resolves and provides content



Rendering Engine

→ Determines how the content is rendered



Theme Engine

→ Provides presentation resources



Plugin Engine

→ Provides Plugin functionality



The Content Engine must not select:



- Theme templates

- Layouts

- Components

- Widgets

- Rendering overrides



Those responsibilities remain within the Rendering Engine and related presentation systems.



---



# 26. Content Metadata and Presentation



Content metadata may provide information required by presentation systems.



Examples include:



- Title

- Description

- Publication information

- Update information

- Author or owner reference

- Content Type

- Labels or categorization metadata



The Content Engine provides this information as content data or metadata.



The Rendering Engine decides whether and how that information is presented.



---



## Acceptance Criteria



- [x] Content access control defined.

- [x] Content state rules defined.

- [x] Content data integrity defined.

- [x] Content Type isolation defined.

- [x] Plugin integration boundaries defined.

- [x] Content resolution contract defined.

- [x] Rendering integration boundary defined.

- [x] Content metadata and presentation responsibilities separated.



---









---



# 27. Content Cache Boundary



The Content Engine may support caching of Content Resources and approved query results.



Caching must respect:



- Content lifecycle state

- Content permissions

- Content Type

- Content updates

- Content visibility

- Caller access context



A cached Content Resource must not be returned to a caller who is not authorized to access it.



Content cache behavior must remain separate from the Rendering Engine's render cache.



The Rendering Engine is responsible for presentation-level rendering cache behavior.



---



# 28. Content Cache Invalidation



A cached Content Resource must be invalidated when a relevant content change occurs.



Possible invalidation triggers include:



- Content creation

- Content update

- Content deletion

- Publication

- Archiving

- Content Type changes that affect the resource

- Relevant metadata changes



Cache invalidation must not modify the underlying Content Resource incorrectly.



---



# 29. Content Operation Failure Handling



The Content Engine must handle failed operations in a controlled manner.



Possible failures include:



- Content not found

- Invalid Content Type

- Invalid field data

- Validation failure

- Permission failure

- Invalid lifecycle transition

- Query failure

- Storage failure



A failed operation must return a controlled failure result.



The Content Engine must not silently report success when the requested operation was not completed.



---



# 30. Failure Isolation



A failure affecting one Content Resource must not corrupt unrelated Content Resources.



A failure in one Plugin-provided Content Type must not automatically corrupt another Content Type.



A failed content operation must not modify unrelated content.



A failed content update must not leave the target resource in a partially invalid state.



---



# 31. Content Extensibility



The Content Engine must remain extensible through approved public interfaces.



Future extensions may introduce:



- Additional Content Types

- Additional fields

- Additional validation rules

- Additional lifecycle capabilities

- Additional query capabilities

- Additional metadata



Extensions must not require direct modification of the Content Engine's internal implementation.



---



# 32. Content Type Compatibility



A Content Type must declare or expose the information required for the Content Engine to process it safely.



The Content Engine must verify that a Content Type is compatible with the requested operation.



An incompatible Content Type must be rejected before the operation is executed.



Existing valid Content Types must remain compatible when non-breaking changes are introduced.



---



# 33. Content and Plugin Isolation



Plugin-provided Content Types must remain isolated from Plugin implementation details.



The Content Engine communicates with Plugins through approved interfaces.



The Content Engine must not:



- Execute private Plugin internals.

- Modify Plugin source code.

- Bypass Plugin permissions.

- Depend on undocumented Plugin implementation details.



A Plugin must not bypass Content Engine validation or lifecycle rules when using the Content Engine.



---



# 34. Content and Theme Isolation



The Content Engine must remain independent from Theme implementation.



The Content Engine may provide content metadata required for presentation, but it must not:



- Select Theme templates.

- Modify Theme resources.

- Execute Theme components.

- Control Theme layout.

- Apply Theme-specific rendering logic.



Theme presentation remains the responsibility of the Theme and Rendering systems.



---



# 35. Content and Media Boundary



Media-specific storage and processing are outside the primary responsibility of the Content Engine.



A Content Resource may reference media resources when supported by the content contract.



The Content Engine must treat such references as content relationships or metadata.



Media storage, processing, transformation, and delivery belong to the Media Engine defined by the platform.



---



# 36. Content API Boundary



The Content Engine must expose content operations through stable public interfaces.



The public interface must hide internal storage implementation details.



Internal changes to storage or implementation must not require changes to consumers when the public Content contract remains compatible.



The API boundary must preserve:



- Validation

- Permissions

- Lifecycle rules

- Content Type rules

- Data integrity



---



# 37. Content Engine Non-Goals



The Content Engine does not own:



- Theme rendering

- Template rendering

- Layout rendering

- Component rendering

- Widget rendering

- Asset processing

- Media storage

- Authentication implementation

- Plugin business logic

- Search indexing

- Rendering cache



These responsibilities belong to their respective Engines or platform systems.



---



## Acceptance Criteria



- [x] Content cache boundary defined.

- [x] Content cache invalidation defined.

- [x] Content operation failure handling defined.

- [x] Failure isolation defined.

- [x] Content extensibility defined.

- [x] Content Type compatibility defined.

- [x] Plugin isolation defined.

- [x] Theme isolation defined.

- [x] Content and Media boundary defined.

- [x] Content API boundary defined.

- [x] Content Engine non-goals defined.



---









---



# 38. Final Content Resolution Rules



The Content Engine must resolve Content Resources through the registered Content Type and the approved Content Engine interfaces.



The resolution process must:



1\. Identify the requested Content Resource.

2\. Validate the Content Type.

3\. Verify access permissions.

4\. Validate the requested operation or retrieval context.

5\. Resolve the Content Resource.

6\. Return the normalized Content Resource.



The Content Engine must not bypass Content Type validation, permissions, or lifecycle rules during resolution.



---



# 39. Content Lifecycle Rule



All lifecycle operations must follow the registered Content Type capabilities and the Content Engine validation contract.



A lifecycle operation must never:



- Skip required validation.

- Bypass permissions.

- Create an invalid state.

- Partially modify a Content Resource.

- Corrupt unrelated Content Resources.



If a lifecycle operation fails, the existing valid Content Resource must remain valid.



---



# 40. Content Type Rule



Content Types must be registered through approved interfaces.



A Content Type must provide enough information for the Content Engine to:



- Identify the type.

- Validate its content.

- Process supported operations.

- Apply lifecycle rules.

- Resolve the resource safely.



The Content Engine must reject an invalid or incompatible Content Type.



---



# 41. Extension Rule



Plugins may extend the Content Engine through approved public interfaces.



Extensions must not:



- Modify Content Engine internals.

- Bypass validation.

- Bypass permissions.

- Bypass lifecycle rules.

- Modify unrelated Content Types.



Future Content Engine capabilities must be introduced through compatible interfaces.



---



# 42. Rendering Boundary Rule



The Content Engine provides content.



The Rendering Engine renders content.



Therefore:



Content Engine

→ Content data and content metadata



Rendering Engine

→ Templates, layouts, components, slots, widgets, overrides, assets, and final presentation



The Content Engine must never take ownership of presentation resources.



---



# 43. Cache Boundary Rule



Content caching and rendering caching must remain logically separated.



The Content Engine may cache Content Resources or approved content query results.



The Rendering Engine may cache resolved presentation resources or rendered output.



A change in Content must invalidate any affected content cache and must provide the required invalidation signal or integration point for dependent rendering caches.



---



# 44. Failure Safety Rule



Content Engine failures must fail safely.



A failure must not:



- Corrupt stored content.

- Corrupt unrelated content.

- Bypass permissions.

- Produce an invalid lifecycle state.

- Silently report success.

- Modify Theme resources.

- Modify Plugin internals.

- Modify Rendering resources.



Where safe recovery is possible, the system may retry or recover according to the applicable platform contract.



---



# 45. Data Integrity Rule



The Content Engine must preserve the integrity of every successful Content operation.



The following principle is mandatory:



Valid Content Resource

→ Valid Operation

→ Valid Result



Failed Operation

→ No invalid partial state



The Content Engine must prefer a controlled failure over silently accepting inconsistent content.



---



# 46. Implementation Contract



An implementation of the Content Engine must provide the behavior defined by this document.



The implementation must support:



- Content Type registration

- Content Resource management

- Validation

- Retrieval

- Query

- Update

- Delete

- Publish

- Archive

- Content resolution

- Access control

- Lifecycle control

- Plugin integration

- Rendering integration

- Controlled failure handling



Internal implementation details may change as long as the public Content Engine contract remains compatible.



---



# 47. Codex Implementation Rules



When implementing the Content Engine from this specification, Codex must not invent business-specific Content Types or Plugin-specific logic inside the Content Engine.



Codex must:



- Follow the frozen architecture from Documents 001–011.

- Follow the defined folder structure.

- Use approved public interfaces.

- Preserve Content Type isolation.

- Preserve lifecycle validation.

- Preserve permission boundaries.

- Preserve data integrity.

- Preserve Plugin isolation.

- Preserve Theme isolation.

- Preserve the Content Engine and Rendering Engine boundary.



If an implementation detail is not defined by this document, Codex must not silently create a conflicting architecture.



The implementation must follow the existing project architecture and public contracts.



---



# 48. Final Acceptance Criteria



- [x] Content Engine purpose defined.

- [x] Content Engine objectives defined.

- [x] Content ownership defined.

- [x] Content Resource defined.

- [x] Content Types defined.

- [x] Content Type registration defined.

- [x] Content lifecycle defined.

- [x] Content validation defined.

- [x] Content operations defined.

- [x] Content retrieval defined.

- [x] Content query defined.

- [x] Content update defined.

- [x] Content deletion defined.

- [x] Content publishing defined.

- [x] Content archiving defined.

- [x] Content metadata defined.

- [x] Content access control defined.

- [x] Content data integrity defined.

- [x] Content Type isolation defined.

- [x] Plugin integration defined.

- [x] Theme isolation defined.

- [x] Media boundary defined.

- [x] Rendering integration defined.

- [x] Content cache boundary defined.

- [x] Cache invalidation responsibility defined.

- [x] Failure handling defined.

- [x] Failure isolation defined.

- [x] Extensibility defined.

- [x] Final resolution rules defined.

- [x] Implementation contract defined.

- [x] Codex implementation rules defined.



---



# 49. Document Status



This document defines the Content Engine specification for Favorite CMS.



The Content Engine must be implemented according to this document and the frozen architecture established by Documents 001–011.



This document does not define business-specific implementations for Blog, Movie, Shop, Music, Live TV, or other domains.



Those domain-specific behaviors must be implemented by their responsible Plugins or Engines through the approved Content Engine interfaces.



Any future breaking change to the Content Engine must follow the project's versioning and migration rules.



---



End of Document



Next Document:



013-media-engine.md

