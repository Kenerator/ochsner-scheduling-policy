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

Current actual UI: loopback28182, supplied API4012, live gpt-5.4-mini; offline controlled-IAB booking/proposal/actual201/policy inspector/reset/no-match verified. Live browser provider lookup, actual201booking and no-match are now qualified at reviewedsource49c5ad5; the inspector visibly includes currentconsent/identity/proposal facts. To restore deterministic synthetic state, terminate only the owned mock and restart `.venv/bin/python reference/mock-api/server.py --port 4012`; conversation reset preserves bookings and never reconciles unknown effects. Existing mock has completed synthetic browser bookings, so a new capture must restart its owned mock. Recording source revision is49c5ad5706988be77770f646f202637d7f7acf43 (poc/mvp), plus documentation-only finalhandoff. Capture slot remains uncoordinated because recording capability is unavailable here.

No capture files exist and no external destination was written. Canonical UI/API ports are28182/4012; no automatedhandoff feature is supported. Media/Operator must coordinate nativecapture and restart only the owned suppliedmock for each deterministictake.
