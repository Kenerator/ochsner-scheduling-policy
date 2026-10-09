# Local operation and recovery

Updated: 2026-10-09. [README](../../README.md) owns setup and launch. Bind the UI and supplied service to loopback; default ports28182 and4012. Check ownership before stopping a process. Keep live credentials in process environment, never in Git, URLs, notebooks, prompts or logs.

Known failed reads/rejections can lead to correction or finite human guidance. A409 invalidates the proposal and requires a new selection and confirmation. A lost or inconsistent POST response is unknown: freeze retry and reconcile through the usual scheduling channel. No recovery endpoint, durable idempotency or delivered handoff is implied. Conversation reset preserves mock bookings; restarting the owned mock restores fixture state only for synthetic demonstrations and does not prove what happened in a real system.

Diagnostics use fixed categories and opaque local correlation tokens, excluding identity/body/query/text values. [Validation](../../specs/001-appointment-scheduling/quickstart.md) and [next steps](../product/next-steps.md) describe current evidence and limits. Private backup is authorized for the approved repository; public delivery remains Operator-owned. [Security](security.md) governs staged scans; [milestones](milestones.md) records immutable checkpoints.
