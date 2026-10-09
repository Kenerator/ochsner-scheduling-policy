# Feature Specification: AI Appointment Scheduling Assistant

**Feature Branch**: Local `main`; no Git extension or feature branch requested

**Created**: 2026-10-08

**Status**: Specification validated — Q1 resolved; ready for planning; implementation not started

**Input**: User description: "Include the client requirements indexed by docs/product/RFP/README.md. Reconcile docs/product/user-stories.md and Persona mappings with supplied intake."

## Clarifications

### Session 2026-10-08

- Q: Does the required duplicate-identity scenario make existing-appointment lookup mandatory, or does the approved common contract keep lookup optional and demonstrate identity clarification within booking? → A: Existing approved common contract establishes assignment.md/policies/OpenAPI source precedence and optional appointment lookup; retain duplicate-identity clarification within booking. No new mandatory retrieval scope.

## User Scenarios & Testing *(mandatory)*

The supplied scenarios are the acceptance basis. Story wording below is inferred from those scenarios and requirements; this origin does not make explicit requirements optional. No named or pinned Persona was supplied. Each mapping below is an unresolved placeholder linked to [selected personas](../../docs/product/personas.md), rather than an invented identity or validated research finding.

### User Story 1 - Find providers without identifying a patient (Priority: P1)

As a person seeking care, I want to ask which providers serve a specialty and location, so I can choose where to seek an appointment.

**Origin/basis**: INFERRED wording; SPECIFIED journey in assignment Required 1–3 and `provider_lookup` scenario. **Scope**: Required. **Persona**: Primary-user placeholder, selection pending.

**Why this priority**: Useful independently, with no patient-specific disclosure.

**Independent Test**: Ask in ordinary text for downtown primary care providers; inspect the returned providers and scheduling-service evidence without providing patient identifiers.

**Acceptance Scenarios**:

1. **Given** a provider lookup request, **When** specialty or location needs clarification, **Then** the assistant asks a focused follow-up, retains previous answers, and returns only matching providers supplied by the scheduling service.
2. **Given** a public provider search, **When** results are shown, **Then** patient identification is not required and neither patient records nor invented providers are shown.
3. **Given** unsupported criteria or service unavailability, **When** search cannot complete, **Then** the assistant explains the specific limitation and provides a truthful human-help next step.

---

### User Story 2 - Book the selected appointment with confirmation (Priority: P1)

As a patient seeking an appointment, I want a short conversation that identifies me, offers available appointments and lets me confirm a specific choice, so I know what has actually been booked.

**Origin/basis**: INFERRED wording; SPECIFIED assignment booking flow and `happy_path_booking`. **Scope**: Required. **Persona**: Patient-user placeholder, selection pending.

**Why this priority**: Core end-to-end outcome with identity and action safeguards.

**Independent Test**: With reset synthetic scheduling state, provide the supplied unique-match identity, primary care and downtown preferences over multiple turns, choose a returned slot and explicitly confirm it; verify exactly one successful appointment and matching reported details.

**Acceptance Scenarios**:

1. **Given** missing phone, date of birth or specialty, **When** booking is requested, **Then** the assistant gathers missing information in follow-up turns and identifies a unique patient before patient-specific action.
2. **Given** a uniquely identified patient, **When** availability is requested, **Then** only returned available slots are offered with enough provider, specialty, location and time information to make a choice; a provider listing alone is not availability.
3. **Given** a chosen returned slot, **When** the assistant requests confirmation, **Then** it states the exact booking choice and performs no booking until the user explicitly confirms that choice.
4. **Given** refusal, ambiguous assent, an unoffered choice, or a changed patient/slot, **When** the conversation continues, **Then** the assistant does not book using stale or missing confirmation; a changed valid choice requires fresh confirmation.
5. **Given** explicit confirmation, **When** the service confirms the booking, **Then** the assistant reports only returned appointment details, distinguishes success from failure or unknown outcome, and does not repeat a completed booking for repeated confirmation in the same session.

---

### User Story 3 - Resolve identity safely or stop (Priority: P1)

As a patient whose identity cannot yet be resolved, I want a safe clarification or a human-help next step, so another person's details are not disclosed and no guessed identity is used.

**Origin/basis**: INFERRED wording; SPECIFIED identity policies, `no_patient_match` and `multiple_patient_matches`. **Scope**: Required identity safety, including the selected minimum demonstrated failure case: no patient match. **Persona**: Patient-user placeholder, selection pending.

**Why this priority**: Protects patient-specific actions independently of booking completion.

**Independent Test**: Use supplied no-match and duplicate-match inputs; inspect output and action records before any booking or appointment-detail retrieval.

**Acceptance Scenarios**:

1. **Given** no matching patient, **When** the search completes, **Then** no patient or appointment data is exposed, the user is asked to check/provide identifying information, and an unresolved case receives a human-help next step without guessing or a retry loop.
2. **Given** multiple matching patients, **When** identity remains ambiguous, **Then** the assistant asks for the distinguishing zip code without enumerating candidate identities or zip codes; no patient-specific action occurs before exactly one returned record matches the user's answer.
3. **Given** no unique match after clarification, **When** further safe identification is unavailable, **Then** the assistant stops patient-specific work and hands off truthfully.
4. **Given** a request for existing appointment details, **When** lookup is outside the required slice, **Then** the assistant explains that limit and offers human help without claiming retrieval or exposing patient-specific details. Duplicate-identity clarification is demonstrated within booking: a unique zip-code match permits availability and confirmed booking; an unresolved match permits neither.

---

### User Story 4 - Receive truthful failure and human-help guidance (Priority: P1)

As a person whose request cannot safely complete, I want a specific explanation and a finite next step, so I do not mistake an unsuccessful operation for a completed appointment or a delivered handoff.

**Origin/basis**: INFERRED wording; SPECIFIED policies and assignment safety boundaries; scenario examples include conflict, no availability, outage and medical advice. **Scope**: Required safety responses when encountered; optional automated handoff creation is not implied. **Persona**: Primary-user/patient placeholder, selection pending.

**Why this priority**: The assistant must remain safe when normal progress fails.

**Independent Test**: Inject each failure using supplied fixtures or an unsupported text request; inspect output for fabricated success, medical advice, leaks and unbounded repetition.

**Acceptance Scenarios**:

1. **Given** a slot is rejected as taken, **When** booking fails, **Then** the assistant explains that nothing was booked and offers remaining service-returned choices or human help; another slot requires new confirmation.
2. **Given** empty availability, **When** no appointment can be offered, **Then** the assistant states that result and offers a changed search or human help without inventing slots.
3. **Given** unavailable scheduling service, **When** a request fails, **Then** the assistant stops automatic progress, explains the outage and gives a finite human-help next step, without claiming an appointment or handoff was created.
4. **Given** medical-advice, unsupported specialty/location/type, out-of-scope or explicit human-help requests, **When** the assistant responds, **Then** it provides no medical advice or triage, stops the unsupported work and directs the user to human assistance.
5. **Given** an uncertain booking response, **When** success cannot be established, **Then** the assistant labels the outcome unknown and requests reconciliation before retrying the consequential action.

---

### User Story 5 - Understand outcomes and recover responsibly (Priority: P2)

As the support/admin teammate, I want sanitized diagnostic and recovery context, so I can understand what happened without asking the user to repeat work or taking unsafe action.

**Origin/basis**: INFERRED seed migrated from [story background](../../docs/product/user-stories.md), aligned with SPECIFIED observability policies and project Constitution. **Scope**: Required documentation/basic diagnostic coverage; no admin console or live staff delivery. **Persona**: Support/Admin placeholder, selection pending.

**Why this priority**: Helps demonstrate, inspect and maintain the required workflows.

**Independent Test**: Inspect a booking success and unresolved failure record with the documented recovery steps; distinguish attempts, completed effects, unknown effects and escalation reason without sensitive identifiers.

**Acceptance Scenarios**:

1. **Given** a completed or unresolved flow, **When** the diagnostic record is inspected, **Then** intent/state, scheduling calls, outcomes/errors, escalation reason and basic latency are available, while full phone, birth date, other sensitive identifiers and secrets are absent in plaintext.
2. **Given** a fresh local copy and declared prerequisites, **When** a reviewer follows the documentation, **Then** setup, mock-service startup, assistant launch, verification, reset, success and failure demonstrations require no undocumented steps.
3. **Given** an unresolved case, **When** recovery instructions are read, **Then** known facts, missing information, attempted/completed/unknown effects and a useful next step are distinguishable; no delivered support contact is claimed without evidence.

### Edge Cases

- Missing/invalid identifiers or criteria prompt correction without leaking raw sensitive input in diagnostics.
- Unsupported requests and empty provider results are explained without fabricating a provider or broadening criteria silently.
- Duplicate identities are not authentication; a unique synthetic match only enables the prototype's guarded workflow.
- A stale slot, changed selection, refusal or repeated confirmation never silently books a different appointment.
- Malformed, missing or inconsistent scheduling responses cannot establish identity, availability or success.
- Loss of a response after booking is an unknown effect, not evidence of failure suitable for an automatic retry.
- Service outage may also prevent automated handoff; guidance must distinguish an offered next step from a queued request.
- New conversations do not inherit another user's identity or confirmation. Scheduling state reset is separate from conversation reset.
- Returned fixture times have a fixed offset and relative dates; no daylight-saving or real scheduling-calendar claim is made.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The assistant MUST disclose that it is AI and support text-based, multi-turn interaction that recognizes provider lookup and appointment booking, asks for missing information, and preserves relevant answers within the conversation. (US1–2)
- **FR-002**: Provider results MUST come from the supplied scheduling service and respect supported search criteria; public provider lookup MUST NOT require patient identity. (US1)
- **FR-003**: Before patient-specific disclosure or booking, the assistant MUST gather the required identity information and resolve exactly one service-returned patient. User-supplied patient IDs or model guesses MUST NOT bypass identification. (US2–3)
- **FR-004**: No matches MUST lead to safe clarification and, if unresolved, human-help guidance; multiple matches MUST prompt distinguishing clarification before proceeding and hand off if still ambiguous. Candidate patient details MUST NOT be exposed to disambiguate. (US3)
- **FR-005**: Availability MUST be fetched for the identified patient and supported criteria. Only slots returned as available by the scheduling service MAY be offered or selected; fixture internals MUST NOT be used to predict or override service decisions. (US2)
- **FR-006**: The assistant MUST show appointment options and the exact proposed choice before asking for explicit booking confirmation. Missing, ambiguous or withdrawn confirmation MUST cause zero booking actions. (US2)
- **FR-007**: Confirmation MUST bind the identified patient and selected offered slot. A changed choice invalidates confirmation; repeated confirmation of a completed proposal in one session MUST NOT create another booking. (US2)
- **FR-008**: The assistant MUST submit a confirmed booking only after FR-003–007 hold, and report success only from a successful scheduling response, using its returned appointment details. (US2)
- **FR-009**: The assistant MUST NOT invent patient, provider, slot, appointment, confirmation or handoff results. Failed, completed and unknown outcomes MUST be distinguished. (US1–5)
- **FR-010**: A rejected/taken slot MUST produce a truthful failure explanation and another returned option or human-help next step, without an automatic alternate booking. (US4)
- **FR-011**: Empty availability MUST produce an explicit no-availability explanation and an alternate search or human-help next step. (US4)
- **FR-012**: Scheduling unavailability MUST stop automatic progress and provide a specific explanation and finite human-help next step; unknown consequential effects MUST be reconciled before retry. (US4)
- **FR-013**: Medical-advice requests MUST receive no advice or triage and MUST lead to human-help guidance. User requests for a human, unsupported criteria and out-of-scope tasks MUST also lead to human-help guidance. (US4)
- **FR-014**: Human-help guidance MUST describe a truthful next step and reason. It MUST NOT claim an actual referral, contact, ticket or queued handoff unless that action is implemented and confirmed. (US3–5)
- **FR-015**: Diagnostics MUST include intent/state, scheduling calls, outcomes/errors, escalation reason and basic elapsed-time measurements, excluding plaintext full birth date, phone, sensitive identifiers, secrets and keys. (US5)
- **FR-016**: The prototype MUST use synthetic data and the supplied mock scheduling service. It MUST isolate conversations and retain the ability to reset deterministic success/failure demonstrations. Matching synthetic identifiers MUST NOT be described as production authentication or authorization. (US2–5)
- **FR-017**: Verification MUST cover provider lookup, end-to-end confirmed booking, no patient match, duplicate-match identity safeguards, refusal/changed confirmation, conflict, empty availability, outage, medical advice and sanitized diagnostic/recovery behavior, with meaningful success, negative and boundary cases. (US1–5)
- **FR-018**: Documentation MUST give setup, mock startup, assistant launch, exact verification commands, reset and success/failure demonstrations, design boundaries, assumptions, tradeoffs, known limitations and next steps, with a short linked document index and actual as-built references after implementation. (US5)
- **FR-019**: A walkthrough plan MUST cover provider lookup, booking, one failure/handoff, architecture and tradeoffs in at most five minutes. Actual recorded/delivered video status MUST remain separate from a script or plan. (US5)
- **FR-020**: The project MUST exclude committed secrets and real personal data. External model-service use, repository publication, pushing and delivery MUST respect separate Operator authorization; defining those assignment dependencies does not authorize their execution. (US5)

### Key Entities *(include if feature involves data)*

- **Conversation**: Current intent, gathered answers, identity resolution, displayed options, pending confirmation and known outcome; isolated from other conversations.
- **Patient match**: Service-returned synthetic identity and distinguishing information used only for guarded patient-specific work; not an authenticated user identity.
- **Provider**: Service-supplied provider identity, name, specialties, locations and modalities; a provider is not an available slot.
- **Available slot**: Service-supplied provider, specialty, location, start time and availability; may become unavailable before booking.
- **Booking proposal**: The exact identified patient and selected offered slot awaiting explicit confirmation.
- **Appointment**: Service-confirmed booking identity and scheduled details; distinct from a proposal or failed attempt.
- **Recovery context**: Sanitized intent, progress, errors, latency, escalation reason and known/unknown effects. A queued handoff record exists only if the optional handoff capability is implemented and confirmed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In every supplied provider-lookup acceptance run, all displayed providers match the scheduling results and zero patient identifiers are required. (FR-001–002)
- **SC-002**: A reviewer can complete the synthetic happy-path booking over at least two user turns, see the selected appointment before confirmation, and receive one matching confirmed appointment with no booking before explicit confirmation. (FR-001,003,005–008)
- **SC-003**: All required identity and confirmation acceptance cases produce zero unauthorized patient-specific disclosures or unconfirmed bookings; duplicate candidates remain hidden and unresolved identity never proceeds. (FR-003–009)
- **SC-004**: Every specified failure acceptance case produces a specific truthful explanation and finite next step, with zero fabricated success, medical-advice responses or automatic retry loops. The no-match case is demonstrated end to end. (FR-004,009–014)
- **SC-005**: A reviewer can identify intent, attempted action, known outcome, escalation reason and elapsed time from each success/failure diagnostic record, with zero plaintext sensitive identifiers or secrets in those records. (FR-015,020)
- **SC-006**: Following documented prerequisites and commands from a clean local copy, a reviewer can run the assistant, repeat the provider/booking/failure demonstrations after reset and run the declared verification without undocumented steps. (FR-016–018)
- **SC-007**: The planned walkthrough contains all four assignment topics and fits within five minutes; any recorded walkthrough is checked against that duration and its actual demonstrated behavior. (FR-019)

## Assumptions

### Intake reconciliation and source coverage

- Reviewed all 11 text entries in the [RFP manifest](../../docs/product/RFP/manifest.json): assignment; policies; scheduling contract; mock README and reference server; scenarios; data README and all four fixture files. Original bytes and manifest metadata were verified. Supplied code was read as reference, not executed during Specify.
- The sole attachment, `.DS_Store`, was identified as Apple Desktop Services metadata. Its content was not interpreted as product requirements; no document/image attachment remains awaiting conversion.
- The assignment's broad instruction to stop when multiple patients match is read together with its explicit detailed policy/scenario requiring clarification first: stop patient-specific progress while asking a safe distinguishing question, then continue only on a unique result or hand off. This preserves both privacy and the supplied disambiguation journey.
- Required provider lookup and booking plus no-match failure are the minimum demonstrated slice. All supplied safety policies remain applicable when failures occur. `multiple_patient_matches` is labeled required in the supplied scenarios, but invokes existing-appointment lookup, which the assignment calls optional. Per the explicit Q1 answer, its identity safeguard is required and tested within booking; completed existing-appointment retrieval remains optional.
- Source precedence follows the approved common contract: `assignment.md` establishes required versus optional scope, `policies.md` defines safety and observability rules, and `openapi/scheduling-api.yaml` defines the scheduling-service surface and returned facts. Scenarios, mock implementation and fixtures provide acceptance/reference evidence within that scope, rather than making optional capabilities mandatory.
- Basic observability is retained because the detailed policy calls for it, although the assignment lists logs/traces among good-to-haves. Structured/per-step tracing is optional. Extra recommended evaluation scenarios supply safety acceptance cases without accepting optional product capabilities.
- Existing generic brief/decisions and the bootstrap normalization qualification example are reference scaffolding, not replacement requirements for this scheduling assignment. The reusable-core boundary and exact confirmation intent remain applicable; no existing synthetic starter is claimed to satisfy the scheduling flow.

### Scope and dependencies

- Text interaction is required; a CLI is an allowed default for later planning. The approved Policy candidate includes a thin Marimo conversation and inspectable ZEN policy decisions. New scheduling backend, database, reschedule and cancellation remain outside scope.
- **Q1 resolved — 2026-10-08, explicit developer response (Option A)**: “Existing approved common contract establishes assignment.md/policies/OpenAPI source precedence and optional appointment lookup; retain duplicate-identity clarification within booking. No new mandatory retrieval scope.” This resolves the scenario/scope conflict without removing identity safety requirements or authorizing optional integrations.
- Automated handoff submission, existing-appointment lookup, a larger evaluation harness, advanced traces, production/design extension notes remain optional, unaccepted additions. Marimo and ZEN are accepted by the candidate launch and direct Operator correction. Basic diagnostic and mandatory behavior verification remain required independently of those additions.
- Required human-help behavior means truthful escalation guidance, not real staff availability or ticket delivery. If automated handoff is later selected, its confirmed queued outcome and reason must match the scheduling service, and failures cannot be presented as delivered handoffs. The recommended outage scenario's actual queued handoff depends on selecting this optional capability.
- The mock contract defines the implementation's later scheduling-call obligations: provider search, patient search, availability and confirmed appointment creation. Protocol details belong in Plan/contracts rather than user requirements. The supplied service's in-memory reset, fixed-offset fixture times and synthetic identities do not prove durable execution, concurrency safety or clinical readiness.
- The assignment expects AI/model use and offers a temporary model-service key; model reasoning may help interpret language but cannot invent service facts, resolve ambiguous identity by guessing or supply confirmation. No credential acquisition, authenticated model call or live integration is performed or authorized by this Specify stage. Offline fixtures must remain available; later implementation must report the difference between simulated and actual model behavior.
- Primary/patient and Support/Admin Persona selections remain visibly pending. No new catalog identity, validated research, permissions or admin console is inferred. Selection/validation is a follow-on, not a barrier to starting the required implementation.

### Effort, submission and truthful claims

- The assignment defines a three-hour code/README window from receipt and video due thirty minutes later. Receipt time, deadline baseline and compliance are not established by this stage; the developer/Operator owns those determinations and tradeoffs. No scope is silently removed because of elapsed time.
- A repository link and recorded video are requested submission deliverables, but Specify itself performs no remote work. The launch separately grants private Kenerator/ochsner-scheduling-policy milestone pushes; public submission and delivery remain Operator-owned.
- The requested README statement “I completed this within the assigned 3-hour window.” may be included only if verified true. Otherwise document actual timing and unfinished work honestly; this specification makes no time-window compliance claim.
- Useful interactive feedback targets the Constitution's 400 ms where feasible. Completion latency must be measured with scenario/environment/load before claims; no model completion deadline, capacity benchmark or production service level is invented.

## Approved candidate reconciliation — 2026-10-08

The original bootstrap input omitted the separately approved lane contract. This additive reconciliation restores that existing authority; it does not relax supplied policies or restart completed native stages.

- **FR-021**: Genuine model-backed multi-turn interpretation MUST support provider lookup and booking, ask for missing information, and validate extracted fields. Offline fixtures remain available for tests and disclosed rehearsals; they do not satisfy live-AI acceptance.
- **FR-022**: The Policy candidate MUST execute ZEN 2.1.2 decision tables in actual workflow behavior. Reviewers can inspect stable rule/reason/source IDs and normalized facts. Missing/malformed facts or engine failures stop the proposed action. The engine neither verifies identity nor creates consent nor performs effects. Deterministic transaction checks independently recheck exact current patient/slot binding before POST.
- **FR-023**: A thin Marimo 0.25.1 interface MUST provide the text conversation and privacy-safe policy inspection. It shares the CLI core and must not replay booking through reactive reruns. Approved sponsor assets/colors are used for this internal-only audience.
- **SC-008**: Live provider and booking conversations complete over multiple turns using the configured model; no unit double is presented as live evidence.
- **SC-009**: Real ZEN negative/missing/conflicting fact cases produce zero proposed adapter calls; a forged engine proceed cannot bypass deterministic booking checks. UI and CLI share the tested core.

Source: approved four-candidate launch (native Operator OptionA), common acceptance contract, and direct Operator instruction to retain selected scalable rule technology rather than omit it because rules are small. Existing appointment lookup/handoff submission remain optional; no new clinical/eligibility rules are accepted. Persona pins remain pending.
