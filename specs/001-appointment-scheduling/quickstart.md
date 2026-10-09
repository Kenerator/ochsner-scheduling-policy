# Planned validation quickstart

Date: 2026-10-08. This guide defines commands and outcomes for the implementation stage. `scheduling_assistant` does not exist yet; the current generic demos do not prove scheduling acceptance. Run commands from repository root. See [interfaces](contracts/interfaces.md) and [data model](data-model.md).

## Prerequisites and setup

Use Python 3.11+. Inspect `python3 --version`; substitute a verified compatible executable in every command if necessary. Current shell inspection returned 3.14.3, while prior project environment evidence records 3.11.13; verify the executable actually used. No global tooling changes, model key or network account is needed for offline verification.

```sh
python3 --version
python3 -m venv .venv
.venv/bin/python --version
```

If `.venv` already exists, verify and reuse it rather than recreating it. Required ZEN2.1.2 and Marimo0.25.1 are declared/pinned in project dependencies. Install the project and locked runtime dependencies before running; final exact commands are verified during integration. Use `.venv/bin/python` instead of `python3` in the following commands when selected. Check that candidate port 4012 is free; never terminate an unrelated process.

## Start and reset supplied scheduling service

```sh
python3 reference/mock-api/server.py --port 4012
```

Keep it in a separate terminal. Restart only that owned process to reset bookings. There is no HTTP reset endpoint. Tests use isolated server ports/state; demos must not race with each other. Conversation `reset` clears assistant state only. Reset does not prove an uncertain prior booking failed.

## Planned interactive assistant

```sh
PYTHONPATH=src python3 -m scheduling_assistant --api-base http://127.0.0.1:4012 --intent-mode offline
```

Expect explicit AI/offline-mode disclosure and a multi-turn prompt. Ask “Which primary care providers are downtown?”: expect actual service providers, no identity prompt and no appointment claim. Start booking and provide supplied synthetic identity (phone `555-0101`, DOB `1985-04-12`), specialty primary care and downtown. Choose a displayed returned slot, review exact details, then explicitly confirm. Expect exactly one matching service appointment and zero POSTs before confirmation. Repeated yes returns known completed details without another booking.

## Verification commands

Required existing baseline checks (currently runnable generic starter only):

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m poc_demo --scenario success
PYTHONPATH=src python3 -m poc_demo --scenario failure
```

Planned scheduling demos, each on fresh owned mock state:

```sh
PYTHONPATH=src python3 -m scheduling_assistant.demo --scenario provider_lookup --api-base http://127.0.0.1:4012
PYTHONPATH=src python3 -m scheduling_assistant.demo --scenario success --api-base http://127.0.0.1:4012
PYTHONPATH=src python3 -m scheduling_assistant.demo --scenario failure --api-base http://127.0.0.1:4012
```

## Required behavior matrix

| Scenario | Trigger / action | Expected evidence |
| --- | --- | --- |
| Provider lookup (US1) | primary care/downtown without identity | Matching providers from GET /providers, no patient calls |
| Booking (US2) | unique identity, offered slot, exact yes | Patient search and availability precede one POST; matching returned appointment |
| No match (US3) | phone 555-9999, DOB 1990-01-01 | No patient-specific work; focused correction then finite guidance; demonstrated end to end |
| Duplicate identity (US3) | phone 555-0130, DOB 1978-09-22; then user-provided ZIP | Candidate identities/ZIPs not shown; exactly one match enables booking; unresolved ZIP stops it; retrieval not required |
| Confirmation guards (US2) | refusal, ambiguous yes, unoffered slot, changed identity/slot, reused/cross-session proposal | Zero stale/unconfirmed POSTs; new exact proposal needs new confirmation |
| Conflict (US4) | selected returned slot_conflict_001 | 409 truthful failure; suppress rejected ID, remaining returned options or guidance; no alternate auto-booking |
| Empty availability (US4) | dermatology/lakeside | slots empty; changed search or human help, no invented slot |
| Outage (US4) | test/demo adapter sets X-Mock-Scenario: api_failure | 503 explanation and finite guidance; no claimed queued handoff |
| Medical advice / scope (US4) | supplied medical-advice example, human request or unsupported type | No advice/triage or fabricated contact; scheduling effects stop |
| Malformed/unknown effect (US4) | isolated transport fault after POST, malformed/mismatched success | Outcome unknown; further booking blocked pending reconciliation, no blind retry |
| Support/privacy/isolation (US5) | inspect success/failure/error diagnostics; new conversation | intent/state/calls/outcomes/reason/elapsedMs visible; sentinel sensitive fields absent; no inherited identity or assent |

Write meaningful failing tests before implementing these cases. Contract tests exercise real local supplied HTTP service; transport fault fixtures cover errors not reachable deterministically in the reference server. Do not modify the canonical service to force tests to pass.

## Clean-copy acceptance and walkthrough

After integration, validate from a clean checkout or explicitly labeled clean-copy equivalent with declared interpreter and only owned local mock state. Verify setup, assistant launch, provider lookup, booking, failure, restart/reset and all exact commands; record scenario/environment/load and elapsed times before performance claims. Run existing baseline and new scheduling checks together. Passing generic starter checks alone is insufficient.

Plan a maximum five-minute video: 0:00–0:30 purpose/mode/limitations; 0:30–1:15 provider lookup; 1:15–2:45 confirmed booking; 2:45–3:45 no-match and truthful help; 3:45–4:45 core/adapters and tradeoffs; 4:45–5:00 next steps. Link actual as-built docs after implementation. Live-model calls and exact private repository milestone pushes are approved. Public submission and recording delivery remain Operator-owned; a script is not a recorded/delivered video. Do not state three-hour compliance without an established Operator baseline and evidence.
