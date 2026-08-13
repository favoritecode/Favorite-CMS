# Favorite CMS



Document ID: 013



Title: Media Engine



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



Next Document:

014-search-engine.md



---



# 1. Purpose



This document defines the architecture, responsibilities, boundaries, and public interfaces of the Favorite CMS Media Engine.



The Media Engine is responsible for managing media resources used by the CMS and providing normalized media information to other platform Engines.



The Media Engine must provide a stable media contract without taking ownership of business-specific logic that belongs to individual Plugins.



---



# 2. Media Engine Objectives

The Media Engine must provide a controlled foundation for:

- Media Resource Management
- Media Identification
- Media Metadata
- Media Upload Handling
- Media Retrieval
- Media Update
- Media Deletion
- Media Validation
- Media Resolution
- Media Access Control
- Media Processing Integration
- Media Delivery Integration
- Platform Storage Integration

The Media Engine owns Media Resource lifecycle and Media metadata.

Physical file storage and Storage Provider abstraction must remain behind the approved platform Storage abstraction rather than being implemented as provider-specific storage inside the Media Engine.

Media processing implementation must remain behind approved Media Engine interfaces.

---

# 3. Media Resource



A Media Resource represents a managed media item available to the CMS.



A Media Resource may represent:



- Image

- Video

- Audio

- Document

- Other supported media formats



A Media Resource may contain:



- Unique identifier

- Media type

- File information

- Metadata

- Resource location reference

- Creation information

- Update information

- Access information



The exact fields depend on the supported media contract.



---



# 4. Media Type



The Media Engine must identify the type of each Media Resource.



Supported media types may include:



- Image

- Video

- Audio

- Document



Additional media types may be supported through approved platform extensions.



A Media Type must be validated before the Media Resource is accepted.



---



# 5. Media Metadata



The Media Engine may maintain generic metadata for a Media Resource.



Metadata may include:



- File name

- Media type

- File size

- MIME type

- Dimensions when applicable

- Duration when applicable

- Creation information

- Update information



Metadata must describe the Media Resource and must not contain business-specific logic.



---



# 6. Media Ownership



The Media Engine owns the generic lifecycle and management of Media Resources.



Business-specific usage remains with the responsible Plugin or Content Type.



For example:



Content or Plugin

→ References media



Media Engine

→ Manages the media resource



Rendering Engine

→ Determines how the media is presented



The Media Engine must not implement business-specific behavior merely because a Plugin uses a particular media type.



---



# 7. Media Validation



The Media Engine must validate a Media Resource before accepting it.



Validation may include:



- Media Type validation

- File information validation

- Supported format validation

- Metadata validation

- Access validation

- Processing requirements



Invalid Media Resources must be rejected before they enter the normal Media Engine lifecycle.



Validation rules must be deterministic.



---



# 8. Media Resolution



The Media Engine must provide a public interface for resolving Media Resources.



A resolution operation may identify media by:



- Media identifier

- Approved resource reference

- Content relationship

- Other supported media references



The Media Engine must return normalized media information.



The Media Engine must not render Theme templates, layouts, components, or widgets.



---



# 9. Content and Media Boundary



The Content Engine manages Content Resources.



The Media Engine manages Media Resources.



A Content Resource may reference a Media Resource when supported by the content contract.



The Content Engine must not take ownership of media storage or media processing.



The Media Engine must not take ownership of Content lifecycle operations.



The boundary is:



Content Engine

→ Content



Media Engine

→ Media



Rendering Engine

→ Presentation



---



## Acceptance Criteria



- [x] Media Engine purpose defined.

- [x] Media Engine objectives defined.

- [x] Media Resource defined.

- [x] Media Type defined.

- [x] Media Metadata defined.

- [x] Media ownership defined.

- [x] Media validation defined.

- [x] Media resolution defined.

- [x] Content and Media boundaries defined.



---









---



# 10. Media Upload

The Media Engine must provide a controlled interface for accepting new Media Resources.

An upload operation must:

1\. Receive the media input.
2\. Validate the media information.
3\. Determine the Media Type.
4\. Validate the supported format.
5\. Apply required access rules.
6\. Coordinate approved storage through the platform Storage abstraction when a physical file must be stored.
7\. Create or finalize the Media Resource according to the applicable lifecycle contract.
8\. Associate an approved Storage Reference when applicable.
9\. Return a normalized Media Resource reference.

An invalid upload must be rejected before it becomes an active Media Resource.

The Media Engine must not expose Storage Provider details, provider-specific paths, credentials, SDK identifiers, or private Storage Engine implementation details through the upload interface.

---

# 11. Media Storage Boundary

The Media Engine owns the logical lifecycle, identity, metadata, access rules, and business-neutral management of Media Resources.

Physical file or object storage is owned by the approved platform Storage abstraction.

The preferred boundary is:

Media Engine

→ Approved Storage Engine Interface

→ Storage Provider

The Media Engine may associate a Media Resource with an approved Storage Reference.

The Media Engine must not implement a competing provider-specific storage layer.

Consumers must interact with Media Resources through the Media Engine's public interfaces and must not depend directly on Storage Provider APIs or internal storage paths.

The Media Engine must not require Content, Theme, Rendering, or Plugin code to access private storage implementation details.

---

# 12. Media Retrieval



The Media Engine must provide controlled retrieval of Media Resources.



A retrieval operation may return:



- Media identifier

- Media Type

- Metadata

- Resource reference

- Delivery information when supported



Retrieval must respect access rules.



A caller must not receive a protected Media Resource without the required permission.



---



# 13. Media Update



Media metadata and other supported Media Resource properties may be updated through the Media Engine.



An update must:



1\. Resolve the Media Resource.

2\. Verify access.

3\. Validate the requested changes.

4\. Apply the valid changes.

5\. Return the updated Media Resource.



A failed update must not leave the Media Resource in a partially invalid state.



---



# 14. Media Deletion



Media deletion must be controlled by the Media Engine.



Before deletion, the system must verify:



- Media Resource existence

- Access permissions

- Media lifecycle requirements

- Required dependency rules when applicable



A deletion operation must not silently remove unrelated Content Resources, Theme resources, or Plugin resources.



Any relationship between Content and Media must be handled according to the approved Content Engine contract.



---



# 15. Media Processing



The Media Engine may provide controlled integration with media processing capabilities.



Processing may be applicable to supported media types.



Examples may include:



- Image preparation

- Thumbnail preparation

- Media metadata extraction

- Format-specific processing



Processing must occur only after the Media Resource has passed the required validation.



The exact processing implementation is not defined by this document.



No specific processing library or external provider is required by this contract.



---



# 16. Media Delivery

The Media Engine may provide a normalized delivery reference for a Media Resource.

Delivery information may be consumed by:

- Rendering Engine
- Content presentation
- Theme resources
- Approved Plugins

The Media Engine may resolve approved delivery information through Storage Engine or other approved delivery interfaces when applicable.

Consumers must not be required to know the underlying Storage Provider, provider-specific object key, SDK identifier, or internal storage location.

The Rendering Engine remains responsible for deciding how a Media Resource is presented.

---

# 17. Media and Rendering Integration



The Rendering Engine may request Media Resources from the Media Engine.



The integration boundary is:



Media Engine

→ Resolves media and provides media information



Rendering Engine

→ Uses the resolved media during presentation



Theme Engine

→ Determines Theme-level presentation



Plugin Engine

→ Provides Plugin functionality



The Media Engine must not select Theme templates, layouts, components, or widgets.



---



# 18. External Media References



The platform may support references to externally hosted media when such behavior is explicitly supported by the Media contract.



An external reference must not be treated as an internally stored Media Resource unless it has been registered or normalized through the appropriate interface.



External media integration must not bypass:



- Access rules

- Validation rules

- Resource safety rules

- Rendering boundaries



---



## Acceptance Criteria



- [x] Media upload defined.

- [x] Storage boundary defined.

- [x] Media retrieval defined.

- [x] Media update defined.

- [x] Media deletion defined.

- [x] Media processing boundary defined.

- [x] Media delivery boundary defined.

- [x] Rendering integration defined.

- [x] External media reference boundary defined.



---









---



# 19. Media Access Control



The Media Engine must enforce access rules for Media Resources.



Access control may depend on:



- Media ownership

- Media Resource permissions

- Resource visibility

- Caller context

- Plugin or Content integration rules



A protected Media Resource must not be returned to an unauthorized caller.



Access control must be enforced by the Media Engine and must not depend solely on the Rendering Engine.



---



# 20. Media Resource Integrity



The Media Engine must preserve the integrity of Media Resources.



A successful Media operation must produce a valid Media Resource.



A failed operation must not leave a Media Resource in a partially invalid state.



The Media Engine must not silently replace or modify unrelated Media Resources.



---



# 21. Media Processing Failure



If a supported media-processing operation fails, the failure must be handled in a controlled manner.



The Media Engine must not report a processing operation as successful when the required result was not produced.



A processing failure must not corrupt the original valid Media Resource.



Where a safe fallback exists, the Media Engine may continue using the valid original resource.



---



# 22. Media Delivery Failure



If a Media Resource cannot be delivered through its configured delivery mechanism, the Media Engine must return a controlled failure result.



The failure must not expose:



- Internal storage paths

- Private implementation details

- Credentials

- Secrets

- Sensitive system information



The failure must not modify the underlying Media Resource.



---



# 23. Media Deletion Safety



Deletion must not remove a Media Resource while an operation is still relying on it unless the applicable lifecycle contract explicitly permits that behavior.



Where content or other resources reference media, deletion behavior must respect the approved relationship rules.



The Media Engine must not silently delete unrelated resources.



---



# 24. Media Cache Boundary



The Media Engine may support caching of approved media metadata or delivery information.



Any Media Engine cache must remain separate from the Rendering Engine's render cache.



The cache must respect access-control requirements.



A cached Media Resource must not be returned to an unauthorized caller.



No specific caching technology is mandated by this document.



---



# 25. Media and Content Relationship



A Content Resource may reference one or more Media Resources when supported by the Content contract.



The relationship must use stable Media Resource references.



The Content Engine remains responsible for Content lifecycle operations.



The Media Engine remains responsible for Media Resource management.



Neither Engine may bypass the other's public contract.



---



# 26. Media and Plugin Integration



Plugins may use Media Resources through approved Media Engine interfaces.



A Plugin may:



- Create supported media references.

- Resolve Media Resources.

- Provide media-related metadata required by its content contract.

- Request supported media processing.



A Plugin must not:



- Access private Media or Storage internals.

- Bypass Media validation.

- Bypass Media access control.

- Modify Media Engine internals.



---



# 27. Media and Theme Integration



Themes may consume Media Resources through approved interfaces.



A Theme may use media for presentation purposes such as:



- Images

- Thumbnails

- Video

- Audio



The Theme must not access private Media or Storage internals.



The Theme must not modify Media Resource ownership or lifecycle.



The Rendering Engine remains responsible for composing media into the final presentation.



---



# 28. Media Engine Non-Goals



The Media Engine does not own:



- Content lifecycle

- Theme configuration

- Template rendering

- Layout rendering

- Component rendering

- Widget rendering

- Plugin business logic

- Search indexing

- User authentication implementation



Those responsibilities remain with their respective Engines or platform systems.



---



## Acceptance Criteria



- [x] Media access control defined.

- [x] Media Resource integrity defined.

- [x] Media processing failure handling defined.

- [x] Media delivery failure handling defined.

- [x] Media deletion safety defined.

- [x] Media cache boundary defined.

- [x] Content and Media relationship defined.

- [x] Plugin integration boundary defined.

- [x] Theme integration boundary defined.

- [x] Media Engine non-goals defined.



---









---



# 29. Media Security Boundary



The Media Engine must preserve the security boundaries defined by Core and the Extension System.



Media operations must respect:



- Access permissions

- Resource ownership

- Media validation

- Approved storage interfaces

- Approved processing interfaces



A Media Resource must not expose protected information through public media responses.



The Media Engine must not expose internal storage paths, credentials, secrets, or private implementation details.



---



# 30. Media Resource Isolation



A Media Resource must remain isolated from unrelated resources.



An operation on one Media Resource must not unintentionally modify:



- Another Media Resource

- Content Resources

- Theme Resources

- Plugin Resources

- Rendering Resources



Media processing must operate only on the resource explicitly provided to the operation.



---



# 31. Media Processing Boundary



Media processing must remain separated from Media Resource management.



The Media Engine may coordinate processing, but processing implementations must use approved interfaces.



A processing implementation must not directly modify unrelated CMS resources.



If processing produces a derived media result, that result must be associated with the appropriate Media Resource through the Media Engine contract.



---



# 32. Media Metadata Consistency



Media metadata must remain consistent with the Media Resource it describes.



When relevant media information changes, dependent metadata must not remain silently inconsistent.



Metadata extraction or update failures must be handled as controlled failures.



The Media Engine must not report metadata as valid when the required metadata operation has failed.



---



# 33. Media Delivery and Presentation Boundary



The Media Engine provides media information or delivery references.



The Rendering Engine determines how that media is presented.



For example, the same Media Resource may be presented as:



- Image

- Thumbnail

- Video

- Audio



depending on the presentation context.



The Media Engine must not contain Theme-specific presentation logic.



---



# 34. Media Extension Points



The Media Engine may expose controlled extension points for approved Plugins.



Extensions may provide:



- Additional supported media types

- Media metadata handlers

- Processing integrations

- Delivery integrations

- Media-related validation rules



Extensions must use public Media Engine interfaces.



An Extension must not bypass Media Engine validation or access control.



---



# 35. Media Compatibility



Changes to internal Media Engine implementation must preserve the public Media contract when the change is non-breaking.



A Media Resource created under a valid supported contract must remain processable through compatible versions of the Media Engine.



Breaking changes must follow the project's versioning and migration rules.



---



# 36. Media Failure Recovery



When a Media operation fails, the Media Engine must prefer preserving the last valid Media Resource state.



Examples:



- Failed upload → no invalid active resource.

- Failed metadata update → preserve valid metadata.

- Failed processing → preserve original valid media.

- Failed delivery → return controlled failure.

- Failed deletion → preserve the resource when deletion did not complete.



The exact recovery mechanism is implementation-specific.



---



# 37. Media Engine Implementation Contract

An implementation of the Media Engine must provide the behavior defined by this document.

The implementation must support:

- Media Resource management
- Media Type handling
- Media validation
- Upload coordination
- Retrieval
- Update
- Deletion
- Media resolution
- Access control
- Processing integration
- Delivery integration
- Approved platform Storage integration
- Content integration
- Plugin integration
- Theme integration
- Controlled failure handling

Internal Media Engine classes and services may change as long as the public Media contract remains compatible.

Storage Provider mechanisms are not owned by the Media Engine and must remain behind the approved platform Storage abstraction.

Changing Storage Provider implementation must not require unrelated Media business logic or consuming components to change when the public contracts remain compatible.

---

## Acceptance Criteria

- [x] Media security boundary defined.
- [x] Media Resource isolation defined.
- [x] Media processing boundary defined.
- [x] Media metadata consistency defined.
- [x] Media delivery and presentation boundary defined.
- [x] Platform Storage integration boundary defined.
- [x] Media extension points defined.
- [x] Media compatibility defined.
- [x] Media failure recovery defined.
- [x] Media Engine implementation contract defined.

---

# 38. Final Media Resolution Rules



The Media Engine must resolve Media Resources through approved public interfaces.



The resolution process must:



1\. Identify the requested Media Resource.

2\. Validate the Media Type.

3\. Verify access permissions.

4\. Resolve the Media Resource.

5\. Return normalized media information.



The Media Engine must not bypass validation or access-control rules during resolution.



---



# 39. Media Resource Lifecycle Rule



All Media Resource operations must preserve a valid resource state.



The lifecycle must support the operations defined by the Media Engine contract, including:



- Create

- Retrieve

- Update

- Delete

- Resolve



Processing and delivery operations must not silently alter the ownership or lifecycle of the Media Resource.



---



# 40. Media Type Rule



Supported Media Types must be handled through a stable Media Type contract.



The initial generic contract supports:



- Image

- Video

- Audio

- Document



Additional Media Types may be introduced through approved extensions.



An unsupported Media Type must be rejected safely.



---



# 41. Content Integration Rule



Content may reference Media Resources through stable Media references.



The Content Engine remains responsible for Content.



The Media Engine remains responsible for Media.



The Rendering Engine consumes the resolved media information when constructing presentation output.



No Engine may bypass another Engine's public contract to access private implementation details.



---



# 42. Theme and Plugin Integration Rule



Themes and Plugins may consume Media Resources through approved interfaces.



Themes must use Media Resources for presentation without taking ownership of their lifecycle.



Plugins may integrate Media Resources into their functionality without bypassing:



- Media validation

- Media access control

- Media resource integrity

- Public Media interfaces



---



# 43. Storage Abstraction Rule

Consumers must never depend directly on the physical Storage Provider implementation.

The Media Engine must use the approved platform Storage abstraction for physical Media file or object storage.

The Media Engine owns Media Resource lifecycle and Media metadata.

The Storage Engine owns storage coordination and Storage Provider abstraction.

Preferred architecture:

Media Engine

→ Storage Engine

→ Storage Provider

Changing the Storage Provider must not require unrelated Content, Theme, Rendering, Plugin, or Media business logic to change when the public Media and Storage contracts remain compatible.

---

# 44. Processing Abstraction Rule



Media processing implementations must remain replaceable behind approved interfaces.



The Media Engine must not require consumers to depend on a specific processing library or provider.



A processing implementation may change without changing the public Media contract when the behavior remains compatible.



---



# 45. Delivery Abstraction Rule

Media delivery behavior must remain behind approved Media delivery interfaces.

Consumers should receive a normalized delivery reference or Media information rather than depending on Storage Provider paths, internal object keys, or provider-specific SDK identifiers.

The Media Engine may coordinate with the Storage Engine or another approved delivery component to obtain delivery information.

The Rendering Engine determines how the resolved Media Resource is presented.

---

# 46. Codex Implementation Rules

When implementing the Media Engine from this specification, Codex must:

- Follow the frozen architecture from Documents 001–012.
- Follow the defined folder structure.
- Use approved public interfaces.
- Preserve Media Resource isolation.
- Preserve Media validation.
- Preserve access-control boundaries.
- Preserve Content and Media separation.
- Preserve Theme and Plugin isolation.
- Preserve Media Engine ownership of Media lifecycle and Media metadata.
- Use the approved platform Storage abstraction for physical Media storage.
- Keep Storage Provider-specific logic outside the Media Engine.
- Use normalized Storage References when physical Media storage is involved.
- Keep processing implementation behind approved Media interfaces.
- Keep delivery implementation behind approved interfaces.
- Avoid inventing business-specific media behavior inside the Media Engine.

Codex must not create a second Storage Provider abstraction inside the Media Engine when the platform Storage abstraction exists.

If an implementation detail is not defined by this document, Codex must not silently introduce a conflicting architecture.

---

# 47. Final Acceptance Criteria



- [x] Media Engine purpose defined.

- [x] Media Engine objectives defined.

- [x] Media Resource defined.

- [x] Media Types defined.

- [x] Media Metadata defined.

- [x] Media ownership defined.

- [x] Media validation defined.

- [x] Media upload defined.

- [x] Media retrieval defined.

- [x] Media update defined.

- [x] Media deletion defined.

- [x] Media resolution defined.

- [x] Media processing boundary defined.

- [x] Media delivery boundary defined.

- [x] Platform Storage abstraction integration defined.

- [x] Processing abstraction defined.

- [x] Delivery abstraction defined.

- [x] Media access control defined.

- [x] Media Resource integrity defined.

- [x] Media failure handling defined.

- [x] Media cache boundary defined.

- [x] Content integration defined.

- [x] Theme integration defined.

- [x] Plugin integration defined.

- [x] Extension points defined.

- [x] Compatibility rules defined.

- [x] Implementation contract defined.

- [x] Codex implementation rules defined.



---



# 48. Document Status

This document defines the Media Engine specification for Favorite CMS.

The Media Engine must be implemented according to this document and the frozen architecture established by Documents 001–012.

This document defines generic Media Engine responsibilities.

Business-specific media behavior must remain within the responsible Plugin or Engine.

The Media Engine owns Media Resource lifecycle and Media metadata, while physical storage and Storage Provider abstraction belong to the approved platform Storage capability.

No specific storage provider, processing library, or external media service is required by this document unless another approved architecture document explicitly defines one.

Any future breaking change to the Media Engine must follow the project's versioning and migration rules.

---

End of Document

Next Document:

014-search-engine.md
