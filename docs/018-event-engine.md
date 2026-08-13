# Favorite CMS



Document ID: 018



Title: Event Engine



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

- 017-cache-engine.md



Next Document:

019-queue-engine.md



---



# 1. Purpose



This document defines the architecture, responsibilities, boundaries, and public interfaces of the Favorite CMS Event Engine.



The Event Engine provides a controlled mechanism for publishing and consuming platform events.



Events allow independent platform systems to react to approved state changes or platform actions without creating unnecessary direct dependencies between unrelated Engines.



---



# 2. Event Engine Objectives



The Event Engine must provide a foundation for:



- Event Definition

- Event Publishing

- Event Consumption

- Event Subscription

- Listener Management

- Event Payload Validation

- Event Isolation

- Plugin Event Integration

- Controlled Event Failure Handling



The exact event transport and storage implementation remains behind the Event Engine's public interfaces.



---



# 3. Event



An Event represents a meaningful occurrence within the platform.



An Event may describe:



- A resource creation

- A resource update

- A resource deletion

- A User-related state change

- A Media-related state change

- A Content-related state change

- A Plugin-defined occurrence

- Another explicitly approved platform occurrence



Only approved Event types may be published through the public Event contract.



---



# 4. Event Name



Each Event must have a stable Event Name.



The Event Name identifies the type of occurrence.



Event Names must be deterministic and must follow the platform's naming conventions.



Consumers must not depend on private implementation details to identify an Event.



---



# 5. Event Payload



An Event may contain a Payload describing the occurrence.



The Payload may contain:



- Event metadata

- Resource identifier

- User identifier

- Relevant state information

- Event-specific data



The Payload must contain only information approved for that Event.



Private implementation details and unrelated sensitive information must not be exposed through an Event Payload.



---



# 6. Event Publisher



An Event Publisher is the Engine or approved system that publishes an Event.



The Publisher is responsible for:



- Selecting the correct Event type.

- Building the approved Event Payload.

- Publishing through the Event Engine interface.



The Publisher remains responsible for the source resource.



Publishing an Event does not transfer resource ownership to the Event Engine.



---



# 7. Event Consumer



An Event Consumer receives an Event through an approved subscription.



A Consumer may:



- React to the Event.

- Update its own derived state.

- Invalidate related Cache Entries.

- Update approved indexes.

- Trigger approved Plugin behavior.



A Consumer must not assume ownership of the resource that caused the Event.



---



# 8. Event Subscription



A Consumer may subscribe to approved Event types.



Subscriptions must be explicitly registered.



A subscription must identify the Event type it consumes.



A Consumer must not automatically receive unrelated Event types.



---



# 9. Event Boundary



The Event Engine provides Event delivery.



The Event Engine does not own the business operation represented by an Event.



Therefore:



Content Engine

→ Owns Content operation.



Media Engine

→ Owns Media operation.



User Engine

→ Owns User operation.



Cache Engine

→ Owns Cache operation.



Event Engine

→ Publishes and delivers approved Events.



---



## Acceptance Criteria



- [x] Event Engine purpose defined.

- [x] Event Engine objectives defined.

- [x] Event defined.

- [x] Event Name defined.

- [x] Event Payload defined.

- [x] Event Publisher defined.

- [x] Event Consumer defined.

- [x] Event Subscription defined.

- [x] Event boundary defined.



---









---



# 10. Event Dispatch



The Event Engine is responsible for dispatching published Events to approved Subscribers.



The dispatch process must:



1\. Validate the Event.

2\. Identify matching subscriptions.

3\. Deliver the Event to approved Consumers.

4\. Isolate Consumer execution from the Publisher.

5\. Report controlled failures when delivery cannot be completed.



The exact dispatch mechanism is implementation-specific.



---



# 11. Event Ordering



Event ordering must follow the guarantees defined by the Event Engine implementation.



Consumers must not assume a stronger ordering guarantee than the platform contract provides.



If an Event requires ordering for correct processing, the required ordering scope must be explicitly defined.



---



# 12. Event Delivery



An Event may be delivered to one or more registered Consumers.



Each Consumer must receive only Events for which it has an approved subscription.



Event delivery must not grant the Consumer ownership of the source resource.



---



# 13. Event Listener



An Event Listener is the approved Consumer callback or handler responsible for processing a received Event.



A Listener must:



- Accept the approved Event structure.

- Validate required Event data.

- Perform only its approved reaction.

- Handle failures without corrupting the source resource.



A Listener must not modify another Engine's private state directly.



---



# 14. Event Handler Isolation



A Consumer failure must not automatically prevent unrelated Consumers from receiving the same Event when the platform's delivery model permits independent processing.



A failing Listener must not corrupt the Event Publisher's source resource.



The Event Engine must keep Event delivery boundaries separate from resource ownership.



---



# 15. Event Validation



The Event Engine must validate:



- Event Name

- Event structure

- Required Event metadata

- Payload structure

- Approved Event type



An invalid Event must not be published as a valid platform Event.



---



# 16. Event Payload Isolation



Event Payloads must contain only information required by the Event contract.



A Publisher must not include unrelated private data merely because it is available internally.



Consumers must not assume access to data that is not part of the approved Event Payload.



---



# 17. Event and Cache



The Cache Engine may consume approved Events when a source-resource change requires cache invalidation.



Example boundary:



Source Engine

→ Resource changes.



Event Engine

→ Publishes approved Event.



Cache Engine

→ Reacts by invalidating affected cache.



The Event Engine does not perform cache invalidation itself.



---



# 18. Event and Search



The Search Engine may consume approved Events when a resource change requires Search-related processing.



Example boundary:



Content / Media Engine

→ Resource changes.



Event Engine

→ Publishes approved Event.



Search Engine

→ Performs its own approved reaction.



The Event Engine does not modify Search Index data directly.



---



## Acceptance Criteria



- [x] Event dispatch defined.

- [x] Event ordering boundary defined.

- [x] Event delivery defined.

- [x] Event Listener defined.

- [x] Event handler isolation defined.

- [x] Event validation defined.

- [x] Event Payload isolation defined.

- [x] Event and Cache boundary defined.

- [x] Event and Search boundary defined.



---









---



# 19. Event and Content



The Content Engine may publish approved Events when relevant Content state changes occur.



Possible lifecycle points may include:



- Content creation

- Content update

- Content deletion

- Other explicitly approved Content events



The exact Event types must be defined by the platform contract.



The Event Engine only delivers the Event.



The Content Engine remains responsible for Content lifecycle and state.



---



# 20. Event and Media



The Media Engine may publish approved Events when relevant Media state changes occur.



Possible lifecycle points may include:



- Media creation

- Media update

- Media deletion

- Other explicitly approved Media events



The Event Engine does not modify Media Resources.



The Media Engine remains responsible for Media lifecycle and storage.



---



# 21. Event and User



The User Engine may publish approved Events when relevant User state changes occur.



User-related Event Payloads must contain only information approved by the Event contract.



Private User information must not be exposed unnecessarily.



The User Engine remains responsible for User lifecycle and User data.



---



# 22. Event and Permission



The Permission Engine may participate in Event-driven workflows where authorization-related state changes require approved reactions.



Permission decisions must not be replaced by Events.



An Event indicating an authorization-related change does not itself grant permission.



Consumers must continue to use the Permission Engine for authorization decisions when required.



---



# 23. Event and Plugin



Plugins may publish and consume approved Events through the public Event Engine interface.



A Plugin may:



- Subscribe to approved platform Events.

- Publish approved Plugin Events.

- React to Events within its own responsibility.



A Plugin must not:



- Modify the Event Engine internals.

- Intercept unrelated Events without authorization.

- Bypass resource ownership boundaries.

- Assume delivery guarantees not provided by the Event contract.



---



# 24. Event and Theme



Themes may consume approved Events only when an Event-driven presentation update is explicitly required.



Themes must not use Events to bypass the Rendering Engine.



The Theme remains responsible for presentation definitions.



The Event Engine remains responsible only for Event delivery.



---



# 25. Event Recursion Protection



Event Consumers must avoid uncontrolled Event recursion.



If processing Event A publishes Event B, and Event B causes Event A to be published again, the implementation must prevent uncontrolled recursive processing where required.



The Event Engine must not silently create an infinite Event-processing loop.



---



# 26. Event Idempotency



Consumers should process Events safely when the same Event may be delivered more than once under the supported delivery model.



An Event Consumer must not perform irreversible duplicate operations solely because an Event was delivered repeatedly.



Where idempotency is required, the Consumer must use the approved Event identity or equivalent mechanism.



---



# 27. Event Failure Handling



Possible Event failures include:



- Invalid Event

- Invalid Payload

- No matching Subscriber

- Consumer failure

- Dispatch failure

- Listener failure



A failed Event operation must not automatically corrupt the source resource.



The failure behavior must follow the Event delivery contract.



---



# 28. Event Failure Isolation



A failed Consumer must remain isolated from unrelated Engines and Consumers.



For example:



Failed Cache Consumer

→ Must not corrupt Content.



Failed Search Consumer

→ Must not corrupt Media.



Failed Plugin Consumer

→ Must not corrupt User data.



The Event Engine must preserve resource ownership boundaries.



---



## Acceptance Criteria



- [x] Content Event boundary defined.

- [x] Media Event boundary defined.

- [x] User Event boundary defined.

- [x] Permission Event boundary defined.

- [x] Plugin Event boundary defined.

- [x] Theme Event boundary defined.

- [x] Event recursion protection defined.

- [x] Event idempotency defined.

- [x] Event failure handling defined.

- [x] Event failure isolation defined.



---











---



# 29. Event Security Boundary



The Event Engine must treat Event Payloads according to their approved visibility and security requirements.



An Event must not expose:



- Authentication credentials

- Private session information

- Unrelated private User data

- Internal storage details

- Private implementation details



A Consumer must receive only the information required by its approved Event subscription.



---



# 30. Event Authorization



Publishing or consuming an Event may require authorization according to the applicable platform rules.



The Event Engine must not treat Event delivery as a replacement for Permission evaluation.



If a Consumer performs a protected resource operation after receiving an Event, the Consumer must perform the applicable Permission check before that operation.



---



# 31. Event Ownership



The Event Engine does not own the resource represented by an Event.



For example:



Content Event

→ Content Engine remains resource owner.



Media Event

→ Media Engine remains resource owner.



User Event

→ User Engine remains resource owner.



Cache Event Reaction

→ Cache Engine remains cache owner.



The Event Engine only transports the approved occurrence.



---



# 32. Event Registration



Event Publishers and Consumers must use approved Event Engine interfaces.



A registration must identify:



- Publisher or Consumer context

- Event type

- Approved handler or delivery target

- Required configuration



Private Event Engine internals must not be directly modified by Publishers or Consumers.



---



# 33. Event Lifecycle



An Event follows the general lifecycle:



Create

→ Validate

→ Publish

→ Match subscriptions

→ Dispatch

→ Consume

→ Complete or Fail



The exact lifecycle may vary according to the supported Event delivery implementation.



The Event Engine must preserve the defined public behavior regardless of internal implementation.



---



# 34. Event Retry Boundary



If the Event implementation supports retry behavior, retry rules must be explicitly defined by the Event delivery contract.



A Consumer must not assume unlimited retries.



Repeated Event delivery must remain safe according to the Consumer's idempotency requirements.



Retry behavior must not create uncontrolled recursive processing.



---



# 35. Event Observability



The Event Engine may expose controlled operational information such as:



- Event Published

- Event Dispatched

- Event Consumed

- Event Failed

- Event Retried

- Subscription Registered

- Subscription Removed



Operational information must not expose protected Event Payload contents unless explicitly authorized.



---



# 36. Event Compatibility



Changes to the internal Event Engine implementation must preserve the public Event contract when the change is non-breaking.



Existing Publishers and Consumers must remain compatible with supported Event Engine versions.



Breaking Event changes must follow the project's versioning and migration rules.



---



# 37. Event Engine Non-Goals



The Event Engine does not own:



- User Resources

- Content Resources

- Media Resources

- Search Indexes

- Cache Entries

- Permission rules

- Theme resources

- Plugin business logic

- Resource storage



The Event Engine is responsible only for approved Event publishing, subscription, and delivery behavior.



---



## Acceptance Criteria



- [x] Event security boundary defined.

- [x] Event authorization boundary defined.

- [x] Event ownership boundary defined.

- [x] Event registration defined.

- [x] Event lifecycle defined.

- [x] Event retry boundary defined.

- [x] Event observability defined.

- [x] Event compatibility defined.

- [x] Event Engine non-goals defined.



---











---



# 38. Final Event Resolution Rules



The Event Engine must process Events through approved public interfaces.



The general Event resolution flow is:



1\. Create the Event.

2\. Validate the Event Name.

3\. Validate the Event Payload.

4\. Identify approved Subscribers.

5\. Dispatch the Event.

6\. Execute approved Consumers.

7\. Record completion or failure.



The Event Engine must not bypass Event validation or subscription rules.



---



# 39. Event Contract



Every Event must follow an approved Event contract.



The contract must define:



* Event Name

* Event Payload structure

* Publisher responsibility

* Consumer expectations

* Applicable visibility rules

* Applicable delivery behavior



Publishers and Consumers must depend on the public Event contract rather than private implementation details.



---



# 40. Event Payload Contract



Event Payloads must contain only the information required by the Event.



Payloads must not unnecessarily expose:



* Authentication credentials

* Session secrets

* Private implementation details

* Internal storage information

* Unrelated User data

* Unrelated resource data



Consumers must treat the Event Payload as the approved data contract for that Event.



---



# 41. Event Isolation Contract



Events must preserve Engine and resource ownership boundaries.



The Event Engine must not allow Event processing to become an uncontrolled method for directly modifying another Engine's internal state.



The general boundary is:



Source Engine

→ Performs resource operation.



Event Engine

→ Announces approved occurrence.



Consumer

→ Performs its own approved reaction.



---



# 42. Event Failure Contract



Event failures must be handled safely.



A failed Event operation must not automatically roll back or corrupt a source resource that was already successfully committed unless the applicable resource contract explicitly defines transactional behavior.



A failed Consumer must not be treated as evidence that the source resource itself is invalid.



Failure reporting must remain explicit.



---



# 43. Plugin Event Contract



Plugins may participate in the Event system through approved public interfaces.



Plugins may:



* Publish approved Events.

* Subscribe to approved Events.

* Register approved Event Consumers.



Plugins must not:



* Modify Event Engine internals.

* Receive unrelated private Events without authorization.

* Bypass Permission checks through Events.

* Depend on undocumented Event delivery guarantees.

* Use Events to directly access another Plugin's private implementation.



---



# 44. Event and Queue Boundary



Event delivery and queued background processing are separate responsibilities.



The Event Engine defines approved Event publishing and consumption behavior.



If the platform later uses a Queue Engine for asynchronous processing, that Queue Engine must consume or schedule work through approved interfaces.



The Event Engine must not assume a specific Queue implementation.



---



# 45. Event and Cache Boundary



The Cache Engine may react to approved Events.



For example:



Resource Updated

→ Event Published

→ Cache Consumer receives Event

→ Relevant Cache Entry invalidated



The Event Engine does not perform cache invalidation itself.



---



# 46. Event and Search Boundary



The Search Engine may react to approved resource Events.



For example:



Content Updated

→ Event Published

→ Search Consumer receives Event

→ Search representation updated



The Event Engine does not directly modify the Search Index.



---



# 47. Codex Implementation Rules



When implementing the Event Engine, Codex must:



* Follow the frozen architecture from Documents 001–017.

* Follow the defined folder structure.

* Use approved public interfaces.

* Preserve Event Publisher and Consumer isolation.

* Preserve resource ownership boundaries.

* Preserve Plugin isolation.

* Preserve Permission boundaries.

* Preserve Cache ownership boundaries.

* Preserve Search ownership boundaries.

* Keep Event validation mandatory.

* Keep Event Payloads minimal and approved.

* Avoid introducing undocumented Event types.

* Avoid introducing a specific message broker, event bus provider, or transport technology as an architectural requirement unless another document explicitly defines one.

* Avoid assuming delivery ordering, retries, or persistence guarantees that are not explicitly documented.



If an implementation detail is not defined by this document, Codex must not silently introduce a conflicting Event architecture.



---



# 48. Final Acceptance Criteria



* [x] Event Engine purpose defined.

* [x] Event Engine objectives defined.

* [x] Event definition established.

* [x] Event Name established.

* [x] Event Payload established.

* [x] Event Publisher defined.

* [x] Event Consumer defined.

* [x] Event Subscription defined.

* [x] Event Dispatch defined.

* [x] Event Listener defined.

* [x] Event validation defined.

* [x] Event ordering boundary defined.

* [x] Event delivery boundary defined.

* [x] Event Payload isolation defined.

* [x] Content Event boundary defined.

* [x] Media Event boundary defined.

* [x] User Event boundary defined.

* [x] Permission Event boundary defined.

* [x] Plugin Event boundary defined.

* [x] Theme Event boundary defined.

* [x] Cache Event boundary defined.

* [x] Search Event boundary defined.

* [x] Event recursion protection defined.

* [x] Event idempotency boundary defined.

* [x] Event failure handling defined.

* [x] Event failure isolation defined.

* [x] Event security boundary defined.

* [x] Event authorization boundary defined.

* [x] Event lifecycle defined.

* [x] Event retry boundary defined.

* [x] Event observability defined.

* [x] Event compatibility defined.

* [x] Queue boundary defined.

* [x] Codex implementation rules defined.



---



# 49. Document Status



This document defines the Event Engine specification for Favorite CMS.



The Event Engine must be implemented according to this document and the frozen architecture established by Documents 001–017.



The Event Engine provides a controlled mechanism for platform Events while preserving loose coupling between independent Engines and Extensions.



No specific event transport, message broker, Event storage technology, retry provider, or asynchronous processing system is required by this document unless a future architecture document explicitly defines one.



Any future breaking change to the Event Engine must follow the project's versioning and migration rules.



---



End of Document



Next Document:



019-queue-engine.md



