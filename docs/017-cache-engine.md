# Favorite CMS



Document ID: 017



Title: Cache Engine



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

- 015-user-engine.md

- 016-permission-engine.md



Next Document:

018-event-engine.md



---



# 1. Purpose



This document defines the architecture, responsibilities, boundaries, and public interfaces of the Favorite CMS Cache Engine.



The Cache Engine is responsible for temporarily storing approved reusable data or generated results so that repeated access can be served efficiently.



The Cache Engine must remain independent from resource ownership and presentation logic.



---



# 2. Cache Engine Objectives



The Cache Engine must provide a foundation for:



- Cache Storage

- Cache Retrieval

- Cache Invalidation

- Cache Expiration

- Cache Isolation

- Cache Key Management

- Engine Cache Integration

- Controlled Cache Failure Handling

- Cache Clearing



The exact cache storage implementation remains behind the Cache Engine's public interfaces.



---



# 3. Cache Entry



A Cache Entry represents temporarily stored data associated with a Cache Key.



A Cache Entry may contain:



- Cache Key

- Cached Value

- Expiration information

- Cache metadata

- Resource or context reference



A Cache Entry must not become the source of truth for the original resource.



---



# 4. Cache Key



A Cache Key uniquely identifies a cached value within its applicable cache scope.



A Cache Key must be deterministic for equivalent cache requests.



Different resource contexts must not unintentionally share the same Cache Key.



Cache Key generation must remain behind an approved Cache Engine contract.



---



# 5. Cache Retrieval



The Cache Engine may retrieve a valid Cache Entry using its Cache Key.



A successful retrieval returns the cached value.



A missing, expired, or invalid Cache Entry must be treated as a cache miss.



A cache miss must not be treated as a resource failure.



The responsible Engine remains responsible for resolving the original resource.



---



# 6. Cache Storage



The Cache Engine may store approved values for later retrieval.



Only values approved by the Cache Engine contract may be cached.



The Cache Engine must not automatically cache every resource or operation.



The caching decision must remain explicit and controlled.



---



# 7. Cache Expiration



A Cache Entry may have an expiration policy.



When a Cache Entry expires, it must no longer be treated as a valid cached value.



The exact expiration mechanism is implementation-specific.



The Cache Engine must not require consumers to know the internal expiration implementation.



---



# 8. Cache Invalidation



The Cache Engine must support invalidation of cached data.



Invalidation may occur when:



- A source resource changes.

- A resource is deleted.

- Searchable information changes.

- User-specific information changes.

- Permission state changes.

- A Theme or Plugin changes relevant cached output.



Invalidation must remove or invalidate the affected cache representation without modifying the source resource.



---



# 9. Cache Clearing



The platform may provide a mechanism to clear cached data.



The source interface demonstrates a user-facing `Clear Cache` operation. :contentReference\[oaicite:1]{index=1}



Cache clearing must affect only the cache scope defined by the operation.



Clearing a cache must not delete or modify the original Content, Media, User, Plugin, or Theme resources.



---



## Acceptance Criteria



- [x] Cache Engine purpose defined.

- [x] Cache Engine objectives defined.

- [x] Cache Entry defined.

- [x] Cache Key defined.

- [x] Cache Retrieval defined.

- [x] Cache Storage defined.

- [x] Cache Expiration defined.

- [x] Cache Invalidation defined.

- [x] Cache Clearing defined.



---









---



# 10. Cache Hit



A Cache Hit occurs when a valid Cache Entry is found for the requested Cache Key.



On a Cache Hit:



- The cached value may be returned.

- The original resource does not need to be resolved again unless required by the applicable cache policy.

- Access-control requirements must still be respected where the cached value is access-sensitive.



A Cache Hit must not bypass required security checks.



---



# 11. Cache Miss



A Cache Miss occurs when a valid Cache Entry cannot be returned.



A Cache Miss may occur when:



- No Cache Entry exists.

- The Cache Entry has expired.

- The Cache Entry has been invalidated.

- The Cache Entry is unavailable.

- The Cache Entry is incompatible with the current request.



A Cache Miss must allow the responsible Engine to resolve the original resource.



---



# 12. Cache-as-Optimization Boundary



Caching is an optimization layer.



The platform must remain functionally correct when a Cache Entry is unavailable.



Therefore:



Cache Hit

→ May improve retrieval efficiency.



Cache Miss

→ Must fall back to the responsible resource resolution path.



The absence of cache data must not make the original resource permanently unavailable.



---



# 13. Resource Ownership Boundary



The Cache Engine does not own the resources represented by cached values.



For example:



Content Engine

→ Owns Content.



Media Engine

→ Owns Media.



User Engine

→ Owns User.



Search Engine

→ Owns Search behavior.



Cache Engine

→ Temporarily stores approved representations.



The Cache Engine must not modify the source resource when storing, retrieving, or invalidating cached data.



---



# 14. Cache and Content



The Content Engine may use the Cache Engine for approved Content-related data.



When Content changes, relevant cached representations may need to be invalidated.



The Cache Engine must not perform Content lifecycle operations.



---



# 15. Cache and Media



The Media Engine may use the Cache Engine for approved Media-related data or metadata.



Media changes may require invalidation of related cached representations.



The Cache Engine must not modify Media storage or Media lifecycle.



---



# 16. Cache and User



The User Engine may use caching for approved User-related data.



User-specific cached data must remain isolated from other User contexts.



When User information changes, affected cached representations must be invalidated according to the applicable cache policy.



Sensitive User information must not be exposed through an unrelated cache context.



---



# 17. Cache and Search



The Search Engine may use caching for approved Search Results or Search-related data.



Search cache entries must respect the current visibility and authorization state of the underlying resources.



When searchable resource state changes, affected Search cache entries may require invalidation.



The Cache Engine does not own Search Index data.



---



# 18. Cache and Rendering



The Rendering Engine may use the Cache Engine for approved rendered or presentation-related data.



Cached presentation data must not become a substitute for Theme or Rendering resource ownership.



When relevant Theme or Rendering resources change, affected cached representations may require invalidation.



---



## Acceptance Criteria



- [x] Cache Hit defined.

- [x] Cache Miss defined.

- [x] Cache-as-Optimization boundary defined.

- [x] Resource ownership boundary defined.

- [x] Cache and Content boundary defined.

- [x] Cache and Media boundary defined.

- [x] Cache and User boundary defined.

- [x] Cache and Search boundary defined.

- [x] Cache and Rendering boundary defined.



---









---



# 19. Cache Scope



A Cache Entry must belong to a defined cache scope.



Possible scopes may include:



- Resource cache

- Search cache

- User-specific cache

- Rendering cache

- Plugin cache

- Other explicitly registered cache scopes



A Cache Entry must not unintentionally cross its defined scope.



User-specific data must not be returned from a cache entry belonging to another User context.



---



# 20. Cache Context



A cache request may depend on a context.



A context may include:



- User identity

- Resource identifier

- Query parameters

- Locale

- Theme context

- Plugin context

- Other approved cache dimensions



Context-sensitive values must use a Cache Key that represents the required context.



---



# 21. Cache Invalidation by Resource Change



When a source resource changes, affected cached representations must be invalidated when required by the applicable cache policy.



Examples:



Content update

→ Invalidate affected Content cache.



Media update

→ Invalidate affected Media cache.



User profile update

→ Invalidate affected User cache.



Searchable metadata update

→ Invalidate affected Search cache.



Theme resource update

→ Invalidate affected Rendering cache.



---



# 22. Cache Invalidation Safety



Cache invalidation must be isolated from source-resource mutation.



Invalidating a Cache Entry must not:



- Delete the source resource.

- Modify the source resource.

- Change resource ownership.

- Change User permissions.

- Change Content state.



Invalidation affects cached representations only.



---



# 23. Cache Clear Operation



The Cache Engine may expose a controlled cache-clear operation.



The operation may clear:



- A specific Cache Key.

- A defined Cache Scope.

- An approved cache group.

- The complete cache according to platform policy.



A cache-clear operation must not exceed its approved scope.



The existing system provides a `Clear Cache` user action through `clearLocalCache()`. :contentReference\[oaicite:1]{index=1}



---



# 24. Cache Clear and User Context



If a cache-clear operation is available to users, the operation must operate only within the cache scope permitted by the platform.



A User must not be able to clear or modify another User's protected cache context unless explicitly authorized.



---



# 25. Cache and Permissions



Cached protected data must remain compatible with current authorization rules.



A cached value must not be returned merely because it exists.



When authorization-sensitive data is cached, the Cache Engine must preserve the required authorization context or require authorization to be re-evaluated before returning the value.



---



# 26. Cache Failure Isolation



A Cache failure must not corrupt the source resource.



Possible Cache failures include:



- Cache storage failure

- Cache retrieval failure

- Cache invalidation failure

- Cache expiration failure

- Cache key conflict

- Cache clear failure



A Cache failure must be handled without treating the source resource as automatically corrupted.



---



# 27. Cache Availability



The platform must remain functionally correct when the Cache Engine is unavailable, where the responsible resource Engine can resolve the original data.



Cache availability must improve performance, not become an uncontrolled dependency for the existence of the source resource.



---



# 28. Cache and Plugin Boundary



Plugins may use approved Cache Engine interfaces.



A Plugin may define cache entries for its own approved resources or generated data.



A Plugin must not:



- Modify Cache Engine internals.

- Access unrelated protected cache scopes.

- Clear platform-wide cache without authorization.

- Use another Plugin's private cache context.



---



## Acceptance Criteria



- [x] Cache scope defined.

- [x] Cache context defined.

- [x] Resource-change invalidation defined.

- [x] Invalidation safety defined.

- [x] Cache clear operation defined.

- [x] User cache-clear boundary defined.

- [x] Cache and Permission boundary defined.

- [x] Cache failure isolation defined.

- [x] Cache availability defined.

- [x] Plugin cache boundary defined.



---









---



# 29. Cache Management Boundary



The Cache Engine may provide controlled management operations for approved cache scopes.



Management operations may include:



- Clear Cache

- Invalidate Cache Entry

- Invalidate Cache Scope

- Refresh approved cached data



Management operations must remain within their approved authorization and scope.



---



# 30. Cache Refresh



A Cache Entry may be refreshed when the responsible Engine can generate an updated value.



A refresh operation must not modify the ownership or lifecycle of the source resource.



If refresh fails:



- The existing valid Cache Entry may remain available according to cache policy.

- Or the entry may be invalidated when required by the applicable policy.



The Cache Engine must not report stale data as newly refreshed data.



---



# 31. Cache Versioning



A Cache Entry may contain a version or validity marker when required to distinguish different representations of the same resource.



A new resource representation must not incorrectly reuse an incompatible Cache Entry.



Cache versioning remains an internal Cache Engine concern unless exposed through an approved public contract.



---



# 32. Cache Isolation



Cache data must remain isolated according to its defined scope.



A failure or invalidation in one cache scope must not unintentionally clear unrelated cache scopes.



For example:



User Cache

→ Must not unintentionally clear Content Cache.



Content Cache

→ Must not unintentionally clear Media Cache.



Plugin Cache

→ Must not unintentionally clear another Plugin's private cache.



---



# 33. Cache Security



The Cache Engine must treat cached protected data as protected data.



Caching a value must not make that value public.



Cache access must follow the applicable authorization and resource visibility rules.



Private or User-specific cache data must not be exposed through a public cache context.



---



# 34. Cache Observability



The Cache Engine may provide controlled operational information such as:



- Cache Hit

- Cache Miss

- Cache Invalidation

- Cache Expiration

- Cache Clear

- Cache Failure



Operational information must not expose protected cached values or private resource data.



---



# 35. Cache Failure Handling



Cache failures must be controlled.



Possible failures include:



- Storage unavailable

- Retrieval failure

- Invalid Cache Key

- Expired Cache Entry

- Invalidation failure

- Clear operation failure

- Refresh failure



A Cache failure must not automatically become a source-resource failure.



The responsible Engine must remain capable of handling the original resource according to its own contract where possible.



---



# 36. Cache Compatibility



Changes to the internal Cache Engine implementation must preserve the public Cache contract when the change is non-breaking.



Existing consumers must remain compatible with supported Cache Engine versions.



Breaking changes must follow the project's versioning and migration rules.



---



# 37. Cache Engine Non-Goals



The Cache Engine does not own:



- Content lifecycle

- Media lifecycle

- User lifecycle

- Search Index ownership

- Permission evaluation

- Theme resources

- Plugin business logic

- Source-resource storage



The Cache Engine is an optimization and temporary-data layer.



---



## Acceptance Criteria



- [x] Cache management boundary defined.

- [x] Cache refresh defined.

- [x] Cache versioning defined.

- [x] Cache isolation defined.

- [x] Cache security defined.

- [x] Cache observability defined.

- [x] Cache failure handling defined.

- [x] Cache compatibility defined.

- [x] Cache Engine non-goals defined.



---









---



# 38. Final Cache Resolution Rules



The Cache Engine must resolve cache operations through approved public interfaces.



The resolution process must:



1\. Generate or receive the approved Cache Key.

2\. Determine the applicable Cache Scope.

3\. Check for a valid Cache Entry.

4\. Return the cached value on a valid Cache Hit.

5\. Return a Cache Miss when no valid entry exists.

6\. Allow the responsible Engine to resolve the original resource when required.



The Cache Engine must not become the source of truth for cached resources.



---



# 39. Cache Clear Contract



The Cache Engine must provide a controlled cache-clear mechanism where cache clearing is supported.



A clear operation must:



- Clear only the approved cache scope.

- Remove or invalidate applicable Cache Entries.

- Leave source resources unchanged.

- Complete without corrupting unrelated cache scopes.



The existing implementation exposes `Clear Cache` and its `clearLocalCache()` function clears local storage and reloads the page. :contentReference\[oaicite:1]{index=1}



The exact storage and reload behavior remains implementation-specific unless explicitly required by another architecture document.



---



# 40. Cache Invalidation Contract



Cache invalidation must be available through an approved interface.



Invalidation may target:



- A Cache Key

- A Cache Scope

- A Resource-related cache group

- Another explicitly defined cache boundary



Invalidation must affect cached representations only.



---



# 41. Cache Security Contract



The Cache Engine must preserve the security context of protected cached data.



A cached value must not bypass:



- Permission checks

- User isolation

- Resource visibility rules

- Approved access-control requirements



Caching must never convert protected data into public data.



---



# 42. Cache Failure Contract



A Cache failure must degrade safely.



When possible:



Cache failure

→ Resolve through the responsible Engine.



Cache miss

→ Resolve original resource.



Invalid cache entry

→ Ignore or invalidate entry.



Failed cache clear

→ Do not modify source resources.



The Cache Engine must not report a successful cache operation when the operation actually failed.



---



# 43. Codex Implementation Rules



When implementing the Cache Engine, Codex must:



- Follow the frozen architecture from Documents 001–016.

- Follow the defined folder structure.

- Use approved public interfaces.

- Preserve resource ownership boundaries.

- Preserve User-specific cache isolation.

- Preserve Permission boundaries.

- Preserve Search boundaries.

- Preserve Rendering boundaries.

- Preserve Plugin boundaries.

- Keep cache behavior optional from the source-resource perspective.

- Never treat cached data as the source of truth.

- Never delete source resources during cache invalidation or cache clearing.

- Never introduce an undocumented cache provider or storage technology as an architectural requirement.



If an implementation detail is not defined by this document, Codex must not silently introduce a conflicting architecture.



---



# 44. Final Acceptance Criteria



- [x] Cache Entry defined.

- [x] Cache Key defined.

- [x] Cache Scope defined.

- [x] Cache Context defined.

- [x] Cache Storage defined.

- [x] Cache Retrieval defined.

- [x] Cache Hit defined.

- [x] Cache Miss defined.

- [x] Cache Expiration defined.

- [x] Cache Invalidation defined.

- [x] Cache Clear defined.

- [x] Cache Refresh defined.

- [x] Cache Versioning defined.

- [x] Cache Security defined.

- [x] Cache Isolation defined.

- [x] Content cache boundary defined.

- [x] Media cache boundary defined.

- [x] User cache boundary defined.

- [x] Search cache boundary defined.

- [x] Rendering cache boundary defined.

- [x] Plugin cache boundary defined.

- [x] Permission boundary defined.

- [x] Cache failure handling defined.

- [x] Cache failure isolation defined.

- [x] Cache compatibility defined.

- [x] Codex implementation rules defined.



---



# 45. Document Status



This document defines the Cache Engine specification for Favorite CMS.



The Cache Engine must be implemented according to this document and the frozen architecture established by Documents 001–016.



The Cache Engine is an optimization and temporary-data layer.



The Cache Engine must not become the owner or source of truth for Content, Media, User, Search, Plugin, Theme, or other platform resources.



The existing source demonstrates a user-facing `Clear Cache` operation and local cache clearing behavior. 



No specific cache provider, cache database, distributed-cache technology, or storage implementation is required by this document unless a future architecture document explicitly defines one.



Any future breaking change to the Cache Engine must follow the project's versioning and migration rules.



---



End of Document



Next Document:



018-event-engine.md

