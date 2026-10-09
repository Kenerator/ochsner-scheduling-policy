# Demonstration runbook

Updated: 2026-10-09. Use the [README](../../README.md#verification-and-repeatable-demos) exact commands. Scheduling demos own fresh ephemeral supplied-service instances and explicitly use offline rehearsal. Required scenarios: provider_lookup, success and failure (no match). Additional checks: duplicate_identity, conflict, no_availability, outage and medical_advice. Each emits sanitized outcomes, booking request count, actual policy rules and timings.

Interactive UI/API use loopback28182/4012. For live mode configure an ordinary OPENAI_API_KEY securely; never show it. Provider lookup requires no identity; booking must show returned choices and exact proposal before a separate explicit yes. Restart only your owned mock to restore synthetic bookings; conversation reset does not reset scheduling state. Unknown outcomes freeze retry pending reconciliation.

See [video notes](video-notes.md) for the≤5minute script and explicit recording status. Tests/output are not substitute footage. [Validation](../../specs/001-appointment-scheduling/quickstart.md) distinguishes actual live, controlled tests and browser evidence.
