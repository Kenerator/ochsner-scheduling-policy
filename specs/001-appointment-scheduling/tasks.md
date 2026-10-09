---
description: "Executable implementation tasks for the AI Appointment Scheduling Assistant"
---

# Tasks: AI Appointment Scheduling Assistant

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [interfaces](contracts/interfaces.md), [quickstart.md](quickstart.md).
**Updated**: 2026-10-08. Generated Tasks only; implementation has not started.
**Organization**: Setup → shared foundation → US1–US5 in native priority order → integration and handoff. Python 3.11+, pinned ZEN 2.1.2 and Marimo 0.25.1, standard-library HTTP, flat unittest discovery, reusable core and thin CLI/HTTP/intent adapters.
**Tests**: Required by FR-017, plan and Constitution. Write meaningful tests first and observe the intended failures before implementing their behavior. Preserve existing generic tests/demos. Never modify supplied mock, fixtures, OpenAPI, managed assets, bootstrap controls or Constitution to satisfy tests.

## Format: `[ID] [P?] [Story] Description`

Every task has an unchecked box, sequential ID and exact project-relative file path. Story phases use [USn]. [P] means a disjoint-file lane eligible for parallel execution **after its listed prerequisites are satisfied**, not permission to bypass a tests-first dependency. Assign one owner per file; do not share mock process/state between lanes. No concurrent native stages on this feature.

## Path Conventions

Single package `src/scheduling_assistant/`; flat `tests/`; unchanged supplied `reference/mock-api/`, `reference/data/`, `reference/openapi/`. Supporting docs link native requirements/progress rather than duplicating ledgers. Use pending Primary/Patient and Support/Admin Persona mappings from spec; do not invent pins or permissions.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the declared runtime and package without replacing starter tooling.

- [x] T001 Verify a chosen Python 3.11+ interpreter and reuse or create project-local `.venv` as needed; document its explicit executable and declared-dependency/PYTHONPATH setup in specs/001-appointment-scheduling/quickstart.md without global tooling changes.
- [x] T002 Create the package skeleton in src/scheduling_assistant/__init__.py and src/scheduling_assistant/adapters/__init__.py; retain src/poc_demo/ and src/poc_template/ and existing pyproject.toml behavior.
- [x] T003 [P] Create tests/scheduling_test_support.py with disposable owned supplied-server processes on independent ports, readiness checks, reliable cleanup and fresh state; use reference/mock-api/server.py unchanged and never terminate unrelated processes (depends on T001).

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Stable validated contracts and transport/interpretation seams before any story. These prerequisites block story implementation.

- [x] T004 [P] Write failing validation/isolation tests in tests/test_scheduling_models.py covering every data-model entity, missing/type-invalid service fields, foreign conversation/proposal tokens and unchanged returned timestamps (depends on Phase 1).
- [x] T005 [P] Write failing offline intent boundary tests in tests/test_scheduling_intent.py for ordinary multi-turn text, invalid fields, minimized safe context, unsupported types and malicious structured responses attempting patientId, facts, confirmation or effects; use synthetic recorded responses only (depends on Phase 1).
- [x] T006 [P] Write failing common HTTP transport tests in tests/test_scheduling_http.py for encoded exact query strings, JSON, five-second timeout configuration, no automatic retry, categorized 400/409/503/read/POST errors, malformed responses and sanitized exceptions (depends on Phase 1).
- [x] T007 Define SchedulingPort, IntentPort, IntentResult, TurnResult and categorized errors in src/scheduling_assistant/ports.py matching specs/001-appointment-scheduling/contracts/interfaces.md; intent enum is `provider_lookup`, `book`, `human_help`, `medical_advice`, `unsupported`, `unknown`; interpreter cannot perform effects or establish confirmation (depends on failing T004–T006).
- [x] T008 Implement shared typed models and validators in src/scheduling_assistant/models.py to satisfy T004, quoting these data-model constraints: Conversation “In-memory per session. New conversation inherits no patient/proposal/result. No raw transcript persisted in diagnostics”; Patient match “Service facts only. Required usable ID and identifying fields validated. Private candidates never enumerated. Synthetic match is not authentication”; Search criteria “specialty in primary_care/dermatology; location in downtown/uptown/lakeside. Valid ISO dates and ordered bounds. Unsupported requested type goes to guidance; not silently discarded”; Provider “Returned provider only; no inferred availability. Enrich slot labels by joining providerId to returned providers; missing/inconsistent details cannot be invented”; Available slot “Only returned available=true slots matching criteria. Valid offset-bearing timestamp shown as returned. No fixture-only daysFromToday/time/conflictOnBooking in application model”; Booking proposal “Immutable exact pair. Must reference uniquely resolved patient and offered slot. Changed identity/criteria/slot clears proposal and assent”; Appointment “Only validated 201 response can establish scheduled success. Must agree with proposed patient and slot details (response has no slotId). Missing/inconsistent success after POST produces unknown effect” (depends on T007).
- [x] T009 [P] Implement the deterministic offline intent adapter in src/scheduling_assistant/adapters/intent.py to satisfy T005 through T007–T008: extract only user-supplied values, preserve uncertainty, minimize context, ignore/reject injected authority and leave explicit yes/no decisions to the core; offline-only here; required live adapter tests/implementation belong exclusively to T056.
- [x] T010 [P] Implement common JSON/HTTP transport and error categorization in src/scheduling_assistant/adapters/http.py to satisfy T006 through T007–T008: explicit local base URL, finite five-second timeout, no retries, no raw URLs/bodies in errors and distinguish rejected operations from indeterminate POST effects; story endpoint mappings follow below.
- [x] T011 Run foundational tests using the verified interpreter and record outcomes in specs/001-appointment-scheduling/quickstart.md; inspect models/ports against contracts and keep generic baseline behavior intact (depends on T008–T010).

**Checkpoint**: Stable models/ports, offline interpretation and common transport; no scheduling outcome claimed yet.

## Phase 3: User Story 1 — Find providers without identifying a patient (P1)

**Goal**: Service-grounded public provider lookup with retained search criteria and focused prompts.
**Independent test**: Ordinary-text downtown primary-care search returns matching actual service providers, with zero identity prompts/patient calls; missing criteria, empty results and unsupported criteria have truthful finite responses (SC-001).

### Tests first

- [x] T012 [P] [US1] Add failing GET /providers contract tests in tests/test_scheduling_http.py against an isolated supplied mock: optional specialty/location, essential field/types, exact returned facts and invalid/missing provider data (depends on T011).
- [x] T013 [P] [US1] Write failing provider conversation tests in tests/test_scheduling_core.py for ordinary-text lookup, focused clarification, retained answers, empty results, no patient identification, no invented providers and separate sessions (depends on T011).
- [x] T014 [P] [US1] Write failing public CLI tests in tests/test_scheduling_cli.py for AI/offline disclosure, one message per turn, provider rendering, --api-base, --intent-mode offline, quit and conversation reset (depends on T011).

### Implementation

- [x] T015 [US1] Implement providers(criteria) in src/scheduling_assistant/adapters/http.py using GET /providers and validated returned arrays only; satisfy T012 and reject unsupported criteria without silently broadening them.
- [x] T016 [US1] Implement Assistant.handle public lookup transitions and display-safe TurnResult in src/scheduling_assistant/core.py, retaining answers and separating provider facts from availability; satisfy T013 (depends on T015).
- [x] T017 [US1] Implement thin text CLI in src/scheduling_assistant/__main__.py with disclosed offline simulation, explicit port wiring, reset/quit and no workflow policy in shell code; satisfy T014 (depends on T016).
- [x] T018 [US1] Add isolated service-grounded provider acceptance in tests/test_scheduling_acceptance.py and run provider/core/CLI tests together, proving no patient calls and SC-001 (depends on T017; write new acceptance assertions before any fixes).

**Checkpoint**: Independently useful first increment, not the full assignment MVP.

## Phase 4: User Story 2 — Book the selected appointment with confirmation (P1)

**Goal**: Unique identity → returned availability → exact displayed proposal → explicit confirmation → one matching service appointment.
**Independent test**: Fresh mock, unique supplied identity over at least two turns, returned slot choice and explicit yes produce exactly one matching 201 booking; refusal, ambiguity, changed or foreign proposal and repeated confirmation never cause unauthorized/replayed POSTs (SC-002–003).

### Tests first

- [x] T019 [P] [US2] Add failing patient search, availability and booking contract tests in tests/test_scheduling_http.py: exact phone/dob query, patientId/specialty with optional location/startDate/endDate, confirmed:true JSON, usable 201 scheduled appointment and proposal consistency (depends on T018).
- [x] T020 [US2] Write failing deterministic policy tests in tests/test_scheduling_core.py for unique identity requirement, displayed offered selection, exact immutable patient/slot pair, explicit yes provenance, refused/ambiguous assent, identity/criteria/slot revision, foreign tokens and completed replay suppression (depends on T018).
- [x] T021 [P] [US2] Extend failing booking workflow tests in tests/test_scheduling_core.py for missing/invalid phone/DOB/specialty, retained answers, no trusted user/model patientId, available=true criteria-matching slots, provider joins and exact confirmation before any POST (depends on T018).

### Implementation

- [x] T022 [US2] Implement patient_matches, availability and book mappings in src/scheduling_assistant/adapters/http.py to satisfy T019; locally validate essential response fields and matching appointment patient/provider/specialty/location/time/status, never use fixture-only fields or nonexistent filters/endpoints.
- [x] T023 [P] [US2] Implement independent exact transaction proposal guards in src/scheduling_assistant/core.py; actual ZEN table/adapter belongs exclusively to T054 to satisfy T020 with concise boundary comments; bind conversation and identity revision, require current displayed proposal, clear stale assent and cache same-session completed result (depends on T020 and stable T008; disjoint from T022).
- [x] T024 [US2] Implement unique-match booking state transitions in src/scheduling_assistant/core.py to satisfy T021: collect identifiers/criteria, resolve service identity, retrieve available slots, join returned provider labels, select offered slot, display proposal, confirm once and validate returned success (depends on T022–T023).
- [x] T025 [US2] Extend src/scheduling_assistant/__main__.py rendering for exact appointment details, explicit yes/no, changed selections and known outcomes; first add failing CLI cases in tests/test_scheduling_cli.py and then implement (depends on T024).
- [x] T026 [US2] Add and run fresh-mock multi-turn booking acceptance in tests/test_scheduling_acceptance.py, asserting zero POSTs before confirmation, one matching booking after yes and no repeat POST, cross-session identity/assent isolation and changed-selection re-confirmation (depends on T025; tests before any corrective behavior).

**Checkpoint**: Happy-path booking with guards; identity/failure phases remain required before full handoff.

## Phase 5: User Story 3 — Resolve identity safely or stop (P1)

**Goal**: Focused correction or private zip clarification; unresolved identity stops patient-specific progress.
**Independent test**: No-match 555-9999/1990-01-01 ends in finite truthful guidance. Duplicate 555-0130/1978-09-22 prompts zip without listing candidates; only one private match enables booking. Unresolved zip and optional retrieval request disclose no details (SC-003–004).

### Tests first

- [x] T027 [P] [US3] Extend failing identity tests in tests/test_scheduling_core.py for zero/multiple matches, candidate/zip secrecy, no availability/booking before uniqueness, user-provided zip filtering locally, failed clarification and finite correction limits (depends on T026).
- [x] T028 [P] [US3] Add failing identity acceptance cases in tests/test_scheduling_acceptance.py using isolated no-match and duplicate supplied fixtures, unique zip then confirmed booking, unresolved zip stopping action and existing-appointment requests receiving scope guidance (depends on T026).

### Implementation

- [x] T029 [US3] Implement safe identity clarification and bounded correction/guidance in src/scheduling_assistant/core.py to satisfy T027–T028: zip filters private returned candidates, never enumerates them or guesses, and optional retrieval remains outside required scope.
- [x] T030 [US3] Add no-match and duplicate_identity deterministic demo scenarios in src/scheduling_assistant/demo.py, with fresh owned server state, public-safe output and zero claims of queued handoff; run T027–T028 and demonstrate both resolved and unresolved identity outcomes (depends on T029).

**Checkpoint**: Required identity failure demonstrated within booking; Q1 does not mandate retrieval.

## Phase 6: User Story 4 — Receive truthful failure and human-help guidance (P1)

**Goal**: Finite recovery, no fabricated success, advice, automatic alternate booking or uncertain-effect retry.
**Independent test**: Conflict, empty availability, validated outage, unsupported/human/medical requests and interrupted or mismatched booking responses yield their exact known/unknown outcome and useful next step (SC-004).

### Tests first

- [x] T031 [P] [US4] Add failing failure/uncertainty tests in tests/test_scheduling_http.py for validated 400/409/503 rejection, connection/timeout/500 and malformed/mismatched 201; use transport fixtures for indeterminate effects and assert no retry (depends on T030).
- [x] T032 [P] [US4] Add failing failure/recovery tests in tests/test_scheduling_core.py for permanent conflict suppression, remaining returned choices with fresh confirmation, empty slots, outage stop, unknown-effect booking freeze, medical advice/triage refusal, explicit human help and unsupported work (depends on T030).
- [x] T033 [P] [US4] Add failing fresh-service failure acceptance in tests/test_scheduling_acceptance.py using slot_conflict_001, dermatology/lakeside and isolated X-Mock-Scenario: api_failure, plus no-advice/scope cases and synthetic interrupted POST faults (depends on T030).

### Implementation

- [x] T034 [US4] Complete HTTP failure semantics in src/scheduling_assistant/adapters/http.py to satisfy T031: distinguish validated rejection from unknown POST effects, keep reads as read failures and never infer success from malformed/mismatched appointments.
- [x] T035 [US4] Implement guarded failure transitions in src/scheduling_assistant/core.py to satisfy T032–T033: suppress rejected slot for current search, require fresh choice/confirmation, provide finite human guidance, freeze unknown booking pending external reconciliation, and never claim staff contact or delivered ticket (depends on T034).
- [x] T036 [US4] First add unknown-effect reset-warning and failure rendering tests in tests/test_scheduling_cli.py, then update src/scheduling_assistant/__main__.py so conversation/mock reset cannot imply an uncertain booking failed (depends on T035).
- [x] T037 [US4] Extend src/scheduling_assistant/demo.py with conflict, no_availability, outage and medical_advice scenarios; run failure acceptance and demonstrate specific outcomes with independent fresh mock state (depends on T036).

**Checkpoint**: All P1 workflows and encountered safeguards pass; diagnostics/docs still required.

## Phase 7: User Story 5 — Understand outcomes and recover responsibly (P2)

**Goal**: Support/Admin can inspect sanitized intent/state/calls/outcomes/reason/timing and follow reproducible setup/recovery instructions; no admin console or delivered contact.
**Independent test**: Success/failure/unknown records distinguish attempted/completed effects with nonnegative elapsedMs; all diagnostic/stderr paths omit sensitive sentinel values. Clean-copy instructions repeat lookup, booking, failure and resets without hidden setup (SC-005–007).

### Tests first

- [x] T038 [P] [US5] Write failing privacy/diagnostic tests in tests/test_scheduling_diagnostics.py for allowlisted fields, intent/state transitions, operation/outcome/error/escalation and elapsedMs; seed phone/DOB/zip/names/patient/appointment IDs/secret sentinels through success, rejection, malformed response and stderr paths and assert absence (depends on T037).
- [x] T039 [P] [US5] Add failing recovery/privacy/isolation acceptance in tests/test_scheduling_acceptance.py for inspectable completed/failed/unknown effects, finite next steps, retained answers and no inherited identity/proposals; assert no contact delivery claims (depends on T037).

### Implementation and support documentation

- [x] T040 [US5] Implement allowlisted event construction in src/scheduling_assistant/diagnostics.py to satisfy T038 with the verbatim data-model constraint “Allowlist only. No patient IDs, raw queries/bodies/text, DOB, phone, zip, names or keys. Distinguish guidance from delivered handoff”; include opaque local token, intent/state, operation, category/outcome/reason and elapsedMs only.
- [x] T041 [US5] Integrate diagnostic sink and measured turn/operation timing in src/scheduling_assistant/core.py and sanitize adapter/CLI stderr in src/scheduling_assistant/adapters/http.py and src/scheduling_assistant/__main__.py; preserve visible unexpected programming errors without raw sensitive inputs; satisfy T038–T039 (depends on T040).
- [x] T042 [US5] Complete provider_lookup/success/failure demo entry points in src/scheduling_assistant/demo.py with interpreter/scenario/offline-mode labels, diagnostic summaries and fresh-state discipline; run all required success/failure/privacy acceptance (depends on T041).
- [x] T043 [US5] Update README.md and specs/001-appointment-scheduling/quickstart.md with verified interpreter/setup, mock startup, assistant launch, all exact tests/demo commands, conversation versus server reset, uncertainty reconciliation, finite support guidance, limitations and a short working document index (depends on T042; final clean-copy evidence follows).

**Checkpoint**: Diagnostic behavior and documented support path exist; as-built/clean-copy integration closes the handoff.

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Verify combined behavior and populate actual documentation after code stabilizes; stubs never block starting implementation.

- [x] T044 Run `PYTHONPATH=src python3 -m unittest discover -s tests -v`, `PYTHONPATH=src python3 -m poc_demo --scenario success` and `PYTHONPATH=src python3 -m poc_demo --scenario failure` with the verified compatible executable; then run all scheduling scenarios on independent fresh owned mock state and record failures or evidence in specs/001-appointment-scheduling/quickstart.md (depends on T043,T055–T057,T060; substitute verified executable explicitly if python3 is unsuitable).
- [x] T045 Validate documented setup/launch/provider/booking/no-match/reset commands from a clean checkout or labeled clean-copy equivalent without relying on undeclared files; record interpreter/environment/scenario/load and turn/API elapsed measurements in specs/001-appointment-scheduling/quickstart.md, including unmet 400 ms feedback targets without readiness/window claims (depends on T044,T058).
- [x] T046 [P] Populate docs/internal/as-built/code-walkthrough.md from stable actual files/symbols and relevant tests, including policy/adapter boundaries, identity/proposal guards, recovery and modification exercise; stamp update date and reviewed source revision, identifying working-tree additions when not committed (depends on T045).
- [x] T047 [P] Populate docs/internal/as-built/architecture.md from stable actual code/tests with core/CLI/intent/HTTP/mock boundaries, state/effect/diagnostic flows, synthetic/offline limitations and accurate diagrams; stamp update date and reviewed source revision with working-tree caveat if needed (depends on T045; owner distinct from T046).
- [x] T048 Verify README.md navigation and docs/internal/as-built/code-walkthrough.md and docs/internal/as-built/architecture.md links, symbols and rendered diagrams against integrated code/tests; correct only project documentation and rerun affected checks if behavior changed (depends on T046–T047).
- [x] T049 [P] Update docs/internal/video-notes.md with an at-most-five-minute tested lookup/booking/no-match walkthrough, actual architecture/tradeoffs, pending Persona pins, offline/live distinction and recording/delivery status; no invented recording or three-hour compliance statement (depends on T048).
- [x] T050 [P] Reconcile docs/product/decisions.md, docs/product/user-stories.md, docs/product/backlog.md, docs/product/roadmap.md, docs/product/sprint-planning.md and docs/product/next-steps.md as short canonical links/priorities/increments: retain Q1, all required scope and unresolved Primary/Patient and Support/Admin pins; report actual live AI evidence and any unfinished qualification; carry deadline baseline, recording and external delivery without duplicate completion ledgers (depends on T048; disjoint from T049).
- [x] T051 Consider/reuse one optional independent adversarial review using docs/internal/reviews/adversarial-review.md, recording sanitized findings and source revision or honest deferral in docs/product/next-steps.md; do not add a new MVP gate or extra proof cycle (depends on T049–T050; consideration is required, review execution optional).
- [x] T052 Consider meaningful immutable annotated checkpoint tags under docs/internal/milestones.md and optional post-MVP UI/UX refinement; record selected/deferred status in docs/product/next-steps.md. If refinement is separately selected, retain pre/post tags and verify affected behavior; it cannot block the slice and grants no push permission (depends on T051).
- [x] T053 Review combined diff, required behavior and supporting navigation; update checked tasks only for verified work in specs/001-appointment-scheduling/tasks.md and leave incomplete work explicit in docs/product/next-steps.md. Before any authorized local commit run the whole staged credential guard documented in docs/internal/security.md, preserve hooks and surface findings/incomplete scans without printing suspected values. No automatic commit, tag, push, publication or deployment is required by this task (depends on T052,T059).

## Dependencies & Execution Order

### Phase dependencies

Setup → Foundation → US1 → US2 → US3 → US4 → US5 → Integration/clean-copy → parallel as-built → navigation → parallel supporting docs → optional-review/milestone consideration → handoff.

Story priorities are P1 for US1–4, P2 for US5. They are independently **testable**, not all independently implementable: US2 reuses US1 core/HTTP/CLI; US3 builds identity transitions in US2; US4 integrates those workflows; US5 instruments stable outcomes. Shared files have sequential owners. This deliberate dependency chain avoids competing writers and unsafe partial behavior.

### Within each story

All listed test tasks must first fail for intended missing behavior; then implement models/adapter or policy, core, CLI, integration in dependency order. New assertions in integration/doc tasks also precede corrective implementation. Run all affected checks before checking a task. The foundation checkpoint and each story checkpoint are verification points, not external authorization requests.

### Parallel opportunities and ownership

- After T001, T003 can run alongside package setup T002, with no shared files. Foundation failing tests T004/T005/T006 are three disjoint lanes; contracts/models are sequential; after models and respective failing tests, T009/T010 are disjoint adapters.
- Story test lanes: T012/T013/T014; T019 plus sequential root-owned T020→T021; T027/T028; T031/T032/T033; T038/T039. Each needs its phase-entry prerequisite; each server lane owns a separate process/port/state.
- T022 HTTP and T023 policy can proceed together once their tests fail and models are stable; core integration T024 waits for both.
- Stable-source documentation T046/T047 and later T049/T050 have distinct owners; do not parallelize T050 with any other next-steps writer. Integration/navigation waits for both outputs.
- Native Tasks markers describe practical parallel execution during Implement. This Tasks stage has one authoritative tasks.md writer; no concurrent stage or implementation is run here. If client capacity or ownership makes a lane unsafe, execute sequentially and briefly record why; no new orchestration service.

## Parallel Examples by User Story

| Story | Eligible parallel tasks | Integration barrier |
| --- | --- | --- |
| US1 | T012 HTTP tests; T013 core tests; T014 CLI tests, separate files/server state | All tests fail first; T015 → T016 → T017 → T018 |
| US2 | T019 HTTP tests; T020 policy tests; T021 core tests; later T022 HTTP and T023 policy | T024 waits for both implementations; T025 → T026 |
| US3 | T027 core tests; T028 isolated acceptance tests | T029 waits for both; T030 demonstrates outcomes |
| US4 | T031 HTTP tests; T032 core tests; T033 isolated acceptance tests | T034 → T035 → T036 → T037 |
| US5 | T038 diagnostics tests; T039 acceptance tests | T040 → T041 → T042 → T043; as-built T046/T047 only after integration |

## Implementation Strategy

### MVP first

US1 is the smallest independently useful increment. The **required assignment slice** includes provider lookup, multi-turn confirmed booking, no-match demonstration and duplicate identity/failure safeguards (US1–4), plus US5 diagnostics and required documentation. Do not declare the assignment complete after US1 alone or silently remove safety requirements. Validate each local increment against synthetic supplied service facts.

### Incremental delivery

Complete each phase and verify its independent test criterion, preserving earlier behavior. Combine local integration and clean-copy evidence before the handoff. Tests use disposable server instances; demos restart only owned processes. No credentials, external model calls, publication, deployment or delivery follow automatically from local progress.

### External and optional follow-ons

Live model behavior is required and qualified in actual application flows; offline parsing remains a disclosed rehearsal option. See quickstart for live CLI/UI and cross-platform evidence. Persona selection, receipt/deadline baseline, recorded video and repository submission remain explicit follow-ons. Optional appointment retrieval, queued handoff, larger harness and advanced tracing are unaccepted scope; Marimo is required in this candidate; their absence must not be confused with failed required identity or basic diagnostic coverage. Post-MVP refinement and adversarial review were considered in T051–T052 without becoming implementation gates.

## Notes

Task generation does not prove tests pass or behavior exists. Supporting references retain their original planning/status text; tasks.md now owns implementation progress. Existing baseline and intake are preserved. Timing/effort compliance belongs to the Operator; report measurements and unfinished work honestly without shrinking scope or inventing a receipt baseline.

## Approved candidate delta (supersedes conflicting follow-on wording above)

Native stages completed before this reconciliation; native run remains historical completion, not mutated to claim new work. FR021–023 are required. Foundational disjoint files may execute in parallel after shared ports/models contracts and their failing tests are established. Each owner writes meaningful failing tests before behavior; root alone updates this task file.

- [x] T054 [P] Add real ZEN tests for every supplied rule, priority, missing/malformed/unknown facts, engine failure and changed context, then implement table/adapter/source registry with stable IDs and no Python fallback (FR022; depends onT007; policy owner only).
- [x] T055 Integrate actual ZEN before proposed core actions; test denied engine yields zero adapter calls and forged proceed cannot bypass independent transaction guards (FR022; depends onT024,T054).
- [x] T056 [P] Add live model schema/HTTP-error/privacy tests with controlled transport first; then implement required configurable Responses extractor without raw logs (FR021; depends onT007; model adapter owner only). End-to-end live qualification is T060.
- [x] T057 [P] Add thin Marimo per-client callback/UI adapter tests first; implement branded app.py conversation and policy inspector, verify browser core/confirmation/failure behavior and rerun safety (FR023; depends onT024,T035,T041,T054,T056; UI owner after stable core).
- [x] T058 Pin required dependencies/package resources; qualify exact private GitHub fresh-clone instructions on MacARM and Minty using declared deps and actual core/failure flows; report exact limits (depends onT044,T060; no as-built prerequisite).
- [x] T059 Update planned/as-built/video/README/stories/index with actual engine role, source IDs, liveAI evidence, scale path/limits and reviewed revision; integrate one final independent review then delta-only fixes (depends onT058,T048–T052; final review once).

Planning corrections also preserve required supplied mock isolation, current consent, 201-only booked, unknown-write reconciliation, private ZIP and no medical advice. Optional appointment lookup/handoff and UI refinement never replace mandatory work.

- [x] T060 Qualify actual live-model multi-turn provider/booking/no-match conversations and UI/CLI integration using isolated supplied mock state; output only sanitized status/evidence, never raw transcript/prompt/key (depends onT055–T057).

Execution order correction after Analyze: T001–T008 shared contracts/tests first; then disjoint one intent owner executes T005/T009→T056 sequentially in its shared files; disjoint HTTP and ZEN owners execute their tests→implementation in parallel. Root owns core tests→transaction/core integration, waiting for each needed adapter. Mandatory T055–T057 and T060 precede combined T044; T058 clean private clones precedes T045 and near-final T046–T052. T059 final review/document integration precedes T053 final handoff. Old per-story shared-file chains remain within each owner, but do not serialize disjoint adapter foundation work behind completed CLI stories. No native stage runs concurrently with Implement.

Ownership clarification: root sequentially owns T020 then T021 in tests/test_scheduling_core.py. One intent owner owns both T009 and T056, executing them sequentially; they never compete as independent writers. HTTP and ZEN files are disjoint. Analyze critical/high findings are resolved by these changes.

## Analyze remediation audit

Operator instruction (2026-10-08): fix every Analyze finding, regardless of severity. C1 tests-first live sequence, D1 single ZEN implementation owner, I1 mandatory qualification ordering, U1 bounded facts/source/output contracts, and delta shared-file ownership findings are corrected above. I2 active dependency/scope wording was reconciled across spec/plan/research/contracts/quickstart/tasks and inspected at every original location. All original findings and delta ownership findings are corrected; no severity cutoff was used. Qualification evidence is recorded independently of Analyze remediation. Analyze remains read-only; these are Implement corrections, not Converge.

## Completion handoff — 2026-10-09

Reviewed source49c5ad5/poc/mvp: all60tasks verified for required implementation/documentation slice;109tests and8scheduling+2generic demos pass on freshprivateMacARM/Linuxclones; actualliveCLI/UIprovider,booking,no-match verified; allAnalyze findings and4finalreviewfindings fixed. As-built/navigation/diagram checks complete. Recordedvideo itself is a separateblockedfollow-on (no recorder exposed); no finishedvideo/publicdelivery/enterprise readiness is claimed. Operator timedcheckpoints remain centrally dispatched, with actualfuturecapture timestamps required.


## User-selected visual repair — 2026-10-09

- [x] T061 Reproduce clipped approved SVG, add failing coordinate-preservation regression, then repair render-time scaling and compact responsive spacing without changing dependencies or source asset geometry (depends on T057).
- [x] T062 Verify desktop/narrow browser layouts and keyboard-accessible table overflow; run UI/full tests, Marimo check and success/failure demos; record delta review and handoff (depends on T061).

Validation: 13 UI tests and 110 full tests pass; Marimo check is clean; generic success/failure demos pass. Independent source/test delta review found no material issues. Browser evidence and scope are recorded in quickstart.


## Recording-off rehearsal correction

- [x] T063 Reproduce model-missed changed selection retaining pending proposal; write failing core/UI boundary tests, revoke before interpretation/rejection, supply selection-needed context and qualify live changed choice with separate consent.
- [x] T064 Exercise actual app controls and required flows with recording off on corrected candidate; resolve discovered defects, rerun full tests/demos, record source-bound coverage in existing video notes, restore owned synthetic starting state.

T063–T064: 114tests pass, all8scenario demos and generic success/failure pass, Marimo check clean. Independent delta review findings fixed. RC-1 remains immutable historical baseline; corrected candidate receives RC-2.
