# Scheduling policy execution

Updated: 2026-10-08. This candidate executes **ZEN 2.1.2** in its scheduling workflow. The application core calls `PolicyEngine.evaluate` before proposed actions; the engine neither verifies a patient nor grants consent nor performs an HTTP effect. Deterministic transaction checks independently recheck exact current patient/slot/context binding before booking. A policy `proceed` decision alone is insufficient authority.

- [Authoritative first-hit table](../src/scheduling_assistant/policy_models/scheduling.json): 41 ordered rules, including clarification, rejection and a final stop catchall.
- [Source registry](../src/scheduling_assistant/policy_models/sources.json): stable source IDs, origin document/section/bullet and native requirement links. This is a concise provenance map, not an original intake copy.
- [Engine adapter](../src/scheduling_assistant/policy.py): strict categorical input validation, actual ZEN evaluation, immutable decision and fixed safe trace.
- [Behavior and boundary tests](../tests/test_scheduling_policy.py): real-engine positive/negative/missing/priority/context cases and fail-closed engine/model/output handling.
- [Table contract](tables/README.md), [native requirements](../specs/001-appointment-scheduling/spec.md), [implementation tasks](../specs/001-appointment-scheduling/tasks.md).

The supplied `policies.md` rules remain authoritative. `POL-ID-*`, `POL-MED-*`, `POL-BOOK-*` and `POL-HANDOFF-*` map to their exact numbered bullets. `ASSIGN-REQ-01` maps to the assignment's required follow-up behavior. `CON-*` identifies the approved common acceptance contract; `SPEC-FR022` identifies the accepted ZEN fail-closed boundary. The source registry distinguishes supplied origin from approved candidate/common-contract constraints. No clinical eligibility, established-patient, rescheduling or cancellation rules were invented.

Facts contain only the ten documented enum fields and must be derived by the controller from validated state. Unknown/missing keys, unknown values, identity values and non-string values stop. Decisions expose only `disposition`, `reason`, `rule` and source IDs; no raw query, transcript, patient/slot value or arbitrary engine output is retained. The source graph is committed application code: user-supplied graphs, callbacks and dynamic loaders are unsupported. The adapter accepts only the bounded enum-comparison table graph schema, with no function nodes or executable custom expressions. It has no Python policy fallback.

Changing the table requires source review, actual-engine regression tests, packaging verification and affected workflow tests. The reviewer can modify a supplied-policy condition in the committed table and observe its gate through the shared core; production identity/session/effect infrastructure would remain a separate change. This is not production authentication, durable idempotency, clinical readiness or scaling proof.

Run from the candidate root with declared dependencies installed:

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -p 'test_scheduling_policy.py' -v
```

The policy tests do not qualify live AI, actual browser behavior or complete application effects. Those integrated checks belong to native tasks and the as-built handoff. Historical [rules](rules/README.md) and [scenario](scenarios/README.md) scaffolds are not additional executable policy engines.
