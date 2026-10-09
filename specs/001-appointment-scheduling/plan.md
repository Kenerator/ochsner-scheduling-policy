# Implementation Plan: AI Appointment Scheduling Assistant

**Branch**: local Git `main`; native feature identifier `001-appointment-scheduling` | **Date**: 2026-10-08 | **Spec**: [spec.md](spec.md)

**Input**: `specs/001-appointment-scheduling/spec.md`. Native setup completed; no Git extension or new branch requested. Plan ends after Phase 1; implementation and Tasks have not started.

## Summary

Build a policy-first, multi-turn text assistant for provider lookup and confirmed synthetic appointment booking. A reusable Python core owns identity resolution, service-grounded options, exact confirmation, safe failures and sanitized diagnostics. Thin CLI, scheduling HTTP and intent adapters isolate effects. Duplicate-match clarification stays within booking per Q1; existing appointment lookup and automated handoff submission remain optional, unaccepted scope. Required failure guidance describes a next step without claiming staff contact.

The adopted supplied mock is the scheduling source of truth. Offline intent fixtures support repeatable verification; they do not establish the assignment's live AI outcome. The authorized live model adapter classifies requests without acquiring action authority; required live multi-turn evidence is separate from offline tests. See [research](research.md), [data model](data-model.md), [interfaces](contracts/interfaces.md) and [validation guide](quickstart.md).

## Technical Context

**Language/Version**: Python 3.11+, as declared by existing pyproject.toml; inspected shell Python is 3.14.3. Validate the chosen project interpreter before any launch.

**Primary Dependencies**: `zen-engine==2.1.2`, `marimo==0.25.1`; standard library HTTP/JSON/unittest, unchanged supplied mock. OpenAI Responses structured extraction via HTTPS, explicit configurable `gpt-5.4-mini` default (small capability check HTTP200). Reviewer uses ordinary OPENAI_API_KEY; no Bitwarden runtime dependency. Pin the full installed dependency set for clean MacARM/Linux qualification.

**Storage**: Private per-conversation in-memory state; mock-owned synthetic scheduling state backed by supplied JSON fixtures. No database, durable sessions or distributed duplicate guarantees.

**Testing**: unittest behavior tests before implementation; isolated supplied mock integration, contract validation, offline intent fixtures and negative diagnostic assertions. Keep existing generic tests and success/failure demos intact.

**Target Platform**: Local macOS/Linux terminal, mock at http://127.0.0.1:4012; independent test ports and server state.

**Project Type**: Reusable library with thin CLI, demo and HTTP/intent adapters. Required thin Marimo conversation/policy inspector on loopback28182; CLI fallback shares the core.

**Performance Goals**: Useful local feedback near 400 ms where feasible; synchronous scheduling request timeout initially five seconds, no automatic retry. Report actual turn/API elapsed times with interpreter, environment, scenario and load. No measured throughput or model SLA claim.

**Constraints**: Synthetic data only; disclose AI/simulated mode; no medical advice, guessed identity or invented service facts; explicit confirmation for exact proposal; uncertainty stops retry. No credentials, external publication, deployment, Constitution or managed asset changes in this stage.

**Scale/Scope**: One sequential local conversation per CLI; independent sessions do not share identity or confirmations. Supplied data has five patients, three providers, four slots and two pre-existing appointments. No production concurrency claim.

## Constitution Check

Gate evaluated before research and re-evaluated after design. PASS means planned compliance, not implemented acceptance.

| Principle | Pre-research gate | Post-design evidence |
| --- | --- | --- |
| I Empathy | PASS: spec US1–5 includes primary/patient and Support/Admin coverage, explicitly unresolved persona pins | Finite prompts, retained answers, sanitized support context; selection remains a linked follow-on |
| II Predictable interaction | PASS: exact confirmation and truthful recovery are mandatory | Proposal revision guard; refusal/change/replay/unknown effects defined in data-model and interfaces |
| III Honest responsiveness | PASS: targets distinguished from results | Timeout and elapsed-time diagnostics planned; no benchmark claim |
| IV Small core | PASS: core plus thin effect adapters, no replacement backend | Independent intent and scheduling ports; CLI references same core |
| V Verification | PASS: tests-first and supplied synthetic integration | quickstart lists success, negative, boundary, recovery and clean-copy validation |
| VI Safety | PASS: local synthetic scope and external grants separated | Private identity state, allowlisted diagnostics, live AI explicitly pending |
| VII Demonstration/docs | PASS: required setup, failure, reset and walkthrough planned | Near-final as-built population after code integration; reviewed revision/navigation/diagram verification required |
| VIII Lightweight governance | PASS: native spec/plan/tasks authority and safe parallel ownership | Research dispatched read-only; Tasks lanes depend on tests/stable contracts; no deadline compliance claim |

No unjustified Constitution violation was found. No Constitution amendment or gate waiver is proposed.

## Project Structure

### Documentation (this feature)

```text
specs/001-appointment-scheduling/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/interfaces.md
```

`tasks.md` is the next native stage's output, not created by Plan.

### Source Code (repository root)

Proposed additions below; existing generic tooling stays available.

```text
src/scheduling_assistant/
├── __init__.py
├── __main__.py             # text CLI only
├── models.py               # typed facts, conversation and proposal
├── core.py                 # guarded workflow transitions
├── ports.py                # intent and scheduling boundaries
├── policy.py               # deterministic action/confirmation guards
├── diagnostics.py          # allowlisted event construction
├── demo.py                 # repeatable scheduling scenarios
└── adapters/
    ├── http.py             # supplied scheduling contract transport
    └── intent.py           # offline fixtures plus live structured model boundary
reference/mock-api/         # existing unchanged supplied server
reference/data/             # existing synthetic server fixtures
reference/openapi/          # existing canonical service surface
policies/                   # existing human-readable policy home
tests/                      # planned scheduling behavior tests
```

Planned test files: `tests/test_scheduling_core.py`, `tests/test_scheduling_policy.py`, `tests/test_scheduling_http.py`, `tests/test_scheduling_intent.py`, `tests/test_scheduling_diagnostics.py`, `tests/test_scheduling_acceptance.py`. Flat discovery keeps the required unittest command effective. `src/poc_demo/` and `src/poc_template/` are existing scaffold examples/tools, not implemented appointment behavior.

**Structure Decision**: One package with standard-library ports/adapters. Policy guards are deterministic code with concise intent comments and a linked decision table; actual ZEN decisions gate workflow actions; transaction invariants remain independently checked in core. Keep supplied server/data/OpenAPI unchanged. Thin required Marimo UI reuses the same core.

## Implementation sequencing for Tasks

1. Define model/port contracts and meaningful failing guard/state tests before new behavior. Core policy, transport and offline intent/diagnostics work can have disjoint owners once their prerequisite contracts/tests exist; use native [P] tasks and explicit dependencies.
2. Integrate provider lookup (US1), identified and confirmed booking (US2), no/duplicate-match handling (US3), encountered failure guards (US4) and diagnostic/recovery coverage (US5). Do not run different native stages concurrently or share mock state among independent lanes.
3. Run combined tests, generic demos and scheduling provider/booking/failure demos on clean state; verify clean-copy setup, reset, isolation and measured timings. Live model behavior is authorized and required evidence, not replaced by offline success.
4. Near-final tasks must populate `docs/internal/as-built/code-walkthrough.md` and `architecture.md` from actual code/tests, after their implemented components stabilize. Independent sections may be drafted in parallel with clear ownership; integrate before navigation/diagram verification. Record update date and reviewed source revision before completion handoff. Stubs do not block implementation.
5. Update README's short index, setup/recovery/demo/video notes, honest next steps and relevant policy boundaries. Consider one optional independent adversarial review and meaningful annotated checkpoint tags using the documented procedures; no new mandatory review gate. Check the staged credential guard before any separately authorized commit. Optional UI refinement must not block the slice.

## Complexity Tracking

No Constitution violations requiring justification. Unfinished external model validation, Persona selection, video recording, remote setup/publication and deadline-baseline determination are recorded follow-ons, not completed deliverables.

## Reconciled candidate implementation contracts

PolicyEngine.evaluate(facts: dict) returns immutable Decision(disposition, reason, rule, sources). Facts contain only action/request/criteria/identity/slots/selection/proposal/consent/api/model enums; no identity values or raw text. Authoritative versioned ZEN JSON lives in package resources, indexed from policies/tables/README.md. First-hit rows cite supplied source sections; final catchall stops. No dynamic user loaders/callbacks or Python rule fallback. Engine failure fails closed.

Core calls ZEN before provider/identity/availability/proposal/booking actions; policy trace is display-safe. Immediately before booking, independently check verified patient, current API option membership, immutable current patient/slot/context proposal, literal explicit current user assent, and no completed/unknown effect. Only valid matching201 establishes booked.

Model extraction returns IntentResult(intent, fields) only. Fields allowed: phone,dob,zip,specialty,location,startDate,endDate,selection. Reject unknown keys including patientId,slotId,confirmed. Safe model context includes intent, state and required field names; never private candidates. Deterministic code owns yes/no and validates context changes before accepting assent.

Marimo notebook app.py uses a per-client core/conversation and callback-only submission, with replay-safe transaction core. No transcript persisted. Policy inspection uses normalized trace and committed table/source registry.

Scale path: independently version/review/regression-test policy artifacts, preserve bounded facts contract, and replace identity/session/effect infrastructure separately for real deployment. This PoC has no production authentication, durable idempotency, load/scaling proof or clinical readiness claim.
