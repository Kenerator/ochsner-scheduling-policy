# Video production notes

Updated: 2026-10-08 23:23 CDT. Status: planning/prerequisites; no finished assistant demo or recording.

Candidate: policy-first scheduling assistant. Exact local root: `/Users/ken/codeRepos/ochsner-scheduling-policy`. Supplied independent mock: `http://127.0.0.1:4012`. Planned Marimo conversation/policy inspector: `http://127.0.0.1:28182` (not yet running).

Verified prerequisites: Python 3.11.13, Marimo 0.25.1 with passing dependency check; unchanged selectively vendored reference mock returns provider results and no-match response. A bounded live structured intent check returned HTTP200 from `gpt-5.4-mini-2026-03-17`, validated provider intent in 1.12 seconds. This is a single-call capability result, not end-to-end or multi-turn assistant qualification.

Start reference mock from candidate root: `.venv/bin/python reference/mock-api/server.py --port 4012`. Reset by stopping only this candidate-owned process and restarting it; no shared booking state or unrelated process termination. Source hashes: [provenance](../../reference/PROVENANCE.md). No raw query/prompt/transcript or credential retained in evidence.

Baseline local commit: `42e6bb0bab4b934c6361a59fcab17b64d080adf1`; staged guard passed170 files. Private GitHub provisioning is centrally owned by MLX; no candidate remote yet. Native bootstrap `802acfd5` completed Specify and is in Clarify. The supplied scenario lookup-scope conflict was resolved using approved common-contract precedence: duplicate identity safeguards required, existing appointment retrieval optional.

Timing: advisory horizons 00:41/01:41/02:11CDT on October9; Operator owns compliance and baseline capture. No work-window compliance claim.

Keep this file current as Specify, Plan and Implement establish the actual product. Record confirmed behavior, not aspirations; link to canonical specs/tests instead of copying them. Use synthetic data and keep credentials and personal data out of recordings.

## Native Plan update — 2026-10-08

[Planning artifacts](../../specs/001-appointment-scheduling/plan.md) now define the reusable policy core, CLI, scheduling/intent ports, diagnostic boundaries and [planned five-minute validation walkthrough](../../specs/001-appointment-scheduling/quickstart.md). Native setup identifies `001-appointment-scheduling`; actual local Git branch is `main`. Implementation has not started. Preliminary Marimo inspector remains deferred; it is not required by the accepted text slice.

This Plan stage made no model-service call and used no credentials. Fresh verification ran ten generic starter tests and the generic success/failure demos successfully; this proves no appointment-assistant outcome. Prior single-call prerequisite evidence above remains separate from planned/live end-to-end AI verification. Next native stage is Tasks; manual planning does not rewrite bootstrap execution state. No recording, delivery or time-window compliance is claimed.

## Audience and personas

<!-- Bootstrap: selected personas -->
Persona selection pending. Select/validate personas as soon as practical; then capture names, relevant constraints and the workflows demonstrating their needs. See [persona cards](../product/personas.md).
<!-- Bootstrap: end selected personas -->

## What to demonstrate (up to five minutes)

- Purpose and user pain: Not yet recorded.
- Demonstrated User Story and corresponding Persona (including a useful Support/Admin case), supplied vs inferred origin: Not yet recorded. Link [stories](../product/user-stories.md) and native specs; do not present a draft or deferred story as working behavior.
- Core flow and visible outcome: Not yet recorded.
- Failure/recovery or handoff flow, including what really happens: Not yet recorded.
- Exact launch/scenario/reset commands and prerequisites: Not yet recorded.
- Technical walkthrough: architecture and core/adapter boundaries; stack; key decisions and trade-offs: Not yet recorded.
- Methodologies actually used: Spec-Kit stages, meaningful tests/TDD, reviews and persona-driven acceptance: Not yet recorded.
- Limitations, mock vs real integrations, measured vs unmeasured performance, and next steps: Not yet recorded.
- Small live-review modification to invite team discussion: Not yet recorded.

Use the [demo runbook](demo.md) for timing and reproducibility, [decisions](../product/decisions.md) for rationale and [next steps](../product/next-steps.md) for unfinished work. Update the date and replace placeholders as work completes; the video Agent should ask about unresolved facts rather than inventing them.

Link the [code walkthrough](as-built/code-walkthrough.md) and [as-built architecture](as-built/architecture.md) when populated. If multiple candidates will be submitted, explain the distinct hypotheses/trade-offs and why retaining alternatives helps reviewers choose; identify the recommended starting point. Do not imply every candidate is complete or demonstrate unverified behavior.

Record the demonstrated [milestone tags](milestones.md) and permitted [UI assets/conventions](ui-assets.md). If a bounded post-MVP refinement actually occurred, note pre/post tags, comparable redacted views and the user benefit/trade-off. Distinguish separately permitted later work from the original baseline. For the ending/review discussion, include any unresolved sponsor/platform UI-conventions question and whether refinement was performed or deferred; do not expand the five-minute ceiling automatically.
