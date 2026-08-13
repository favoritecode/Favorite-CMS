# Favorite CMS



Document ID: 019



Title: Queue Engine



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



Next Document:

020-notification-engine.md



---



# 1. Purpose



This document defines the architecture, responsibilities, boundaries, and public interfaces of the Favorite CMS Queue Engine.



The Queue Engine is responsible for managing approved background or deferred work that should not block the primary request lifecycle.



The Queue Engine must remain independent from business-specific logic.



---



# 2. Queue Engine Objectives



The Queue Engine must provide a foundation for:



* Job Definition

* Job Submission

* Job Scheduling

* Job Execution

* Job Status

* Job Retry

* Job Failure Handling

* Queue Isolation

* Plugin Queue Integration

* Controlled Background Processing



The exact queue provider, worker technology, transport, and storage implementation remain behind the Queue Engine's public interfaces.



---



# 3. Job



A Job represents an approved unit of work submitted to the Queue Engine.



A Job may represent:



* Background processing

* Deferred processing

* Resource-related processing

* Plugin-defined background work

* Other approved asynchronous or delayed operations



A Job must have a clearly defined responsibility.



---



# 4. Job Identifier



Every submitted Job must have a stable Job Identifier.



The Job Identifier is used to:



* Track Job state

* Reference execution

* Report failures

* Support approved retry behavior

* Support diagnostics



The internal identifier format is implementation-specific.



---



# 5. Job Payload



A Job may contain an approved Payload required for execution.



The Payload may include:



* Resource identifier

* User identifier when required

* Job-specific parameters

* Approved execution metadata



The Job Payload must contain only the information required by the Job contract.



Sensitive or unrelated data must not be included unnecessarily.



---



# 6. Job Producer



A Job Producer is an Engine or approved Plugin that submits work to the Queue Engine.



The Producer is responsible for:



* Selecting the correct Job type

* Creating a valid Job Payload

* Submitting the Job through the public Queue Engine interface



Submitting a Job does not transfer ownership of the source resource to the Queue Engine.



---



# 7. Job Worker



A Job Worker executes approved Jobs.



The Worker must:



* Receive a valid Job

* Validate required Job information

* Execute the approved Job handler

* Report completion or failure

* Respect resource ownership boundaries



The Worker must not access unrelated private Engine internals.



---



# 8. Job Status



A Job may have a processing state such as:



* Pending

* Running

* Completed

* Failed



Additional states may be introduced if explicitly required by the Queue contract.



The Queue Engine must provide a normalized way to identify the current Job state.



---



# 9. Queue Boundary



The Queue Engine manages deferred execution.



It does not own the business operation represented by the Job.



Therefore:



Content Engine

→ Owns Content operations



Media Engine

→ Owns Media operations



Plugin

→ Owns Plugin business logic



Queue Engine

→ Schedules and executes approved Jobs



The Queue Engine must not become the source of truth for the underlying resource.



---



## Acceptance Criteria



* [x] Queue Engine purpose defined.

* [x] Queue Engine objectives defined.

* [x] Job defined.

* [x] Job Identifier defined.

* [x] Job Payload defined.

* [x] Job Producer defined.

* [x] Job Worker defined.

* [x] Job Status defined.

* [x] Queue boundary defined.



---









---



# 10. Job Submission



A Job Producer submits work through the approved Queue Engine interface.



The submission process must:



1\. Identify the Job type.

2\. Validate the Job Payload.

3\. Create the Job record or equivalent execution reference.

4\. Assign the Job Identifier.

5\. Place the Job into the approved execution flow.

6\. Return a normalized submission result.



Submitting a Job must not execute unrelated business logic inside the Producer.



---



# 11. Job Validation



Before a Job is accepted, the Queue Engine must validate:



* Job type

* Required Payload fields

* Payload structure

* Producer authorization when applicable

* Required execution metadata



An invalid Job must not be treated as a valid queued task.



---



# 12. Job Scheduling



The Queue Engine may support immediate or delayed execution according to the approved Queue contract.



Scheduling may define:



* Immediate execution

* Deferred execution

* Explicitly scheduled execution



The exact scheduling mechanism is implementation-specific.



A Consumer of the Queue Engine must not depend on an undocumented scheduling technology.



---



# 13. Job Execution



A Worker executes an approved Job according to its Job handler.



The general execution flow is:



Receive Job

→ Validate Job

→ Resolve Handler

→ Execute Work

→ Record Result

→ Mark Completed or Failed



The Worker must use public Engine interfaces when interacting with other platform systems.



---



# 14. Job Handler



A Job Handler contains the approved logic required to execute a specific Job type.



A Handler must:



* Accept the approved Job structure.

* Validate required Job data.

* Perform only the defined operation.

* Respect Permission and resource ownership boundaries.

* Return a normalized execution result.



A Handler must not directly modify unrelated Engine internals.



---



# 15. Job Result



A completed Job may produce an execution result.



The result may contain:



* Completion status

* Approved output metadata

* Resource reference

* Diagnostic information



The Queue Engine must not expose sensitive execution data unnecessarily.



The exact result structure may vary by Job type.



---



# 16. Job Failure



A Job may fail during validation or execution.



A failure may be caused by:



* Invalid Payload

* Missing resource

* Handler failure

* Dependency failure

* Permission failure

* Worker failure

* Other approved execution error



A failed Job must have a normalized failure state.



---



# 17. Job Retry



The Queue Engine may support controlled retry behavior for failed Jobs.



Retry behavior must be explicitly governed by the Queue contract.



A Job must not be retried indefinitely unless an approved policy explicitly requires it.



Retries must not create duplicate irreversible operations.



---



# 18. Retry Safety



A retryable Job should be designed so repeated execution remains safe where possible.



If repeated execution could create duplicate side effects, the responsible Handler must use an approved protection mechanism.



The Queue Engine must not assume every Job is automatically safe to retry.



---



## Acceptance Criteria



* [x] Job submission defined.

* [x] Job validation defined.

* [x] Job scheduling defined.

* [x] Job execution defined.

* [x] Job Handler defined.

* [x] Job Result defined.

* [x] Job failure defined.

* [x] Job retry defined.

* [x] Retry safety defined.



---









---



# 19. Queue and Content



The Content Engine may submit approved Jobs when Content-related work should be deferred or processed outside the primary request lifecycle.



Examples may include:



* Deferred Content processing

* Content-related derived work

* Other explicitly approved Content Jobs



The Queue Engine must not become the owner of Content.



The Content Engine remains responsible for Content state and lifecycle.



---



# 20. Queue and Media



The Media Engine may submit approved Jobs for Media-related background processing.



Examples may include:



* Deferred Media processing

* Media metadata processing

* Other explicitly approved Media Jobs



The Queue Engine must not directly own Media storage or Media lifecycle.



The Media Engine remains responsible for Media Resources.



---



# 21. Queue and Search



The Search Engine may use the Queue Engine for approved deferred Search-related processing.



For example:



Resource changes

→ Search-related Job submitted

→ Queue Engine schedules execution

→ Search Engine performs its approved update



The Queue Engine does not own Search Index data.



---



# 22. Queue and Cache



The Cache Engine may use queued work when an approved cache operation should run outside the primary request lifecycle.



The Queue Engine may schedule the work.



The Cache Engine remains responsible for:



* Cache invalidation

* Cache refresh

* Cache clearing

* Cache ownership



The Queue Engine must not modify Cache Engine internals directly.



---



# 23. Queue and Event Engine



The Event Engine and Queue Engine serve different responsibilities.



Event Engine

→ Communicates that an approved occurrence happened.



Queue Engine

→ Executes approved deferred work.



An Event Consumer may submit a Job when the reaction to an Event should be deferred.



Example:



Source Engine

→ Publishes Event



Event Engine

→ Delivers Event



Consumer

→ Submits Job



Queue Engine

→ Executes deferred work



The Event Engine must not automatically become a Queue implementation.



The Queue Engine must not replace Event communication.



---



# 24. Queue and Permission Engine



Queued Jobs must respect applicable Permission boundaries.



Submitting a protected Job does not automatically authorize the Job's resource operation.



Where authorization is required at execution time, the Job Handler must evaluate the applicable Permission contract.



A Queue Job must not be used to bypass authorization checks that would apply to the same protected operation outside the Queue.



---



# 25. Queue and User Context



A Job may reference a User when User context is required for the operation.



User context must be explicit.



A Job must not assume that the User who submitted the Job remains authorized indefinitely.



Execution-time authorization must be re-evaluated when required by the applicable operation.



Sensitive User information must not be copied into the Job Payload unnecessarily.



---



# 26. Queue and Plugin Boundary



Plugins may submit and process approved Jobs through public Queue Engine interfaces.



A Plugin may:



* Register approved Job types.

* Submit its own Jobs.

* Provide handlers for its own approved Jobs.



A Plugin must not:



* Modify Queue Engine internals.

* Read another Plugin's private Job Payload.

* Execute another Plugin's private handlers directly.

* Bypass Permission boundaries through queued execution.

* Depend on undocumented Queue implementation details.



---



# 27. Queue Isolation



Jobs must remain isolated according to their defined responsibility and ownership context.



A failed Job must not automatically corrupt unrelated Jobs or resources.



For example:



Failed Media Job

→ Must not corrupt Content.



Failed Search Job

→ Must not corrupt User data.



Failed Plugin Job

→ Must not corrupt another Plugin.



Queue isolation must preserve platform boundaries.



---



# 28. Queue Failure Isolation



Queue infrastructure failure must be separated from source-resource state.



Possible Queue failures include:



* Job submission failure

* Worker unavailable

* Handler resolution failure

* Job execution failure

* Retry failure

* Scheduling failure



A Queue failure must not automatically imply that the source resource is corrupted.



The responsible Engine remains the source of truth for its resource.



---



## Acceptance Criteria



* [x] Content Queue boundary defined.

* [x] Media Queue boundary defined.

* [x] Search Queue boundary defined.

* [x] Cache Queue boundary defined.

* [x] Event and Queue boundary defined.

* [x] Permission Queue boundary defined.

* [x] User context boundary defined.

* [x] Plugin Queue boundary defined.

* [x] Queue isolation defined.

* [x] Queue failure isolation defined.



---









---



# 29. Queue Security Boundary



The Queue Engine must treat queued Jobs as controlled platform operations.



Job data must not expose:



* Authentication credentials

* Private session information

* Unrelated User data

* Internal secrets

* Private implementation details



Only the information required by the Job contract should be included in the Job Payload.



---



# 30. Queue Authorization



Job submission and Job execution may require authorization.



The Queue Engine must not treat successful Job submission as automatic authorization for the underlying operation.



Where required:



Job Submission

→ Validate submission permission.



Job Execution

→ Re-evaluate applicable execution permission.



Authorization decisions remain the responsibility of the Permission Engine.



---



# 31. Queue Ownership



The Queue Engine owns Job scheduling and execution state.



It does not own the source resource referenced by the Job.



For example:



Content Job

→ Content Engine owns Content.



Media Job

→ Media Engine owns Media.



Search Job

→ Search Engine owns Search state.



Plugin Job

→ Plugin owns its business responsibility.



Queue Engine

→ Owns Job execution coordination.



---



# 32. Job Registration



Approved Job types must be registered through public Queue Engine interfaces.



A Job registration may define:



* Job type

* Approved handler

* Payload contract

* Execution requirements

* Retry behavior when applicable



Private Queue Engine internals must not be modified by Job Producers or Plugins.



---



# 33. Queue Lifecycle



The general Queue lifecycle is:



Create Job

→ Validate Job

→ Submit Job

→ Queue or Schedule

→ Worker Receives Job

→ Execute Handler

→ Complete or Fail

→ Retry if approved



The exact internal implementation may vary.



The public Queue contract must remain stable.



---



# 34. Job Cancellation Boundary



The Queue Engine may support Job cancellation when explicitly required.



Cancellation behavior must be defined by the applicable Queue contract.



A cancellation request must not be assumed to stop a Job that has already completed or reached an execution state where cancellation is no longer supported.



Cancellation must not corrupt the source resource.



---



# 35. Queue Observability



The Queue Engine may provide controlled operational information such as:



* Job Submitted

* Job Started

* Job Completed

* Job Failed

* Job Retried

* Job Cancelled

* Worker Failure

* Scheduling Failure



Operational information must not expose protected Job Payload contents unnecessarily.



---



# 36. Queue Recovery



The Queue Engine should recover safely from supported infrastructure or Worker failures.



Recovery behavior may include:



* Returning a failed Job to an approved retry flow

* Marking the Job as Failed

* Preserving execution diagnostics

* Allowing controlled manual recovery



The exact recovery mechanism remains implementation-specific.



---



# 37. Queue Compatibility



Changes to the internal Queue implementation must preserve the public Queue contract when the change is non-breaking.



Existing Job Producers, Workers, and Plugins must remain compatible with supported Queue Engine versions.



Breaking changes must follow the project's versioning and migration rules.



---



# 38. Queue Engine Non-Goals



The Queue Engine does not own:



* Content Resources

* Media Resources

* User Resources

* Search Indexes

* Cache Entries

* Event definitions

* Permission rules

* Theme resources

* Plugin business logic

* Source-resource storage



The Queue Engine is responsible for approved deferred execution and Job coordination.



---



## Acceptance Criteria



* [x] Queue security boundary defined.

* [x] Queue authorization defined.

* [x] Queue ownership defined.

* [x] Job registration defined.

* [x] Queue lifecycle defined.

* [x] Job cancellation boundary defined.

* [x] Queue observability defined.

* [x] Queue recovery defined.

* [x] Queue compatibility defined.

* [x] Queue Engine non-goals defined.



---









---



# 39. Final Queue Resolution Rules



The Queue Engine must process Jobs through approved public interfaces.



The general Job flow is:



1\. Create the Job.

2\. Validate the Job type.

3\. Validate the Job Payload.

4\. Submit the Job.

5\. Determine immediate or scheduled execution.

6\. Assign the Job to an approved Worker.

7\. Resolve the Job Handler.

8\. Execute the Job.

9\. Record completion or controlled failure.

10\. Retry only when explicitly allowed by the Job contract.



The Queue Engine must not become the source of truth for the resource referenced by a Job.



---



# 40. Job Contract



Every Job must follow an approved Job contract.



The contract must define:



* Job type

* Job purpose

* Approved Producer

* Approved Payload structure

* Approved Handler

* Execution requirements

* Authorization requirements when applicable

* Retry behavior when applicable

* Compatibility requirements



A Worker must not depend on Job data that is not part of the approved contract.



---



# 41. Producer Contract



A Job Producer must:



* Submit only approved Job types.

* Build valid Job Payloads.

* Avoid exposing unrelated sensitive data.

* Preserve ownership of the source resource.

* Use the public Queue Engine interface.



Submitting a Job must not transfer business responsibility to the Queue Engine.



---



# 42. Worker Contract



A Worker must:



* Accept only approved Jobs.

* Validate the Job before execution.

* Resolve the approved Handler.

* Respect Permission boundaries.

* Respect resource ownership boundaries.

* Report completion or failure.

* Avoid unsupported direct access to private Engine internals.



Worker execution must remain isolated from unrelated Jobs and resources.



---



# 43. Retry Contract



Retry behavior must be explicit.



A retryable Job must define the conditions under which another execution attempt is allowed.



The Queue Engine must not assume that every failed Job can be safely retried.



Retry processing must avoid uncontrolled duplicate side effects.



If retry safety cannot be guaranteed, the Job must follow the failure policy defined by its contract.



---



# 44. Queue Isolation Contract



Jobs provide deferred execution without removing system boundaries.



The preferred model is:



Producer

→ Queue Engine

→ Worker

→ Public Engine Interface



not:



Producer

→ Worker

→ Private Engine Internals



This separation is required for modularity, reliability, and maintainability.



---



# 45. Plugin Queue Contract



Plugins may register and submit approved Jobs through the public Queue Engine interface.



Plugin Jobs must remain isolated from Core internals and unrelated Plugins.



A Plugin must not:



* Modify Queue Engine internals.

* Access another Plugin's private Job data.

* Execute another Plugin's private Handler directly.

* Bypass Permission checks through queued execution.

* Introduce hidden dependencies on a specific Queue provider.

* Assume unsupported scheduling or retry guarantees.



---



# 46. Queue Failure Contract



Queue processing must fail safely.



A Queue failure must not automatically:



* Corrupt the source resource.

* Corrupt unrelated Jobs.

* Corrupt unrelated Workers.

* Corrupt other Plugins.

* Expose protected Job Payload data.

* Convert a failed Job into a successful business operation.



The Queue Engine must report controlled Queue failures.



---



# 47. Codex Implementation Rules



When implementing the Queue Engine, Codex must:



* Follow the frozen architecture from Documents 001–018.

* Follow the defined folder structure.

* Use approved public interfaces.

* Preserve resource ownership boundaries.

* Preserve Permission Engine boundaries.

* Preserve Event Engine boundaries.

* Preserve Cache Engine boundaries.

* Preserve Search Engine boundaries.

* Preserve Content Engine ownership.

* Preserve Media Engine ownership.

* Preserve User Engine ownership.

* Preserve Plugin isolation.

* Keep Producers independent from Workers.

* Keep Job Payloads minimal and contract-driven.

* Avoid inventing undocumented Job types.

* Avoid introducing a specific queue broker, worker framework, message transport, distributed task system, or external queue service as an architectural requirement.

* Avoid assuming unsupported delivery, ordering, scheduling, retry, or cancellation guarantees.



If an implementation detail is not defined by this document, Codex must not silently introduce a conflicting Queue architecture.



---



# 48. Final Acceptance Criteria



* [x] Queue Engine purpose defined.

* [x] Job defined.

* [x] Job Identifier defined.

* [x] Job Payload defined.

* [x] Job Producer defined.

* [x] Job Worker defined.

* [x] Job Handler defined.

* [x] Job Status defined.

* [x] Job Submission defined.

* [x] Job Validation defined.

* [x] Job Scheduling defined.

* [x] Job Execution defined.

* [x] Job Result defined.

* [x] Job Failure defined.

* [x] Job Retry defined.

* [x] Retry safety defined.

* [x] Content Queue boundary defined.

* [x] Media Queue boundary defined.

* [x] Search Queue boundary defined.

* [x] Cache Queue boundary defined.

* [x] Event and Queue boundary defined.

* [x] Permission Queue boundary defined.

* [x] User context boundary defined.

* [x] Plugin Queue boundary defined.

* [x] Queue isolation defined.

* [x] Queue security defined.

* [x] Queue authorization defined.

* [x] Queue ownership defined.

* [x] Job registration defined.

* [x] Queue lifecycle defined.

* [x] Job cancellation boundary defined.

* [x] Queue observability defined.

* [x] Queue recovery defined.

* [x] Queue failure isolation defined.

* [x] Queue compatibility defined.

* [x] Codex implementation rules defined.



---



# 49. Document Status



This document defines the Queue Engine specification for Favorite CMS.



The Queue Engine must be implemented according to this document and the frozen architecture established by Documents 001–018.



The Queue Engine provides controlled deferred and background execution for approved platform Jobs.



It must not become the owner or source of truth for Content, Media, User, Search, Cache, Plugin, Theme, or other platform resources.



No specific queue broker, worker framework, scheduling service, distributed task system, message transport, queue database, or external queue provider is required by this document unless a future architecture document explicitly defines one.



Any future breaking change to the Queue Engine must follow the project's versioning and migration rules.



---



End of Document



Next Document:



020-notification-engine.md



