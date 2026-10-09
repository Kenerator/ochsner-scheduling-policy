# Implementation validation quickstart

Updated during implementation reconciliation, 2026-10-08. The scheduling package, CLI and demo entry points now exist; integration, dependency setup and final qualification remain ongoing in [tasks](tasks.md). Commands below describe the current interfaces and expected outcomes, not a claim that every setup/platform/live scenario has been qualified. Generic starter demos do not prove scheduling acceptance. Run commands from repository root. See [interfaces](contracts/interfaces.md) and [data model](data-model.md).

## Prerequisites and setup

Use Python 3.11+. Inspect `python3 --version`; substitute a verified compatible executable in every command if necessary. The candidate `.venv/bin/python` used for implementation tests was verified as 3.11.13; earlier shell inspection returned 3.14.3. Verify the executable actually used. No global tooling changes, model key or network account is needed for offline verification.

```sh
python3 --version
python3 -m venv .venv
.venv/bin/python --version
```

If `.venv` already exists, verify and reuse it rather than recreating it. Required runtime selections are `zen-engine==2.1.2` and `marimo==0.25.1`. Follow the integration-owned [README setup](../../README.md) for project/dependency installation; dependency declaration and exact fresh-copy installation qualification must be completed and evidenced during integration. An existing prepared environment is not proof of reproducible setup or a lock file. The runtime commands below use the verified candidate `.venv/bin/python`; substitute another explicitly verified Python 3.11+ environment only when needed. Check that candidate port 4012 is free; never terminate an unrelated process.

## Start and reset supplied scheduling service

```sh
.venv/bin/python reference/mock-api/server.py --port 4012
```

Keep it in a separate terminal. Restart only that owned process to reset bookings. There is no HTTP reset endpoint. Tests use isolated server ports/state; demos must not race with each other. Conversation `reset` clears assistant state only. Reset does not prove an uncertain prior booking failed.

## Interactive assistant

```sh
PYTHONPATH=src .venv/bin/python -m scheduling_assistant --api-base http://127.0.0.1:4012 --intent-mode offline
```

Expect explicit AI/offline-mode disclosure and a multi-turn prompt. Ask “Which primary care providers are downtown?”: expect actual service providers, no identity prompt and no appointment claim. Start booking and provide supplied synthetic identity (phone `555-0101`, DOB `1985-04-12`), specialty primary care and downtown. Choose a displayed returned slot, review exact details, then explicitly confirm. Expect exactly one matching service appointment and zero POSTs before confirmation. Repeated yes returns known completed details without another booking.

Required live mode is the application default: omit `--intent-mode offline` after supplying `OPENAI_API_KEY` through the environment. Never put the key in source, command arguments or output. Live provider and booking conversations need genuine multi-turn evidence; the offline flow above is a disclosed rehearsal. The required Marimo UI shares this core; its integration-owned launch/configuration steps are in the [README](../../README.md).

## Verification commands

Required combined test suite and retained generic baseline demonstrations:

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python -m poc_demo --scenario success
PYTHONPATH=src .venv/bin/python -m poc_demo --scenario failure
```

Scheduling demos each own a fresh disposable supplied mock on an ephemeral port; they do not need the manually started port-4012 service:

```sh
PYTHONPATH=src .venv/bin/python -m scheduling_assistant.demo --scenario provider_lookup
PYTHONPATH=src .venv/bin/python -m scheduling_assistant.demo --scenario success
PYTHONPATH=src .venv/bin/python -m scheduling_assistant.demo --scenario failure
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

## Current integration evidence — 2026-10-09

MacARM Python3.11.13: 103 unittest tests passed after integration, including actual ZEN+suppliedHTTP acceptance and UI callback tests. Editable installation and pip check pass after pinning setuptools84.0.0/wheel0.48.0. requirements.lock pins the complete selected runtime set.

Authorized actual Responses model (`gpt-5.4-mini`) + actual ZEN + disposable suppliedHTTP service: provider_lookup returned providers, zero booking POST,1897.06ms whole scenario; success gathered missing identity over turns, displayed options/proposal then explicit yes, booked with exactly onePOST,5027.46ms; failure no_match,zeroPOST,3452.06ms. One sequential synthetic conversation per run; measured whole scenario, not per-turn throughput or production SLA. Raw prompts/transcripts/key were not emitted or saved. Live completion exceeds400ms; no claim of meeting that target.

Controlled IAB and fresh private-clone Mac/Linux qualification remain in progress. Recorded video is not delivered.

## Fresh private GitHub clone qualification

Commit046287d3f121eac522659c564c76a8b75ed665bb qualified on MacARM/Python3.11.13 and Minty Linuxx86_64/Python3.12.3. Both used new remote clones and project virtual environments, installed all28 locked package versions plus editable project, passed pip check and103tests, both generic demos and all8 scheduling demos. No source/venv copy, global/trust change or model credential was used. MacSSH22 timed out; the successful clone used per-command SSH443 with existing GitHub host trust. These host-specific paths/auth details are operational evidence, not reviewer prerequisites. Current core provenance/name-display deltas need targeted refresh on these exact clones before final handoff.
