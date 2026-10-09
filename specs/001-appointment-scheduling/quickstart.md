# Implementation validation quickstart

Updated2026-10-09. The implemented scheduling package, CLI, Marimo and demos are qualified as recorded below; [tasks](tasks.md) owns completion. Commands describe the current tested interfaces and supported platforms. Generic starter demos do not prove scheduling acceptance. Run commands from repository root. See [interfaces](contracts/interfaces.md) and [data model](data-model.md).

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

Historical receipt at initial integration: IAB/clean-clone checks were pending then; subsequent receipts below supersede that status. Recorded video remains undelivered.

## Fresh private GitHub clone qualification

Commit046287d3f121eac522659c564c76a8b75ed665bb qualified on MacARM/Python3.11.13 and Minty Linuxx86_64/Python3.12.3. Both used new remote clones and project virtual environments, installed all28 locked package versions plus editable project, passed pip check and103tests, both generic demos and all8 scheduling demos. No source/venv copy, global/trust change or model credential was used. MacSSH22 timed out; the successful clone used per-command SSH443 with existing GitHub host trust. These host-specific paths/auth details are operational evidence, not reviewer prerequisites. The final reviewed-source refresh below qualifies these deltas on the same independently cloned environments.

Final reviewed-source refresh:49c5ad5706988be77770f646f202637d7f7acf43. MacARM/Python3.11.13 passed109tests in16.552s; Linux/Python3.12.3 passed109tests in17.460s. Both retained fresh private clones fast-forwarded from the install-qualified source, preserved all28 locked versions, passed pip check and all8scheduling+2generic demos. Root current combined109tests also passed16.397s. Independent targeted review verified allfourfixes with37tests; no introduced defect found.

Final-source live CLI qualification49c5ad5: provider_lookup exited0,correctresult,0POST,1455.18ms; multi-turnsuccess exited0,correctbooked,1POST,4968.91ms; no-match exited0,correctguidance,0POST,3282.15ms. Each owned a fresh suppliedservice. Only sanitized summaries were emitted; captured transient text/key stayed in process memory.

## Controlled in-app browser receipt

Reviewed source49c5ad5, livegpt-5.4-mini, UIloopback28182/API4012,2026-10-09 America/Chicago. Public lookup visibly returned supplied providers without identity. Multi-turn booking gathered missing identity, offered actual slots with returned provider names, displayed exact proposal, then accepted a separate literalyes. Supplied service logged actualPOST201; UI displayed the matching booked result. Final-source repeat logged201 at00:31:58CDT. Inspector visibly showed action=book,identity=verified,proposal=current,consent=current_explicit and stableR-BOOK/sourceIDs. Reset preserved serverbookings; subsequent no-match logged onlyGETsearch at00:33:40 and displayed finite guidance plusR-REPORT-NO-MATCH. No queuedhandoff was claimed. Offline browser booking/no-match, keyboard submission and client isolation also passed earlier; early readonlyChrome smoke occurred beforeIAB-onlydirection and its tabs were closed. Finalqualification used controlledIAB.

Both as-built Mermaid diagrams rendered in controlledIAB through a temporary loopback page;104localnavigation links checked with zero missing targets at final integration. No WCAG conformance, throughput, enterprise readiness or recordedvideo claim follows from these checks. Actualvideo remains blocked on Operator/Media nativecapture; no supported recorder is exposed in thisagent session.


### Visual repair qualification — 2026-10-09

Delta from source 7cbbd7a: approved logo clipping reproduced in IAB; missing SVG viewBox corrected only in the rendered wrapper. Header/response spacing reduced, title responsive, and policy table placed in a labeled keyboard-focusable horizontal scroll region. Approved dependencies and source asset unchanged. Actual IAB checked at default 832px and narrow 390px: full logo visible and document width equals viewport width. Full suite: 110 tests in 16.450s, UI subset: 13 tests, Marimo check clean; generic success/failure demos passed. Independent source/test delta review found no material issues. Earlier private-clone/core evidence remains tied to its recorded revision and was not repeated for this presentation-only change.


### RC-2 pre-capture qualification — 2026-10-09T01:23:07.955665-05:00

Recording-off actual IAB rehearsal found and repaired proposal retention when live extraction missed a changed choice. Any intervening non-consent message revokes pending proposal before model interpretation; rejected oversized input also revokes it. UI delegates rejection to locked shared core. Selection context/prompt remains genuine-model-backed, with no authority or Python fallback. Actual final live1→2→yes confirmed option2; provider, missing/duplicate identity, refusal, conflict409, empty availability, no match, medical/human guidance and actual service outage reverified. See existing video notes for control coverage/source hashes and pristine reset. Full114tests16.585s, all8demos plus generic2, Marimo check and independent delta review pass. Historical clean-clone evidence remains tied to earlier revision; new core delta was tested locally, not represented as a fresh-clone rerun.


### Persona impact qualification — 2026-10-09T01:37:54.349413-05:00

Local Recoverycontext pure snapshot exposes allowlisted field names and categorical patient/booking state. Booking effect becomes unknown beforePOST, known rejected on validated service rejection, confirmed only after validated actual201; support always Not sent. Meaningful tests preceded code.116tests16.615s, demos8+2, Marimo check and independent30focusedtests pass. Actual liveIAB keyboard-only numeric/invalid recovery and localpanel missing/notattempted/confirmed/rejected verified; controlledunknown tests distinguished from live evidence. Newpanel is required in subsequent recording checklist; no footage/real-user validation claim. See retained persona cards, T065–T067 and video notes/sourcehashes.
