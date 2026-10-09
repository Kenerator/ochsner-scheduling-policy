# Next steps

## Scheduling Plan handoff — 2026-10-08

- Continue with native Tasks from the [scheduling plan](../../specs/001-appointment-scheduling/plan.md) and [validation guide](../../specs/001-appointment-scheduling/quickstart.md). Q1 retains optional existing-appointment lookup and requires duplicate-identity clarification within booking; implementation has not started.
- Select/validate primary-user and Support/Admin Personas when practical; current native stories retain unresolved mappings.
- Establish the assignment receipt/deadline baseline with the Operator before making any time-window compliance claim. Publication, credentials and external submission remain outside this local-stage grant.

The remaining generic follow-ons below are background, not additional scheduling scope.

- Validate selected persona needs with intended users/support staff.
- Add real application authorization, handoff and side-effect tests where relevant.
- Run bootstrap UAT with a real small concept; record useful friction. Later automatic Spec-Kit stages and optional executable profiles remain separate follow-ons.
- Choose licensing and review sharing scope before publication.

## Real-use prerequisites

- Replace synthetic fixtures with real APIs only after reviewing contracts, failure handling and durable duplicate protection.
- Add actual user/admin authentication, action authorization, credential handling and data/privacy controls as appropriate.
- Define a real support/handoff path and test interrupted/ambiguous effects and recovery.
- Record required deployment/security/compliance decisions; synthetic tests are not production readiness.

## Roadmap questions

- Validate pain/personas and UAT with intended users, support and administrators.
- Select a thin UI, documentation site, Marimo or optional reasoning adapter only when useful.
- Measure interactive performance if needed; distinguish useful feedback from completion.
- Record a project-specific video up to five minutes and try the team modification exercise.

## Scale and rollout questions

These are follow-on planning prompts, not new PoC implementation gates. Mark irrelevant items explicitly; replace unknowns with agreed project targets when practical.

- **Will it scale?** Define dataset/workload sizes, concurrent users, peak requests/effects per second or minute, growth and upstream rate limits. Set latency/error/resource targets; measure representative peak load and failure/recovery behavior before claiming capacity.
- **Deployment:** choose environments, safe setup, credentials, observability and rollback. If operating alongside an existing system, name the system of record and single effect owner; plan synchronization/reconciliation and prevent duplicated writes or actions.
- **UAT:** identify user, support and admin participants, representative scenarios, permitted data and acceptance criteria. Decide whether parallel comparison is read-only/shadow or explicitly routed to one write owner; prevent test traffic from affecting real users and reconcile differences.
- **GA rollout:** choose pilot/cohorts, cutover/rollback triggers, monitoring, support and migration. Define coexistence with the old system, duplicate-effect protection, reconciliation and eventual retirement; deployment or UAT success alone does not establish GA readiness.

## Deferred-selection example

# Selected personas

## Persona selection deferred

Select and validate a constraint-rich persona as soon as practical.

- Select or map a Support/Admin Persona and reconcile its draft story against intake.
