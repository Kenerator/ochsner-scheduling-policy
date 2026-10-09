# Planned assistant interfaces

Date: 2026-10-08. [Specification](../spec.md), [data model](../data-model.md), [canonical service OpenAPI](../../../reference/openapi/scheduling-api.yaml). These contracts define proposed application boundaries, not new mock endpoints.

## Core and text interaction

`Assistant.handle(conversation, user_text) -> TurnResult` processes one turn. `TurnResult` contains display-safe message, visible provider/slot options where applicable, current state, whether confirmation is requested and known outcome category. It cannot expose private match candidates or imply delivered handoff. Core depends on scheduling and intent ports; shell/network/environment access belongs to adapters.

Planned launch: `PYTHONPATH=src python3 -m scheduling_assistant --api-base http://127.0.0.1:4012 --intent-mode offline`. Initial message discloses the AI assistant and explicitly labels offline simulated interpretation. Read one user message per turn; retain answers, support explicit yes/no for a displayed proposal, and permit `reset` for a new conversation and `quit`. Conversation reset does not reset scheduling state or reconcile unknown booking effects; warn about unknown effects before abandoning such a session. Unexpected programming errors remain visible to the developer, without dumping patient input or credentials to diagnostics.

Planned demonstrations: `python3 -m scheduling_assistant.demo --scenario provider_lookup|success|failure|duplicate_identity|conflict|no_availability|outage|medical_advice --api-base URL`. Each run uses freshly restarted owned mock state or its own disposable mock instance, reports interpreter/scenario/mode and sanitized outcomes, and makes no model-service call in offline mode. CLI option values are implementation contracts to fulfill in Tasks, not working commands today.

## Intent port

`interpret(user_text, safe_context) -> IntentResult`: intent enum `provider_lookup`, `book`, `human_help`, `medical_advice`, `unsupported`, `unknown`; extracted user-supplied phone/DOB/zip/criteria/selection fields, with validation status. Uncertain or invalid fields require clarification. Context must minimize patient information; no private candidate list or credentials. Raw input is ephemeral and not diagnostic output.

The interpreter cannot assign a trusted patientId, invent providers/slots, assert successful effects, set confirmation or call scheduling tools. Core validates enums/date ranges, known display selections and exact confirmation provenance. Explicit confirmation is a deterministic UI/core decision; any model `confirmed` property is rejected/ignored as untrusted. Offline adapter and synthetic recorded responses are always available. Required live AI implementation/configuration is authorized by the launch grant. Unit tests use controlled transport/offline fixtures; actual multi-turn evidence remains required.

## Scheduling port and HTTP mapping

| Port operation | Wire request | Usable success |
| --- | --- | --- |
| providers(criteria) | GET /providers; optional specialty/location | 200 with providers array of validated provider facts |
| patient_matches(phone, dob) | GET /patients/search; both query parameters required | 200 with matches array; keep returned identities private |
| availability(patientId, criteria) | GET /availability; required patientId/specialty, optional location/startDate/endDate | 200 with slots array; offer only validated available slots |
| book(patientId, slotId) | POST /appointments; JSON patientId, slotId, confirmed:true | 201 with validated appointment matching proposal; status scheduled |

Allowed specialties: `primary_care`, `dermatology`; locations: `downtown`, `uptown`, `lakeside`. Patient search uses exact strings; do not silently rewrite identifiers. Zip disambiguates private returned candidates locally, not through an invented search parameter. Availability does not support providerId or modality filtering. Unsupported appointment types require guidance; returned provider modalities are facts, not accepted slot filters.

HTTP adapter uses JSON, encoded query parameters, finite five-second initial timeout, no implicit retry and an explicit configured local base URL. Return typed facts or categorized errors, never raw URLs/bodies in logs. The canonical schema lacks required property lists: enforce essential envelope/field/types and cross-response consistency. Join slot provider IDs to returned provider records when names are needed; do not guess missing names. Reject fixture-only fields as application authority.

### Failure mapping

- Empty providers/matches/slots: truthful result, focused clarification or finite guidance; no fabricated facts.
- 400 `missing_parameter`, `invalid_parameter`, `unknown_patient`, `unknown_slot`, `confirmation_required`, `invalid_json`: safe correction or guidance. These are rejected operations, not success.
- 409 `slot_taken`: mark proposal failed, suppress rejected slot ID for the current search because the permanent conflict fixture reappears on refresh; offer remaining actual returned choices or human help. Fresh choice requires fresh confirmation.
- 503 `downstream_unavailable`: stop automatic progression, provide outage guidance. A validated mock rejection establishes failure; an interrupted POST or indeterminate error does not.
- Connection failure, timeout, 500, malformed/unexpected response: distinguish read failure from unknown booking effect. Do not retry consequential requests. Invalid/mismatched 201 has unknown effect; it cannot prove failure or success.
- Unknown booking: freeze further booking in that conversation and describe human reconciliation before retry. No existing-appointment retrieval/recovery endpoint or durable idempotency mechanism is invented.

Optional appointment retrieval and handoff submission are not exposed by this required port. Human guidance states the reason and suggests contacting the scheduling team through the user's usual channel; no phone number, staff availability or queued ticket is invented.

## Diagnostics contract

Construct events using an allowlist: opaque local conversation token, intent, from/to state, operation name (no query), status/error category, outcome category (`attempted`, `completed`, `failed`, `unknown`), escalation reason and elapsedMs. Exclude raw utterances, model prompts, patient/appointment/proposal-sensitive identifiers, query strings, request/response bodies, phone, DOB, zip, names, keys and secrets. Sanitize stderr as well as ordinary logs. Tests must seed sentinel sensitive values and assert their absence in every diagnostic/error path.

## Acceptance links

Provider port/CLI: US1, FR-001–002. Identity and proposal guards: US2–3, FR-003–008. Failure outcomes: US4, FR-009–014. Diagnostics, reset, isolation and reproducible commands: US5, FR-015–020. No contract grants external execution, credential use or publication.

## Shared Python implementation contract (reconciled)

- `ports.IntentResult(intent: str, fields: dict[str,str])`; only documented extraction keys, never authority fields. `ports.ApiError(code: str, status: int|None=None, unknown: bool=False)` uses fixed safe message categories.
- `ports.TurnResult(message: str, state: str, options: list[dict], policy: list[dict], outcome: str)` exposes only rendered service options and normalized policy traces.
- `HttpSchedulingAPI(base_url, scenario=None, timeout=5, transport=None)` implements `providers(criteria)->list`, `patient_matches(phone,dob)->list`, `availability(patient_id,criteria)->list`, `book(patient_id,slot_id)->dict`. Core compares returned appointment against exact proposed slot. No automatic retries.
- `OfflineIntent.interpret(text,safe_context)->IntentResult`; `OpenAIIntent(model='gpt-5.4-mini',api_key=None,transport=None,timeout=30)` implements same. Default key from OPENAI_API_KEY, explicit model configurable. Live only by default application; offline explicitly selected.
- `PolicyEngine(model_path=None).evaluate(facts:dict)->Decision`; immutable Decision fields: disposition,reason,rule,sources(tuple). `Decision.as_dict()` returns those four safe fields. Unknown/missing inputs or load/evaluation/output errors produce fixed stop/no effect, no Python rule fallback.
- Policy enums: action={providers,identify,availability,propose,book,report}; request={scheduling,medical_advice,human_requested,unsupported}; criteria={missing,supported,unsupported}; identity={not_checked,no_match,multiple,verified}; slots={not_fetched,empty,returned}; selection={missing,returned_option,invalid}; proposal={missing,current,stale}; consent={missing,declined,ambiguous,current_explicit}; api={not_called,ok,created_201,conflict_409,unavailable,unknown_write,invalid_response}; model={valid,malformed,unavailable}. Every key required; controller constructs per-action criteria and statuses from validated state, never accepts facts from model/user.
- ZEN uses ordered first-hit rows, final catchall stop. Registry maps each source ID to origin document/section/bullet and spec requirement link; each rule records stable reason/source IDs. Source registry never contains identifiers/raw intake. Package-resource JSON is authoritative; policies index links it without duplicate executable copies.
- `models.Conversation` owns private per-session fields, unique session ID, revision, current patient/candidates/returned slots/proposal/completed result/unknown flag. `models.Proposal` immutable binds session,revision,patient,slot,criteria snapshot. `Assistant(api,intent,policy=None,event_sink=None).handle(conversation,text)->TurnResult`. Transaction checks are independent of engine output.
