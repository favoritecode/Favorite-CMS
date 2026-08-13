# Favorite CMS



Document ID: 022



Title: Menu Engine



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



Next Document:

023-seo-engine.md



---



# 1. Purpose



This document defines the architecture, responsibilities, boundaries, and public interfaces of the Favorite CMS Menu Engine.



The Menu Engine is responsible for defining, managing, resolving, and exposing structured navigation data.



The Menu Engine manages navigation structure.



It does not own final visual presentation.



Themes and the Rendering Engine remain responsible for presenting resolved Menu data.



---



# 2. Menu Engine Objectives



The Menu Engine must provide a foundation for:



* Menu Definition

* Menu Registration

* Menu Item Management

* Menu Hierarchy

* Menu Location

* Menu Resolution

* Menu Ordering

* Menu Visibility

* Plugin Menu Integration

* Theme Menu Integration

* Permission-aware Menu Resolution

* Controlled Menu Failure Handling



The exact Menu persistence mechanism remains behind approved Menu Engine interfaces.



---



# 3. Menu



A Menu represents an ordered navigation structure.



A Menu may contain:



* Navigation items

* Nested items

* Resource links

* Internal routes

* External destinations

* Plugin-defined navigation items

* Other explicitly approved navigation targets



A Menu must have a defined identity and purpose.



---



# 4. Menu Identifier



Every Menu must have a stable Menu Identifier.



The Menu Identifier may be used to:



* Retrieve the Menu

* Assign the Menu to a location

* Reference the Menu from Theme configuration

* Manage Menu Items

* Resolve Menu presentation data



The exact internal identifier format is implementation-specific.



---



# 5. Menu Item



A Menu Item represents one navigational entry within a Menu.



A Menu Item may contain:



* Menu Item Identifier

* Label

* Destination

* Parent reference

* Ordering information

* Visibility information

* Approved metadata



A Menu Item must contain only the information required for navigation behavior.



---



# 6. Menu Destination



A Menu Item may reference an approved navigation destination.



Possible destination categories may include:



* Internal route

* Content Resource

* Plugin-provided route

* External URL

* Other explicitly supported destination



The Menu Engine must not assume that every Menu Item points to Content.



Destination resolution must follow the applicable platform contract.



---



# 7. Menu Hierarchy



Menus may support hierarchical navigation.



A Menu Item may have:



* No parent

* One approved parent

* Child Menu Items



Hierarchy must remain deterministic.



The Menu Engine must prevent invalid relationships such as uncontrolled circular parent-child references.



---



# 8. Menu Ordering



Menu Items must have a deterministic ordering within their applicable Menu level.



Ordering may be controlled by approved Menu configuration.



The exact ordering representation is implementation-specific.



Changing Menu Item order must not modify the destination resource.



---



# 9. Menu Ownership Boundary



The Menu Engine owns navigation structure.



It does not own the resources referenced by Menu Items.



Therefore:



Content Engine

→ Owns Content Resources.



Plugin

→ Owns Plugin routes and business functionality.



Theme Engine

→ Owns Theme resources.



Rendering Engine

→ Owns presentation composition.



Menu Engine

→ Owns Menu structure and navigation resolution.



Deleting or changing a Menu Item must not automatically delete or modify its destination resource.



---



## Acceptance Criteria



* [x] Menu Engine purpose defined.

* [x] Menu Engine objectives defined.

* [x] Menu defined.

* [x] Menu Identifier defined.

* [x] Menu Item defined.

* [x] Menu Destination defined.

* [x] Menu Hierarchy defined.

* [x] Menu Ordering defined.

* [x] Menu ownership boundary defined.



---









---



# 10. Menu Registration



Menus must be registered through approved Menu Engine interfaces.



A Menu registration may define:



* Menu Identifier

* Menu purpose

* Applicable scope

* Supported locations

* Approved metadata



Registration must not directly control visual rendering.



The Theme Engine and Rendering Engine remain responsible for presentation.



---



# 11. Menu Item Registration



Menu Items may be created or registered through approved Menu Engine interfaces.



A Menu Item registration must define enough information to resolve:



* Menu ownership

* Item identity

* Destination

* Parent relationship when applicable

* Ordering

* Visibility requirements



Invalid Menu Items must not be added as valid navigation entries.



---



# 12. Menu Location



A Menu Location represents an approved navigation placement that may be requested by a Theme or Rendering context.



Possible locations may include conceptual areas such as:



* Primary navigation

* Secondary navigation

* Footer navigation

* User navigation

* Other explicitly registered locations



The exact location names are defined by the applicable Theme or platform contract.



The Menu Engine must not hard-code Theme-specific visual placement rules.



---



# 13. Menu Location Registration



Themes or approved platform components may register supported Menu Locations through public interfaces.



A Menu Location registration must identify:



* Location identity

* Location purpose

* Applicable owner

* Supported Menu assignment behavior



A Theme must not directly modify Menu Engine internals to create a Menu Location.



---



# 14. Menu Assignment



A registered Menu may be assigned to an approved Menu Location.



Assignment must remain separate from Menu content.



Therefore:



Menu

→ Defines navigation structure.



Menu Location

→ Defines where navigation data is requested.



Theme

→ Defines how that location is presented.



Changing a Menu assignment must not delete or modify the Menu itself unless explicitly requested through a separate operation.



---



# 15. Menu Resolution



The Menu Engine must resolve a requested Menu through approved interfaces.



The general resolution flow is:



Menu Request

→ Resolve Menu Identifier or Location

→ Resolve Assigned Menu

→ Resolve Menu Items

→ Apply Ordering

→ Apply Visibility Rules

→ Resolve Valid Destinations

→ Return Normalized Menu Data



The Rendering Engine may then use the normalized result for presentation.



---



# 16. Menu Visibility



A Menu Item may have approved visibility requirements.



Visibility may depend on:



* Public availability

* User context

* Permission state

* Plugin availability

* Resource availability

* Other explicitly defined conditions



Visibility must be resolved through approved platform contracts.



A hidden Menu Item must not be treated as deleted.



---



# 17. Permission-Aware Menu Resolution



The Menu Engine must not expose protected navigation items to unauthorized Users.



Where a Menu Item references a protected destination, applicable Permission checks must be respected.



Menu visibility is not a substitute for destination authorization.



Therefore:



Menu Item Hidden

→ Prevents presentation of the navigation entry.



Destination Authorization

→ Still determines whether the protected resource or action may be accessed.



Direct access to a protected route must not become authorized merely because a Menu Item exists.



---



# 18. Destination Availability



A Menu Item may become unavailable when its destination is no longer valid or available.



Possible causes may include:



* Resource removed

* Plugin disabled

* Route unavailable

* Permission denied

* Destination configuration invalid



The Menu Engine must handle unavailable destinations safely.



An unavailable Menu Item must not crash Menu resolution or Rendering.



The applicable policy may hide, skip, or otherwise safely handle the invalid item according to the approved contract.



---



## Acceptance Criteria



* [x] Menu registration defined.

* [x] Menu Item registration defined.

* [x] Menu Location defined.

* [x] Menu Location registration defined.

* [x] Menu assignment defined.

* [x] Menu resolution defined.

* [x] Menu visibility defined.

* [x] Permission-aware Menu resolution defined.

* [x] Destination availability handling defined.



---









---



# 19. Menu and Theme Engine



Themes may consume normalized Menu data through approved Menu Engine and Rendering Engine interfaces.



A Theme may:



* Declare supported Menu Locations.

* Request Menu data for those locations.

* Control the visual presentation of Menu Items.

* Present hierarchical navigation.



A Theme must not become the owner of Menu data.



Changing or replacing a Theme must not automatically delete stored Menus.



---



# 20. Theme Switching and Menu Preservation



Menu data should remain independent from a specific Theme package where possible.



When the active Theme changes:



* Existing Menus should remain preserved.

* Existing Menu Items should remain preserved.

* Theme-specific Menu Location assignments may require reassignment when the new Theme does not support the same locations.

* Unsupported locations must fail safely.



A Theme switch must not silently destroy navigation configuration.



---



# 21. Menu and Rendering Engine



The Rendering Engine may request resolved Menu data for presentation.



The preferred flow is:



Theme or Rendering Context

→ Requests Menu Location



Menu Engine

→ Resolves assigned Menu



Menu Engine

→ Applies hierarchy, ordering, visibility, and destination rules



Rendering Engine

→ Receives normalized Menu data



Theme

→ Presents the Menu



The Rendering Engine must not modify Menu ownership or persistence.



---



# 22. Menu and Content Engine



Menu Items may reference Content Resources through approved resource identifiers or routes.



The Menu Engine must not duplicate Content ownership.



If referenced Content becomes unavailable, the Menu Engine must handle the affected Menu Item according to its destination-availability policy.



Changing a Menu Item must not modify the referenced Content Resource.



---



# 23. Menu and Plugin Engine



Plugins may contribute approved navigation entries or destinations through public interfaces.



A Plugin may:



* Register approved Menu-related integration.

* Expose Plugin routes as valid destinations.

* Provide approved Menu Items when supported by the platform contract.



A Plugin must not:



* Modify Menu Engine internals.

* Rewrite unrelated Menus.

* Override another Plugin's private Menu configuration.

* Bypass Permission checks through navigation entries.

* Assume that installation automatically grants placement in every Menu.



Plugin-provided navigation must remain removable or unavailable when the Plugin is disabled or removed.



---



# 24. Plugin Availability and Menu Safety



A Menu Item referencing Plugin functionality must remain safe when that Plugin becomes unavailable.



Possible causes may include:



* Plugin disabled

* Plugin removed

* Plugin validation failure

* Plugin route unavailable



The Menu Engine must not allow an unavailable Plugin destination to crash Menu resolution.



The affected Menu Item may be hidden, skipped, marked unavailable, or otherwise handled according to the approved Menu contract.



---



# 25. Menu and Settings Engine



The Settings Engine may store approved Menu-related configuration when required.



Examples may include:



* Menu-to-location assignment

* Theme-related Menu configuration

* Other explicitly approved Menu preferences



The Menu Engine remains responsible for navigation structure.



The Settings Engine remains responsible for managed configuration values.



Menu Items themselves must not be converted into undocumented Settings simply for convenience.



---



# 26. Menu and Cache Engine



The Cache Engine may cache approved resolved Menu data.



A Menu change may require invalidation of affected cached Menu representations.



Possible invalidation triggers may include:



* Menu Item created

* Menu Item updated

* Menu Item removed

* Menu order changed

* Menu assignment changed

* Visibility-related state changed

* Relevant Plugin or resource availability changed



The Menu Engine remains the source of truth for Menu structure.



---



# 27. Menu and Event Engine



The Menu Engine may publish approved Events when meaningful Menu state changes occur.



Examples may conceptually include:



* Menu changed

* Menu assignment changed

* Navigation structure changed



Exact Event Names must be defined before implementation.



The Event Engine only communicates the occurrence.



The Menu Engine remains responsible for Menu state.



---



# 28. Menu Integrity



The Menu Engine must preserve structural integrity.



It must prevent invalid Menu structures such as:



* Circular parent relationships

* Item self-parenting

* Invalid Menu references

* Invalid parent references

* Duplicate conflicting identifiers

* Cross-Menu hierarchy relationships that are not explicitly supported



A failed Menu mutation must not silently corrupt the existing valid Menu structure.



---



## Acceptance Criteria



* [x] Theme Engine integration defined.

* [x] Theme switching safety defined.

* [x] Rendering Engine integration defined.

* [x] Content Engine integration defined.

* [x] Plugin Engine integration defined.

* [x] Plugin availability safety defined.

* [x] Settings Engine integration defined.

* [x] Cache Engine integration defined.

* [x] Event Engine integration defined.

* [x] Menu integrity requirements defined.



---









---



# 29. Menu Security Boundary



The Menu Engine must treat navigation configuration as controlled platform data.



Protected Menu information may include:



* Administrative navigation

* User-specific navigation

* Plugin-private navigation

* Permission-restricted destinations

* Other protected Menu configuration



The Menu Engine must not expose protected Menu Items to unauthorized contexts.



---



# 30. Menu Authorization



Menu management operations may require authorization.



Authorization may apply to:



* Creating Menus

* Updating Menus

* Deleting Menus

* Managing Menu Items

* Managing Menu Locations

* Assigning Menus to locations

* Managing protected or administrative navigation



The Permission Engine remains responsible for authorization decisions.



---



# 31. Menu Visibility and Authorization Separation



Menu visibility and resource authorization are separate responsibilities.



A Menu Item may be hidden because the current User should not see that navigation option.



However, hiding a Menu Item does not protect the destination by itself.



Therefore:



Menu Engine

→ Controls navigation visibility.



Permission Engine

→ Controls protected access.



Destination Owner

→ Enforces its own resource or route rules.



The platform must never rely on hidden navigation as the only security control.



---



# 32. Menu Lifecycle



The general Menu lifecycle is:



Create Menu

→ Add Menu Items

→ Configure hierarchy

→ Configure ordering

→ Assign Menu Location

→ Resolve Menu

→ Update when required

→ Remove when approved



Menu lifecycle operations must preserve valid navigation structure.



---



# 33. Menu Item Update



An approved Menu Item update may change:



* Label

* Destination

* Parent relationship

* Ordering

* Visibility configuration

* Approved metadata



An update must preserve Menu integrity.



Changing a Menu Item must not modify the destination resource itself.



---



# 34. Menu Item Removal



Removing a Menu Item removes the navigation entry.



It must not automatically:



* Delete Content.

* Delete Plugin data.

* Remove the destination route.

* Delete child resources referenced elsewhere.



If the removed Menu Item has child items, the handling of those child items must follow an explicit Menu contract.



The Menu Engine must not silently create invalid hierarchy after removal.



---



# 35. Menu Removal



Removing a Menu removes the navigation structure or its active registration according to the approved operation.



Menu removal must not automatically delete resources referenced by its Menu Items.



Assignments referencing a removed Menu must fail safely and must not crash Theme or Rendering operations.



---



# 36. Menu Observability



The Menu Engine may provide controlled operational information such as:



* Menu Created

* Menu Updated

* Menu Removed

* Menu Item Added

* Menu Item Updated

* Menu Item Removed

* Menu Assignment Changed

* Menu Resolution Failed

* Destination Unavailable



Operational information must not expose protected navigation data unnecessarily.



---



# 37. Menu Failure Handling



Possible Menu failures include:



* Invalid Menu Identifier

* Invalid Menu Item

* Invalid hierarchy

* Invalid parent reference

* Destination resolution failure

* Permission failure

* Menu assignment failure

* Persistence failure

* Plugin destination unavailable



A Menu failure must return a controlled result.



The Menu Engine must not silently corrupt an existing valid Menu.



---



# 38. Menu Failure Isolation



A Menu failure must remain isolated from unrelated platform resources.



For example:



Broken Plugin Menu Item

→ Must not crash the entire Menu.



Invalid destination

→ Must not corrupt Content.



Theme Menu Location failure

→ Must not delete the Menu.



Menu mutation failure

→ Must not corrupt unrelated Menus.



Graceful degradation is required where safe fallback behavior is possible.



---



# 39. Menu Compatibility



Changes to the internal Menu Engine implementation must preserve the public Menu contract when the change is non-breaking.



Existing Themes, Plugins, Rendering integrations, and Menu management consumers must remain compatible with supported Menu Engine versions.



Breaking changes must follow the project's versioning and migration rules.



---



# 40. Menu Engine Non-Goals



The Menu Engine does not own:



* Content Resources

* Plugin business logic

* Theme presentation

* Rendering composition

* Permission rules

* User identity

* Settings persistence internals

* Cache storage

* Event delivery

* Destination routes themselves



The Menu Engine is responsible for navigation structure, hierarchy, ordering, assignment, visibility resolution, and normalized Menu data.



---



## Acceptance Criteria



* [x] Menu security boundary defined.

* [x] Menu authorization defined.

* [x] Visibility and authorization separation defined.

* [x] Menu lifecycle defined.

* [x] Menu Item update defined.

* [x] Menu Item removal defined.

* [x] Menu removal defined.

* [x] Menu observability defined.

* [x] Menu failure handling defined.

* [x] Menu failure isolation defined.

* [x] Menu compatibility defined.

* [x] Menu Engine non-goals defined.



---









---



# 41. Final Menu Resolution Rules



The Menu Engine must resolve navigation through approved public interfaces.



The general Menu resolution flow is:



1\. Receive the Menu request.

2\. Resolve the Menu Identifier or Menu Location.

3\. Resolve the assigned Menu when applicable.

4\. Load the Menu Items.

5\. Validate Menu structure.

6\. Apply hierarchy.

7\. Apply ordering.

8\. Evaluate visibility rules.

9\. Evaluate destination availability.

10\. Return normalized Menu data.



The Menu Engine must not perform final visual rendering.



---



# 42. Menu Contract



Every managed Menu must follow an approved Menu contract.



The contract must define:



* Menu Identifier

* Menu purpose

* Applicable scope

* Menu Items

* Hierarchy rules

* Ordering rules

* Supported assignments

* Visibility rules

* Compatibility requirements



Consumers must not depend on undocumented Menu behavior.



---



# 43. Menu Item Contract



Every Menu Item must have an approved navigation contract.



The contract may define:



* Menu Item Identifier

* Label

* Destination

* Parent relationship

* Ordering information

* Visibility requirements

* Approved metadata



A Menu Item must not directly own or duplicate the resource represented by its destination.



---



# 44. Menu Location Contract



A Menu Location represents a navigation placement supported by a Theme or approved platform context.



The preferred model is:



Theme

→ Declares supported Menu Locations.



Menu Engine

→ Stores Menu assignments.



Rendering Engine

→ Requests resolved Menu data.



Theme

→ Presents the resolved navigation.



Menu Locations must remain separate from visual implementation details.



---



# 45. Menu Visibility Contract



Menu visibility must be evaluated independently from destination authorization.



The Menu Engine may determine whether a navigation entry should be presented.



The Permission Engine and destination owner remain responsible for actual protected access.



Therefore:



Visible Menu Item

→ Does not automatically grant access.



Hidden Menu Item

→ Does not replace authorization.



Direct destination access must still respect the applicable Permission contract.



---



# 46. Theme Menu Contract



Themes may define Menu Locations and presentation requirements.



A Theme must not:



* Own stored Menu data.

* Directly modify Menu persistence internals.

* Delete Menus during Theme activation.

* Delete Menus during Theme deactivation.

* Delete Menus during Theme update.



Theme switching must preserve compatible Menu data and fail safely when locations differ.



---



# 47. Plugin Menu Contract



Plugins may expose approved navigation destinations and Menu integrations.



A Plugin must not:



* Modify Menu Engine internals.

* Rewrite unrelated Menus.

* Access another Plugin's private Menu configuration without approval.

* Bypass Permission checks.

* Assume automatic placement in a Menu.

* Cause Menu resolution failure when the Plugin becomes unavailable.



Plugin-dependent Menu Items must degrade safely when the Plugin is disabled, removed, or invalid.



---



# 48. Menu Integrity Contract



Menu mutations must preserve structural integrity.



The Menu Engine must reject or safely handle:



* Circular hierarchy

* Self-parenting

* Invalid parent references

* Invalid Menu references

* Conflicting identifiers

* Unsupported cross-Menu relationships

* Invalid destination configuration



A failed mutation must not replace an existing valid Menu structure with a corrupted structure.



---



# 49. Menu Failure Contract



Menu operations must fail safely.



A Menu failure must not automatically:



* Delete destination resources.

* Modify Content.

* Modify Plugin business data.

* Corrupt Theme files.

* Corrupt unrelated Menus.

* Bypass Permission rules.

* Crash the Rendering Engine.

* Crash the active Theme.

* Crash the platform.



Where safe fallback is possible, invalid or unavailable Menu Items should be isolated from the remaining valid navigation structure.



---



# 50. Codex Implementation Rules



When implementing the Menu Engine, Codex must:



* Follow the frozen architecture from Documents 001–021.

* Follow the defined folder structure.

* Use approved public interfaces.

* Preserve Menu ownership boundaries.

* Preserve Content Engine ownership.

* Preserve Theme Engine boundaries.

* Preserve Rendering Engine boundaries.

* Preserve Plugin isolation.

* Preserve Permission Engine boundaries.

* Preserve Settings Engine boundaries.

* Preserve Cache Engine boundaries.

* Preserve Event Engine boundaries.

* Keep Menu structure separate from Theme presentation.

* Keep destination resources separate from Menu Items.

* Preserve Menu data across Theme changes where compatible.

* Validate hierarchy before accepting structural changes.

* Handle unavailable Plugin destinations safely.

* Never treat hidden Menu Items as a security mechanism.

* Never invent undocumented Menu Locations.

* Never hard-code Theme-specific presentation rules inside the Menu Engine.

* Never introduce a specific Menu persistence provider or storage technology as an architectural requirement unless another document explicitly defines one.



If an implementation detail is not defined by this document, Codex must not silently introduce a conflicting Menu architecture.



---



# 51. Final Acceptance Criteria



* [x] Menu Engine purpose defined.

* [x] Menu defined.

* [x] Menu Identifier defined.

* [x] Menu Item defined.

* [x] Menu Destination defined.

* [x] Menu Hierarchy defined.

* [x] Menu Ordering defined.

* [x] Menu Registration defined.

* [x] Menu Item Registration defined.

* [x] Menu Location defined.

* [x] Menu Location Registration defined.

* [x] Menu Assignment defined.

* [x] Menu Resolution defined.

* [x] Menu Visibility defined.

* [x] Permission-aware resolution defined.

* [x] Destination availability defined.

* [x] Theme Engine integration defined.

* [x] Theme switching safety defined.

* [x] Rendering Engine integration defined.

* [x] Content Engine integration defined.

* [x] Plugin Engine integration defined.

* [x] Plugin availability safety defined.

* [x] Settings Engine integration defined.

* [x] Cache Engine integration defined.

* [x] Event Engine integration defined.

* [x] Menu integrity defined.

* [x] Menu security defined.

* [x] Menu authorization defined.

* [x] Visibility and authorization separation defined.

* [x] Menu lifecycle defined.

* [x] Menu Item update defined.

* [x] Menu Item removal defined.

* [x] Menu removal defined.

* [x] Menu observability defined.

* [x] Menu failure handling defined.

* [x] Menu failure isolation defined.

* [x] Menu compatibility defined.

* [x] Theme Menu contract defined.

* [x] Plugin Menu contract defined.

* [x] Menu integrity contract defined.

* [x] Codex implementation rules defined.



---



# 52. Document Status



This document defines the Menu Engine specification for Favorite CMS.



The Menu Engine must be implemented according to this document and the frozen architecture established by Documents 001–021.



The Menu Engine provides controlled creation, management, hierarchy, ordering, assignment, visibility resolution, destination resolution, and normalized navigation data.



The Menu Engine must remain separate from Theme presentation and destination resource ownership.



Themes may define and render Menu Locations, while the Menu Engine remains responsible for navigation structure.



Plugins may contribute approved navigation integration without modifying Menu Engine internals.



No specific Menu database, persistence provider, navigation storage technology, or external Menu service is required by this document unless a future architecture document explicitly defines one.



Any future breaking change to the Menu Engine must follow the project's versioning and migration rules.



---



End of Document



Next Document:



023-seo-engine.md



