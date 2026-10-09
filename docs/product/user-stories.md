# User Stories — draft and index

Updated 2026-10-08. Supplied journeys and scenarios remain verbatim in intake. Reconciled story detail now lives in the native specification below; Q1 is resolved with optional appointment lookup and required duplicate-identity clarification within booking. Specification validation is not implementation completion evidence.

**Origin** (specified/inferred) is separate from **scope** (proposed/accepted/deferred). Inferred story wording can describe an explicitly required capability; preserve that requirement. Acceptance of an inference does not change its origin. Persona labels and drafts grant no permissions.

## Supplied sources

- [Intake 1](RFP/README.md)

## Native specification index

- [Find providers](../../specs/001-appointment-scheduling/spec.md#user-story-1---find-providers-without-identifying-a-patient-priority-p1)
- [Confirm and book](../../specs/001-appointment-scheduling/spec.md#user-story-2---book-the-selected-appointment-with-confirmation-priority-p1)
- [Resolve identity safely](../../specs/001-appointment-scheduling/spec.md#user-story-3---resolve-identity-safely-or-stop-priority-p1)
- [Failure and human-help guidance](../../specs/001-appointment-scheduling/spec.md#user-story-4---receive-truthful-failure-and-human-help-guidance-priority-p1)
- [Support/Admin recovery context](../../specs/001-appointment-scheduling/spec.md#user-story-5---understand-outcomes-and-recover-responsibly-priority-p2)

Native stories retain inferred wording, supplied scenario/requirement basis and scope labels separately. Native `tasks.md` will own implementation progress after Tasks; none exists yet.

## Persona mappings

Primary-user/patient Persona selection remains pending in [Personas](personas.md). Stories 1–4 use this unresolved placeholder, without inventing a named Persona or claiming validated research.

## Support/Admin coverage

**Persona selection pending:** corresponding Support/Admin placeholder in [Personas](personas.md); not a fabricated identity or permission.

- The INFERRED generic teammate seed and acceptance basis were migrated into [native Story 5](../../specs/001-appointment-scheduling/spec.md#user-story-5---understand-outcomes-and-recover-responsibly-priority-p2), reconciled with supplied observability policy. Coverage is documentation/diagnostics, not an admin UI or actual staff handoff.

Always retain this coverage or an explicit documented deferral. It may be served by existing help, diagnostics or documentation; do not silently add a console, authentication, live handoff or new permissions. Validate against actual policy and interfaces.
