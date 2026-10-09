# Scheduling data model

Date: 2026-10-08. Planned model, not as-built. Service spelling comes from [canonical OpenAPI](../../reference/openapi/scheduling-api.yaml); application boundaries from [spec](spec.md) FR-003–016.

| Entity | Fields and relationships | Validation and visibility |
| --- | --- | --- |
| Conversation | opaque local token; state; intent; user-supplied fields; identity revision; private candidates/unique patient; returned providers/offered slots; proposal; outcome | In-memory per session. New conversation inherits no patient/proposal/result. No raw transcript persisted in diagnostics |
| Patient match | patientId, firstName, lastName, dateOfBirth, phone, zipCode, establishedPatient | Service facts only. Required usable ID and identifying fields validated. Private candidates never enumerated. Synthetic match is not authentication |
| Search criteria | specialty, optional location/date bounds | specialty in primary_care/dermatology; location in downtown/uptown/lakeside. Valid ISO dates and ordered bounds. Unsupported requested type goes to guidance; not silently discarded |
| Provider | providerId, name, singular specialty, locations[], modalities[] | Returned provider only; no inferred availability. Enrich slot labels by joining providerId to returned providers; missing/inconsistent details cannot be invented |
| Available slot | slotId, providerId, specialty, location, startTime, available | Only returned available=true slots matching criteria. Valid offset-bearing timestamp shown as returned. No fixture-only daysFromToday/time/conflictOnBooking in application model |
| Booking proposal | opaque proposal token, conversation token, identity revision, patientId, slotId, displayed details, decision status | Immutable exact pair. Must reference uniquely resolved patient and offered slot. Changed identity/criteria/slot clears proposal and assent |
| Appointment | appointmentId, patientId, providerId, specialty, location, startTime, status | Only validated 201 response can establish scheduled success. Must agree with proposed patient and slot details (response has no slotId). Missing/inconsistent success after POST produces unknown effect |
| Diagnostic event / recovery context | opaque local token, intent/state, operation name, status/category, known outcome, escalation reason, elapsedMs | Allowlist only. No patient IDs, raw queries/bodies/text, DOB, phone, zip, names or keys. Distinguish guidance from delivered handoff |

## Guarded state transitions

- `collecting` → public provider lookup/results with no identity requirement; booking collects phone, DOB and specialty, retaining previous answers.
- `identifying` → `identified` on exactly one validated returned match; → `clarifying_identity` on multiple; → safe correction or `guidance` on zero.
- `clarifying_identity` asks for zip without revealing candidates; filter private results on supplied zip. Exactly one permits `identified`; zero/multiple permits correction or finite guidance. No arbitrary repeated automatic search.
- `identified` → `offering` after successful availability response. Empty slots yield alternate-search/guidance. New identity clears availability, proposal and confirmation.
- `offering` → `awaiting_confirmation` only for a selected displayed offered slot. Render exact details before accepting explicit yes for the current proposal. Unoffered input requires correction; a model-suggested slot never becomes an offered one.
- `awaiting_confirmation` + explicit yes with unchanged proposal → `booking`; refusal clears proposal without effect; ambiguity asks for an explicit decision. Any material change invalidates prior assent.
- `booking` → `completed` only on matching valid 201 appointment; → failed proposal on known rejection/409, suppressing the rejected slot ID for that search and requiring new choice and confirmation; → `unknown` on lost/malformed/inconsistent consequential response. Known service outage stops automatic progress. Transport uncertainty must not be mislabeled as definitive failure.
- `completed` + repeated confirmation returns the cached result without another POST. `unknown` blocks further booking in that conversation pending external reconciliation; session/mock reset is not evidence that the prior action failed.
- Any state + medical advice, human request or unsupported work → finite `guidance` without advice, triage or claimed ticket creation.

No persistence or cross-process idempotency is promised. A unique sequential conversation owns each effect; restart can lose replay history. Tests must cover cross-session tokens, changed proposals, duplicate assent and uncertain response recovery.
