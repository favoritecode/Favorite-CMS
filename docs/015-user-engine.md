# Favorite CMS



Document ID: 015



Title: User Engine



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



Next Document:

016-permission-engine.md



---



# 1. Purpose



This document defines the architecture, responsibilities, boundaries, and public interfaces of the Favorite CMS User Engine.



The User Engine is responsible for managing User Resources and providing a stable user-related contract to other platform systems.



The User Engine must remain independent from Theme-specific presentation logic.



---



# 2. User Engine Objectives



The User Engine must provide a foundation for:



- User Resource Management

- User Profile Information

- User Identity Reference

- User Role Information

- User Account State

- User Settings Integration

- User-related Resource References

- User Access Context



The exact authentication and session implementation is not defined by this document unless explicitly established by another architecture document.



---



# 3. User Resource



A User Resource represents a user known to the CMS.



A User Resource may contain:



- Unique user identifier

- Display name

- Profile information

- Role information

- Account state

- Approved user metadata



The exact fields depend on the platform's User contract.



---



# 4. User Identity



Each User Resource must have a stable unique identifier.



Other Engines should use the User identifier when referencing a user.



Consumers must not depend on internal User Engine storage details.



A User identifier must remain stable according to the platform's compatibility rules.



---



# 5. User Profile



The User Engine may provide profile information for a User Resource.



Profile information may include:



- Display name

- Profile image reference

- Other approved profile metadata



The current system demonstrates editable user profile information including a profile name and profile image. :contentReference\[oaicite:1]{index=1}



Profile presentation remains the responsibility of the Rendering and Theme systems.



---



# 6. User Role



A User Resource may have an associated role.



The current source demonstrates a user role represented as `Member`. :contentReference\[oaicite:2]{index=2}



Role information identifies the user's platform role.



Detailed permission enforcement is outside this document and must be handled through the approved Permission system.



---



# 7. User Settings



The User Engine may provide or integrate with user-specific settings.



Settings may include:



- User preferences

- Account-related configuration

- Other approved user-specific options



The source demonstrates a user-facing Settings area associated with the account interface. :contentReference\[oaicite:3]{index=3}



Settings must remain associated with the correct User Resource.



---



# 8. User-Owned Resources



Other Engines may maintain resources associated with a User.



Examples visible in the current system include:



- Uploaded resources

- Favorites

- Watch history

- Comments



These resources remain owned by their responsible Engine.



The User Engine provides the User identity/reference required to associate those resources with a User.



The User Engine must not take ownership of another Engine's resources merely because they belong to a user.



---



# 9. User and Rendering Boundary



The User Engine provides user information.



The Rendering Engine and Theme system determine how user information is displayed.



Therefore:



User Engine

→ User data and user identity



Permission Engine

→ Permission enforcement



Rendering Engine

→ Presentation resolution



Theme Engine

→ Presentation resources



The User Engine must not select Theme templates, layouts, components, or widgets.



---



## Acceptance Criteria



- [x] User Engine purpose defined.

- [x] User Engine objectives defined.

- [x] User Resource defined.

- [x] User identity defined.

- [x] User profile defined.

- [x] User role boundary defined.

- [x] User settings boundary defined.

- [x] User-owned resource boundary defined.

- [x] User and Rendering boundaries defined.



---









---



# 10. User Account State



The User Engine must maintain the current account state required by the platform.



A User Resource may have an account state such as:



- Active

- Inactive

- Restricted



The exact state model must follow the platform's approved User contract.



An invalid account state must not be accepted.



---



# 11. Authentication Boundary



Authentication identifies a User to the platform.



The User Engine may integrate with the platform authentication system.



The exact authentication mechanism is not defined by this document.



Authentication implementation must remain behind an approved platform interface.



The User Engine must not expose authentication credentials through normal User Resource responses.



---



# 12. Session Boundary



A logged-in User may have an authenticated session.



Session creation, validation, renewal, and termination must follow the platform authentication contract.



The User Engine may consume the authenticated User identity.



The User Engine must not expose private session implementation details to Themes or Plugins.



The exact session storage mechanism is not defined by this document.



---



# 13. Login Integration



The platform provides a Login entry point for User accounts. :contentReference\[oaicite:1]{index=1}



The User Engine may provide the User identity required after successful authentication.



A failed authentication operation must not create an authenticated User state.



The User Engine must not treat an unauthenticated visitor as an authenticated User.



---



# 14. Logout Integration



The platform provides a Logout operation for the authenticated account interface. :contentReference\[oaicite:2]{index=2}



Logout must terminate the applicable authenticated User context according to the platform authentication contract.



After logout, protected User Resources must not be treated as accessible through the previous authenticated context.



---



# 15. User Profile Update



An authenticated User may update approved profile information.



Profile updates must:



1\. Resolve the authenticated User.

2\. Verify that the User may modify the profile.

3\. Validate the requested changes.

4\. Apply the valid changes.

5\. Return the updated User profile information.



A failed profile update must not leave the profile in a partially invalid state.



---



# 16. Profile Image Reference



A User Profile may contain a profile image reference.



The User Engine must treat the image as a Media Resource relationship when the Media Engine contract supports it.



The User Engine does not own Media storage or image processing.



The Media Engine remains responsible for the Media Resource.



---



# 17. User Favorites Boundary



The platform exposes a Favorites area associated with the User account. :contentReference\[oaicite:3]{index=3}



Favorites are User-associated resources.



The User Engine provides the User identity required to associate Favorites with the correct User.



The actual Favorite resource lifecycle belongs to the responsible Engine or feature module.



The User Engine must not take ownership of Favorite data unless explicitly defined by the platform contract.



---



# 18. User Uploaded Resources Boundary



The platform exposes an Uploaded area within the User account. :contentReference\[oaicite:4]{index=4}



Uploaded resources may be associated with a User through the User identifier.



The responsible resource Engine remains the owner of the uploaded resource.



For example:



User Engine

→ User identity



Media Engine

→ Media Resource



User Uploaded area

→ Presents resources associated with the User



---



## Acceptance Criteria



- [x] User account state defined.

- [x] Authentication boundary defined.

- [x] Session boundary defined.

- [x] Login integration defined.

- [x] Logout integration defined.

- [x] User profile update defined.

- [x] Profile image relationship defined.

- [x] Favorites boundary defined.

- [x] Uploaded resource boundary defined.



---









---



# 19. User Permission Boundary



The User Engine may expose the User's role or identity context to the platform.



Detailed permission evaluation belongs to the Permission Engine.



The User Engine must not replace the Permission Engine with its own independent permission model.



The boundary is:



User Engine

→ User identity and role information



Permission Engine

→ Permission evaluation and enforcement



---



# 20. User Resource Association



Other platform resources may be associated with a User through the stable User identifier.



Examples may include:



- Content created by a User

- Media uploaded by a User

- Favorites

- Comments

- Other approved User-related resources



The owning Engine remains responsible for the associated resource.



The User Engine provides the identity reference required for that association.



---



# 21. User Data Isolation



User information must remain isolated from unrelated User Resources.



An operation for one User must not unintentionally modify another User.



User-specific settings, profile information, and account state must remain associated with the correct User identifier.



---



# 22. User Profile Visibility



The User Engine may expose approved public profile information.



Private or account-specific information must not be exposed through public User responses unless the applicable access rules permit it.



The Rendering Engine decides how approved profile information is presented.



---



# 23. User Settings Isolation



User settings must remain associated with the correct User Resource.



A settings update must:



1\. Resolve the authenticated User.

2\. Verify the User context.

3\. Validate the requested setting.

4\. Apply the valid change.

5\. Return the updated setting state.



A failed update must not modify unrelated User settings.



---



# 24. User Account Failure Handling



User Engine operations must fail in a controlled manner.



Possible failures include:



- User not found

- Invalid User data

- Invalid profile update

- Invalid settings update

- Unauthorized User operation

- Invalid account state

- User-resource association failure



A failed operation must not silently report success.



---



# 25. User Profile Failure Safety



A failed profile update must preserve the last valid profile state.



For example:



Invalid profile name

→ Existing valid profile remains unchanged.



Invalid profile image reference

→ Existing valid profile image remains unchanged.



Failed profile update

→ No partially invalid profile state.



---



# 26. User and Media Boundary



When a User Profile references a profile image, the relationship must use the Media Engine contract.



The User Engine must not:



- Store media directly.

- Process image files directly.

- Modify Media Engine internals.

- Bypass Media validation.



The Media Engine remains responsible for the Media Resource.



---



# 27. User and Content Boundary



When a Content Resource is associated with a User, the relationship must use the Content Engine contract.



The User Engine must not:



- Publish Content.

- Archive Content.

- Modify Content lifecycle.

- Delete Content on behalf of a User unless the approved Content contract explicitly allows the operation.



The Content Engine remains responsible for Content ownership and lifecycle.



---



# 28. User and Plugin Boundary



Plugins may consume User information through approved User Engine interfaces.



A Plugin may use:



- User identifier

- Approved profile information

- Approved role information

- User-related resource references



A Plugin must not:



- Access private User Engine storage.

- Modify User Engine internals.

- Bypass User access rules.

- Expose protected User information without authorization.



---



## Acceptance Criteria



- [x] User permission boundary defined.

- [x] User resource association defined.

- [x] User data isolation defined.

- [x] User profile visibility defined.

- [x] User settings isolation defined.

- [x] User account failure handling defined.

- [x] User profile failure safety defined.

- [x] User and Media boundary defined.

- [x] User and Content boundary defined.

- [x] User and Plugin boundary defined.



---









---



# 29. User Data Security Boundary



The User Engine must protect User Resource information according to the platform's access rules.



User responses must contain only approved information.



The User Engine must not expose:



- Authentication credentials

- Private session information

- Internal storage details

- Secrets

- Private implementation details



Public profile information and private account information must remain distinguishable.



---



# 30. User Resource Consistency



The User Engine must preserve a valid User Resource state.



A successful User operation must produce a valid result.



A failed operation must not leave the User Resource partially invalid.



An operation for one User must not unintentionally modify another User.



---



# 31. User Account State Changes



Changes to User account state must pass through the approved User Engine and authentication boundaries.



A state change must not silently bypass the applicable access rules.



The User Engine must not treat an invalid account state as a valid authenticated User state.



---



# 32. User Resource References



Other Engines may reference Users through the stable User identifier.



User references must remain stable according to the User compatibility contract.



A User reference must not require consumers to know the internal storage implementation.



If a User Resource becomes unavailable, dependent Engines must handle the missing User according to their own resource contracts.



---



# 33. User Extension Points



The User Engine may provide controlled extension points for approved Plugins.



Extensions may provide:



- Additional User metadata

- User-related features

- Approved profile information

- User resource relationships



Extensions must use approved public interfaces.



Extensions must not:



- Modify User Engine internals.

- Bypass User validation.

- Bypass access rules.

- Access private User storage.



---



# 34. User and Theme Boundary



Themes may consume approved User information for presentation.



A Theme may display:



- Display name

- Profile image

- Approved account information

- Approved role information



The Theme must not:



- Modify User Engine internals.

- Access private User storage.

- Manage authentication directly through private implementation details.

- Change User ownership or account state without an approved interface.



---



# 35. User Failure Isolation



A failure affecting one User must not corrupt unrelated User Resources.



For example:



Failed profile update

→ Must not modify another User.



Failed settings update

→ Must not modify another account.



Failed User-resource association

→ Must not corrupt the source resource.



Authentication failure

→ Must not create a valid authenticated User state.



---



# 36. User Compatibility



Changes to the internal User Engine implementation must preserve the public User contract when the change is non-breaking.



Existing User Resources must remain compatible with supported versions of the User Engine.



Breaking changes must follow the project's versioning and migration rules.



---



# 37. User Engine Non-Goals



The User Engine does not own:



- Detailed permission evaluation

- Theme rendering

- Template rendering

- Layout rendering

- Component rendering

- Media storage

- Media processing

- Content lifecycle

- Search indexing

- Plugin business logic



Those responsibilities remain with their respective Engines or platform systems.



---



# 38. User Engine Implementation Contract



An implementation of the User Engine must provide the behavior defined by this document.



The implementation must support:



- User Resource management

- Stable User identity

- User profile

- User role information

- User account state

- User settings integration

- User-resource association

- Authentication integration

- Session integration

- Controlled failure handling

- Plugin integration

- Theme integration



Internal implementation details may change as long as the public User contract remains compatible.



---



## Acceptance Criteria



- [x] User data security boundary defined.

- [x] User Resource consistency defined.

- [x] User account state boundary defined.

- [x] User resource references defined.

- [x] User extension points defined.

- [x] User and Theme boundary defined.

- [x] User failure isolation defined.

- [x] User compatibility defined.

- [x] User Engine non-goals defined.

- [x] User Engine implementation contract defined.



---









---



# 39. Final User Resolution Rules



The User Engine must resolve User Resources through approved public interfaces.



The resolution process must:



1\. Identify the User.

2\. Validate the User Resource.

3\. Resolve the applicable account state.

4\. Return approved User information.

5\. Apply the applicable access rules.



The User Engine must not expose private User information through normal public User responses.



---



# 40. User Profile Contract



The User Profile contract may expose approved profile information such as:



- Display name

- Profile image reference

- Approved profile metadata



The source interface supports profile image display and editable user name information. :contentReference\[oaicite:1]{index=1}



Profile presentation remains the responsibility of the Rendering and Theme systems.



---



# 41. User Account Interface Contract



The User account interface may expose account-related areas including:



- Favorites

- Uploaded

- Profile

- Settings

- Logout



These areas are visible in the current account navigation. :contentReference\[oaicite:2]{index=2}



The User Engine provides the User identity and account context required by these areas.



Each feature remains responsible for its own resource lifecycle.



---



# 42. User Resource Ownership Contract



The User Engine owns User Resources.



It does not automatically own resources associated with Users.



For example:



User Engine

→ User



Media Engine

→ Uploaded Media



Favorite feature

→ Favorites



Content Engine

→ Content



This ownership boundary must remain explicit.



---



# 43. User Authentication Contract



Authentication and session behavior must remain behind the approved authentication boundary.



The User Engine may consume the authenticated User identity.



The implementation must not expose authentication credentials or private session internals through the User contract.



No specific authentication provider or session-storage technology is required by this document.



---



# 44. User Extension Contract



Plugins may extend approved User functionality through public interfaces.



Extensions may provide:



- Additional profile metadata

- User-related features

- User-resource relationships



Extensions must not bypass:



- User validation

- User access rules

- Authentication boundaries

- Private User storage



---



# 45. Codex Implementation Rules



When implementing the User Engine, Codex must:



- Follow the frozen architecture from Documents 001–014.

- Follow the defined folder structure.

- Use approved public interfaces.

- Preserve stable User identifiers.

- Preserve User data isolation.

- Preserve authentication boundaries.

- Preserve Media ownership boundaries.

- Preserve Content ownership boundaries.

- Preserve Plugin boundaries.

- Preserve Theme and Rendering boundaries.

- Avoid inventing unsupported account behavior.

- Avoid introducing a specific authentication provider unless another architecture document explicitly requires one.



If an implementation detail is not defined by this document, Codex must not silently introduce a conflicting architecture.



---



# 46. Final Acceptance Criteria



- [x] User Resource management defined.

- [x] Stable User identity defined.

- [x] User profile defined.

- [x] Profile image relationship defined.

- [x] User role boundary defined.

- [x] User account state defined.

- [x] Authentication boundary defined.

- [x] Session boundary defined.

- [x] Login integration defined.

- [x] Logout integration defined.

- [x] User profile update defined.

- [x] User settings boundary defined.

- [x] Favorites boundary defined.

- [x] Uploaded resource boundary defined.

- [x] User-resource association defined.

- [x] User data isolation defined.

- [x] User security boundary defined.

- [x] Media integration defined.

- [x] Content integration defined.

- [x] Plugin integration defined.

- [x] Theme integration defined.

- [x] User extension contract defined.

- [x] Failure isolation defined.

- [x] Compatibility rules defined.

- [x] Codex implementation rules defined.



---



# 47. Document Status



This document defines the User Engine specification for Favorite CMS.



The User Engine must be implemented according to this document and the frozen architecture established by Documents 001–014.



This document defines generic User Engine responsibilities.



Business-specific user features must remain within the responsible Engine or Plugin.



No specific authentication provider, session-storage technology, or external identity service is required by this document unless a future architecture document explicitly defines one.



Any future breaking change to the User Engine must follow the project's versioning and migration rules.



---



End of Document



Next Document:



016-permission-engine.md

