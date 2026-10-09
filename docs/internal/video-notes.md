# Walkthrough notes

Updated: 2026-10-09. Script only; no recorded or delivered video is claimed. Reviewed implementation046287d plus tested core deltas; qualification evidence lives in the [validation guide](../../specs/001-appointment-scheduling/quickstart.md).

- 0:00–0:25: Explain synthetic AI scheduling scope; live interpretation, actual ZEN policy gates and independent core safety checks. Persona pins remain unresolved for primary/patient and Support/Admin users.
- 0:25–1:05: Public downtown primary-care provider lookup without identity; open normalized policy inspector.
- 1:05–2:35: Reset conversation; book primary care downtown using supplied synthetic555-0101/1985-04-12. Show missing-information prompts, returned choices, exact patient/slot proposal and explicityes. Only matching actual201 is booked. Show no booking before confirmation.
- 2:35–3:20: Reset conversation, use no-match555-9999/1990-01-01; show finite guidance and no patient-specific action or claimed delivered ticket.
- 3:20–4:20: Walk through [architecture](as-built/architecture.md) and [core symbols](as-built/code-walkthrough.md): model extraction→ZEN decision→independent controller→HTTP→supplied mock; versioned source IDs, callback-only UI, allowlisted diagnostics.
- 4:20–4:50: Explain limits: per-session in-memory effects, synthetic matching, no production authentication/durable idempotency/load proof, no clinical advice; uncertain POST freezes retry. Show [next steps](../product/next-steps.md).

Target4min50sec, leaving10sec margin. Use a fresh owned mock and the mode shown onscreen. Offline rehearsal must be labeled; recorded live claims require the live application configuration. Never show keys, raw operational notes or private intake. Test the actual recording duration before delivery; recording and public submission remain Operator-owned follow-ons.

## Capture status — 2026-10-09

Operator/Media capture request received for actual controlled-IAB provider, booking and failure scenarios. No usable recording exists yet. This agent session exposes screenshots and UI control but no supported video recorder; recording is blocked on Media/Operator capture capability and a coordinated slot. No fake footage, test-output video or screenshot substitute was made. Intended originals destination and naming are managed by Media outside this repository; no file was written there.

Current actual UI: loopback28182, supplied API4012, live gpt-5.4-mini; offline controlled-IAB booking/proposal/actual201/policy inspector/reset/no-match verified. Live browser provider lookup, actual201booking and no-match are now qualified at reviewedsource49c5ad5; the inspector visibly includes currentconsent/identity/proposal facts. To restore deterministic synthetic state, terminate only the owned mock and restart `.venv/bin/python reference/mock-api/server.py --port 4012`; conversation reset preserves bookings and never reconciles unknown effects. After qualification, the owned mock was restarted to supplied fixture state and the UI conversation reset. A new deterministic take should still restart only its owned mock. Recording source revision is49c5ad5706988be77770f646f202637d7f7acf43 (poc/mvp), plus documentation-only finalhandoff. Capture slot remains uncoordinated because recording capability is unavailable here.

No capture files exist and no external destination was written. Canonical UI/API ports are28182/4012; no automatedhandoff feature is supported. Media/Operator must coordinate nativecapture and restart only the owned suppliedmock for each deterministictake.

Handoff state at2026-10-09 00:36CDT: final-source liveUI28182 collecting/unknown, no pendingproposal; ownedAPI4012 restarted to supplied fixture state. Temporary diagram server/tab closed. No recording slot or footage exists. Private finalhandoff documentation is committed separately from reviewedsource49c5ad5.


2026-10-09 visual repair: use the current app for future recording; the logo is no longer clipped and narrow policy tables scroll. Earlier recording-ready revision notes are historical. No finished video was created by this repair.


## Recording-off rehearsal — 2026-10-09T01:23:07.955665-05:00

Corrected candidate for RC-2 (delta from RC-1, source hashes below). Live gpt-5.4-mini, actual ZEN, supplied mock4012 and IAB28182. Recording OFF throughout. Complete before filming; no footage or delivery claim.

| Control/workflow | Actual rehearsal result |
|---|---|
| Message field, character counter, Send, clear after submit | Typed synthetic requests; counter changed and field cleared; current replies rendered |
| Reset, numbered choice, no, changed choice, separate yes | Reset collecting; refusal zero booking; change1→2 produced revised proposal; separate yes booked option2 with actual201 |
| Policy inspector and Action facts | Opened/closed both; enum-only decision/source/facts visible |
| Narrow table and focus | 390px viewport, no document overflow; native Right key scrolled focused region40px; expanded facts minimum210px readable |
| Framework menu, HTML and PNG exports | Opened menu and invoked both controls with public provider results only; no recorded-video claim |
| Provider lookup | Actual returned downtown primary-care providers, no identity |
| Missing identity and duplicate match | Missing fields requested; ZIP asked privately, candidates hidden; unique clarification continued |
| Conflict | Supplied conflict slot produced actual409 and truthful no-confirmation guidance |
| Empty availability and no match | Explicit no-slots/no-patient guidance, no invented booking/handoff |
| Medical advice and human help | No advice/triage, truthful usual-channel guidance, no queued-handoff claim |
| Service outage | Owned API stopped; actual UI request gave finite failure guidance; API then restarted |

Rehearsal exposed missed changed selection on RC-1 before any filming. Fixed by revoking pending proposal before model interpretation (also oversized input), accurately requesting selection in safe context and clarifying numeric extraction. Meaningful failing regressions preceded fixes; full114tests pass in16.585s, all8scenario demos and generic success/failure demos pass, Marimo check clean, independent delta review closed oversized boundary. No known rehearsal defect remains. Repeated identical form submit retained existing visible result and caused no additional POST.

- `app.py`: `7431190fd2e3022410ac76fb4faf44feedc4f95a7d4b81ebadd356e362f6760b`
- `src/scheduling_assistant/core.py`: `36aed4af3b0ce1da2679f8d68c664fb965033b471fd0aedfc0d7ef3dd626be37`
- `src/scheduling_assistant/adapters/intent.py`: `fcedc803dac2c7b29300995a3ac94a42ccf566ffa9bdb0999862c8501bc579b0`

Starting state restored: owned supplied mock restarted to pristine fixture state, UI collecting/unknown with inspector closed and empty field, viewport override reset. Controlled IAB rehearsal is green; native recording capability/exclusive SM capture slot still required. Capture every listed control and required operation; multiple raw clips may be needed, Media owns final≤5minute edit. Never claim omitted controls or tests as footage.


## Persona impact rehearsal — 2026-10-09T01:37:54.349413-05:00

Exact Jules/Ellie-Rae/Morgan-Rae/Sam-Rae pins retained with ancestry; all hypotheses. Existing behavior verified: short numbered choice, preserved identity/search on invalid99, stale/current consent and unknownfreeze. New actual impact: local Recoverycontext disclosure inside policy inspector, no delivery/console. Recording OFF.

Keyboard-only IAB: Tab from page→inspector→message field→Send, typed request changes character counter, Return submits, focus stays Send; Shift+Tab returns to input. Missingidentity→identity→invalid99→valid1 preserves context; inspector/Recoverycontext opened via Tab/Return. Newpanel displays field names only, missing names, patient-match category, actual booking-effect state, support Not sent, finite nextstep. Actual app checked beforeidentity, afteroptions/support-beforePOST (no booking), confirmed201 and rejected409; narrow390px panel has no document overflow. Unknown state tested meaningfully through actual core/UI adapters with controlled port outcome, not a claimed live ambiguous-write recording.

116tests16.615s, all8scenario demos+generic2 and Marimo check pass; independent focused review30tests no material issues. Earlier fullRC2 required/control rehearsal remains linked above; persona delta affected workflows reverified. Sourcehashes at final qualification:
- `app.py`: `16f46e9d09d2c8f740b31d085434a9cbf7d5d735f2ceb07cdf27ccf9d7d61504`
- `src/scheduling_assistant/models.py`: `39f89d129b05529656edb7c5f50a9616c6afe72c66029a1fc655de3121ebac69`
- `src/scheduling_assistant/core.py`: `aadc912af33c393c9037606d171f30e978ab5090dfe6e5475f9c083a0038ad45`
- `src/scheduling_assistant/adapters/intent.py`: `fcedc803dac2c7b29300995a3ac94a42ccf566ffa9bdb0999862c8501bc579b0`

Before filming: exercise new Recoverycontext open/close in addition to prior control checklist; reset only owned supplied mock and conversation, inspector closed, viewport default. Owned mock restored to pristine fixture state after persona checks. No footage exists; awaiting SM exclusive capture slot/capability.


## Final end-scroll text and video hold — 2026-10-09T01:52:25.719206-05:00

Qualified runtime: **RC-3 / 078b34f4fc47e58719bfd6725b9272611435efe1**. All native implementation/persona tasks complete. This final text is a documentation-only follow-on; runtime source hashes above remain unchanged, and no redundant RC is created. Operator VIDEO HOLD supersedes capture scheduling; no new takes until explicitly resumed. Media is finalizing only the already-started provider/control clip at a safe boundary; usable file/coverage has not yet been independently confirmed here. No finished or delivered video claim.

Suggested closing scroll (factual reference text; Media controls final edit):

> **Policy scheduling prototype — RC-3 · 078b34f4**
>
> Find providers without identity; clarify synthetic patient matches privately; choose a service-returned appointment and confirm it in a separate turn. Changed choices revoke the previous proposal. Only a matching scheduling-service201 is reported booked. Conflicts, no match, empty availability and outages produce truthful finite guidance; medical advice is declined. Unknown booking outcomes require reconciliation before retry.
>
> **Architecture:** thin Marimo0.25.1 UI and CLI share a guarded Python core. Genuine model extraction proposes fields; actual ZEN2.1.2 decision tables gate actions; independent transaction checks control consent and booking. HTTP adapters use the supplied synthetic mock. The inspector exposes bounded rule/source/fact provenance.
>
> **Persona impact:** exact Jules, Ellie-Rae, Morgan-Rae and Sam-Rae hypothesis pins are retained with ancestry. Keyboard-only numbered choices and invalid-input context were exercised. Morgan's local recovery panel separates supplied field names, missing information, booking outcome and next step; support contact always remains Not sent. These are synthetic implementation checks, not real-user validation or new permissions.
>
> **Verification:**116tests; eight scheduling demos plus generic success/failure demos; actual live browser required-flow/control rehearsals with recording off; independent focused review. Unknown-effect evidence includes controlled core/UI tests and is not presented as a live ambiguous-write demonstration.
>
> **Limits and next steps:** synthetic fixtures and in-memory sessions; no production authentication, durable distributed effect/idempotency guarantees, load qualification or enterprise-readiness claim. Validate real-user needs and operational/security/audit requirements before expansion. Optional appointment retrieval and automated staff delivery remain unselected. Video/public submission are incomplete and Operator-owned; filming is currently on hold.
