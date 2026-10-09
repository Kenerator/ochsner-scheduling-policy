# Planning research

Date: 2026-10-08. Inputs: [specification](spec.md), [decisions](../../docs/product/decisions.md), supplied assignment/policies and [canonical scheduling API](../../reference/openapi/scheduling-api.yaml). Local source inspection is the research basis; no external model call or new installation was performed.

## Source precedence and required slice

- Decision: Follow assignment scope, policy safeguards and OpenAPI returned facts, in that order of responsibility. Implement provider search and confirmed booking; demonstrate no-match and duplicate-match safeguards within booking.
- Rationale: Explicit developer Q1 resolves the lookup scenario conflict. Identity safety does not require appointment retrieval.
- Alternatives considered: Making retrieval or automated handoff mandatory would expand approved scope. Both remain optional capabilities.

## Runtime and interaction

- Decision: Python 3.11+ reusable scheduling package, standard-library HTTP/JSON/dataclasses/unittest, thin interactive CLI and separate deterministic demo entry point. No new backend or database.
- Rationale: Existing project already declares this runtime and has a CLI/core example. CLI meets the assignment text interaction requirement with minimal dependencies.
- Alternatives considered: Marimo conversation and policy inspector are accepted candidate requirements. Existing Marimo prerequisite evidence is retained; UI reuses the guarded core. Generic poc_demo behavior alone is insufficient for scheduling.

## Scheduling transport and failure semantics

- Decision: Use the unchanged supplied mock adopted under reference/, on candidate port 4012. Validate successful envelopes and essential fields before accepting facts; set finite per-request timeouts (initial design: five seconds), never automatically retry booking. Test on separate owned server instances/ports.
- Rationale: Supplied reference implements actual conflict, empty availability and outage behavior. Fixture internals cannot authorize or predict actions. Independent read-only research confirmed the permanent conflict slot must be suppressed after rejection and mock responses need stronger application validation than the schema alone. Restart resets state; there is no reset API, durable idempotency or production authentication.
- Alternatives considered: Schema-generated mock responses omit these behaviors; a custom scheduling backend adds needless work. Sharing candidate state with tests makes repeatability unreliable.

## Model boundary and offline execution

- Decision: Define a replaceable intent-extraction port that returns validated structured intent and user-supplied fields only. Provide deterministic offline interpretation and recorded synthetic model responses for required local acceptance. Implement the required authorized OpenAI model adapter; explicit default gpt-5.4-mini has one qualified structured call, with actual app multi-turn qualification still required.
- Rationale: Model reasoning may classify text, but deterministic policy owns identity, displayed options, confirmation and effects. Planning itself made no credential call; launch authority separately permits the bounded application capability/integration calls. Offline runs must explicitly identify simulated interpretation and must not claim live AI qualification.
- Alternatives considered: A model with direct booking tools can bypass safeguards. Treating the live AI assignment expectation as optional or claiming offline parsing meets it would conceal unfinished work. This Plan defines the boundary while implementing the already-authorized required service integration.

## Identity and exact confirmation

- Decision: Resolve returned matches using phone/date of birth; if multiple, ask for zip code and filter the private returned candidates locally. Continue only on exactly one result. Bind an immutable proposal to conversation, identity revision and selected offered slot; accept explicit yes only after the proposal is displayed, invalidate on changes, cache completed outcomes in that conversation.
- Rationale: Search does not accept zip as a declared API parameter. The mock does not enforce the assistant's identity or confirmation provenance, so the core must. Same-session suppression is not durable or distributed duplicate prevention.
- Alternatives considered: Listing candidate details leaks identities. Inferring confirmation from model text or accepting patient IDs bypasses required safeguards. Automatic retry after a lost response risks duplicate effects.

## Diagnostics and demonstration

- Decision: Emit allowlisted diagnostic fields (opaque local conversation token, intent/state, operation name, status/error category, outcome, reason and elapsed milliseconds). Exclude raw text, query URLs, bodies, phone, DOB, zip, patient/appointment IDs and credentials. Keep user display separate from diagnostics.
- Rationale: Sanitization by construction is stronger than masking known strings; supplied request logs omit query values but are not a substitute for core diagnostics. Support needs known versus unknown effects and finite next steps.
- Alternatives considered: Raw transcripts and HTTP debug dumps violate privacy. Full tracing and an admin console add unaccepted scope.

## Remaining external decisions

No unresolved design clarification blocks Phase 1. Persona pins, assignment receipt baseline, public submission and recording remain pending; live-model configuration and qualification are required implementation work. They are not silently resolved by this local Plan.

## Superseding approved-lane reconciliation

Earlier suggestions that Marimo/liveAI were unaccepted follow-ons or that Python guards replaced an engine are superseded by specFR021–023 and plan reconciliation. ZEN2.1.2 is selected actual policy execution, Marimo0.25.1 is selected UI, and live Responses extraction is required. Prepared dependency readiness is reused with candidate integration and fresh-clone qualification still required. No engine is dropped due to a small rule count; no other engine is mandated without a distinct capability.
