# ZEN scheduling decision table

Updated: 2026-10-08. The authoritative graph lives in [package resources](../../src/scheduling_assistant/policy_models/scheduling.json), with [source IDs](../../src/scheduling_assistant/policy_models/sources.json). There is one executable copy. The application uses ZEN 2.1.2 `create_decision(str_json)` and `evaluate(dict)["result"]`.

The graph is `inputNode → decisionTableNode → outputNode`, with first-hit matching. Rule order preserves unknown-write reconciliation, medical/human stops, model/downstream failures, supported scope, private-action identity, focused missing-context/consent questions, positive proposed actions, and a final stop catchall. Clarification never authorizes an effect. Changed context must become a stale/missing proposal in controller-derived facts; the engine is stateless.

Every fact key is required. Unrelated fields use their explicit neutral status rather than being omitted:

| Fact | Allowed values |
| --- | --- |
| action | providers, identify, availability, propose, book, report |
| request | scheduling, medical_advice, human_requested, unsupported |
| criteria | missing, supported, unsupported |
| identity | not_checked, no_match, multiple, verified |
| slots | not_fetched, empty, returned |
| selection | missing, returned_option, invalid |
| proposal | missing, current, stale |
| consent | missing, declined, ambiguous, current_explicit |
| api | not_called, ok, created_201, conflict_409, unavailable, unknown_write, invalid_response |
| model | valid, malformed, unavailable |

`criteria` refers to information required for the proposed action, not a global form-completeness requirement. Public provider lookup can proceed with `identity=not_checked`. Private availability/proposal/booking/reporting requires `verified`; that status records the deterministic controller's synthetic matching result and is not production authentication. `propose` follows validated returned availability (`api=ok`); `book` gates a not-yet-issued effect (`api=not_called`); successful reporting requires a validated matching actual 201 (`api=created_201`). A 409 is not a booking; an unknown POST outcome requires reconciliation with no blind retry.

Output: immutable `Decision(disposition, reason, rule, sources: tuple)`. `.as_dict()` exposes exactly those fields, with sources as a JSON-safe list. Engine loading/evaluation/output failure returns `stop / policy_engine_unavailable / R-ENGINE-FAILURE`; invalid facts return `stop / invalid_policy_facts / R-INVALID-FACTS`. These fixed trust-boundary stops do not reproduce policy rules in Python.

See [the policy index](../README.md) and [tests](../../tests/test_scheduling_policy.py) for provenance and verification. The core's exact identity, offered-option membership, displayed current proposal, explicit current user consent, replay suppression and uncertain-effect guards remain independent of the engine result.
