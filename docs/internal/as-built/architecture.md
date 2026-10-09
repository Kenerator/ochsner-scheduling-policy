# As-built architecture

Updated: not yet populated. Reviewed source revision: not yet recorded.
Status: bootstrap stub; planned components are not as-built facts.

## Components and boundaries

Pending implementation: explain the actual entry points, reusable core, state/data
ownership, adapters and dependencies. Link their implementation symbols through
the [code walkthrough](code-walkthrough.md). Distinguish real services, synthetic
fixtures and disabled optional integrations. Link important [decisions](../../product/decisions.md)
instead of repeating their history.

## Diagrams

Pending implementation: add a small Mermaid component/dependency diagram and,
when useful, a sequence or state diagram for the core journey and failure/recovery
path. Name actual components and indicate effect/confirmation boundaries. Do not
invent components merely to fill a diagram. Include a short text explanation so
the document remains useful without Mermaid rendering. Check rendered diagrams
when a renderer is available; otherwise disclose that rendering is unverified.

## Operational limits

Pending implementation: describe actual persistence/reset behavior, uncertain
outcomes and reconciliation, relevant trust boundaries, and what remains mocked
or unimplemented. Link tests and limitations, not duplicated test receipts.

Populate near the end of implementation alongside the walkthrough, not before
coding may start. Planned architecture remains in Spec-Kit `plan.md`; this file
describes what was actually built. Keep it short and update affected sections.
Link the relevant [milestone](../milestones.md) and actual
[theme/asset index](../ui-assets.md) when applicable; do not duplicate their tables.
