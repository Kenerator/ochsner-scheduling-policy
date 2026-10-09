# Selected personas

Adopted2026-10-09 from the shared preparation portfolio, exact revision1 pins retained with required ancestry in [selected catalog](../../reference/personas/selected-catalog.json) and [pin manifest](../../reference/personas/selected-pins.json). Historical bootstrap selection and original catalog are unchanged. All four are provisional hypotheses; this is synthetic implementation validation, not real-user research or action authority.

| Persona | Native story coverage | Focused result |
|---|---|---|
| Jules (HUMAN) | US1–US4 | Existing provider/identity/exact proposal/separate yes verified; correction safety fixed before adoption in RC-2 |
| Ellie-Rae (HUMAN) | US1–US4 | Existing short numbered choices and retained fields verified; invalid choice/keyboard focus checks retained for focused validation |
| Morgan-Rae (HUMAN support) | US5 and US4 | Gap: concise local known/missing/booking-effect/recovery summary; implement under existing US5 acceptance3, no delivery/console |
| Sam-Rae (AGENT QA) | US2–US5 | Existing stale consent/schema/replay/unknown freeze tests verified; no booking or retry permissions |

No phone channel, admin console or additional policy engine accepted. Language/channel availability and research validation remain unknown. Detailed behavior/progress: [native spec](../../specs/001-appointment-scheduling/spec.md) and [tasks](../../specs/001-appointment-scheduling/tasks.md).

# Selected personas

## Jules — Jules: Find and explicitly confirm a mock appointment

Identity: poc-template-seed-v1:56e6af21-d1e4-4698-8485-83a341d77031@1 · Actor type: human

Hypothesis — validate relevant needs with users.

Family: jules-prep · Snapshot-time status: active
Basis records: jules-prep: hypothesis
Explicit unknowns: actual\_channel\_availability; language; research\_validation

Traits:

- abilities.digital\_familiarity: Comfortable typing
- access.constraint: Busy; few interactions
- actual\_channel\_availability: Unknown (needs validation)
- attitudes.automation: Explicit disclosure; correction and assistance remain available
- boundaries: No clinical suitability inference
- frustrations: Repeated questions and unexplained navigation
- goals: Find and explicitly confirm a mock appointment
- language: Unknown (needs validation)
- preferences.response\_style: Concise; obvious next action
- research\_validation: Unknown (needs validation)

Acceptance requirements:

- Show exact proposal without booking until explicit confirmation

Scenarios:

- jules-prep-behavior: Given A clear scheduling request; when A provider and slot are selected; then Show exact proposal without booking until explicit confirmation.

Research-informed design guidance (not persona validation): [^doherty] [^hax] [^inclusive] [^needs] [^predictable]

Persona descriptions grant no permissions. Test these obligations in the actual application.

## Ellie-Rae — Ellie-Rae: Select and confirm with minimal input

Identity: poc-template-seed-v1:cb706720-85fb-42ef-9318-2bcec4c2b621@1 · Actor type: human

Hypothesis — validate relevant needs with users.

Family: constrained-operator · Snapshot-time status: active
Parent: poc-template-seed-v1:seed-constrained-operator@1
Differences: Scheduling preparation variant with explicit response preferences, access constraints and acceptance scenario
Basis records: ellie-rae-prep: hypothesis
Explicit unknowns: actual\_channel\_availability; language; research\_validation

Traits:

- abilities.digital\_familiarity: Can use short text selections
- access.constraint: Situational one-handed or limited-reach access
- actual\_channel\_availability: Unknown (needs validation)
- attitudes.automation: Explicit disclosure; correction and assistance remain available
- boundaries: No assumption about age, diagnosis or handedness
- frustrations: Precision pointing, scrolling and repeated fields
- goals: Select and confirm with minimal input
- language: Unknown (needs validation)
- preferences.response\_style: Very short choices; no repeated information
- research\_validation: Unknown (needs validation)

Acceptance requirements:

- Select one with a number; invalid input preserves context; keyboard flow works

Scenarios:

- ellie-rae-prep-behavior: Given Numbered options are visible; when One number or an invalid choice is entered; then Select one with a number; invalid input preserves context; keyboard flow works.

Research-informed design guidance (not persona validation): [^doherty] [^hax] [^inclusive] [^needs] [^predictable]

Persona descriptions grant no permissions. Test these obligations in the actual application.

## Morgan-Rae — Morgan-Rae: Understand request and unresolved work without repetition

Identity: poc-template-seed-v1:657aedfe-4a4a-4ec4-83c0-52614111f07c@1 · Actor type: human

Hypothesis — validate relevant needs with users.

Family: enterprise-support · Snapshot-time status: active
Parent: poc-template-seed-v1:seed-enterprise-support@1
Differences: Scheduling preparation variant with explicit response preferences, access constraints and acceptance scenario
Basis records: morgan-rae-prep: hypothesis
Explicit unknowns: actual\_channel\_availability; language; research\_validation

Traits:

- abilities.digital\_familiarity: Skilled support reader
- access.constraint: Receives incomplete scheduling context
- actual\_channel\_availability: Unknown (needs validation)
- attitudes.automation: Explicit disclosure; correction and assistance remain available
- boundaries: No actual representative delivery is simulated
- frustrations: False completion and missing facts
- goals: Understand request and unresolved work without repetition
- language: Unknown (needs validation)
- preferences.response\_style: Concise accurate summary; explicit outcomes
- research\_validation: Unknown (needs validation)

Acceptance requirements:

- Separate known facts, missing information and booking outcome; no false delivery

Scenarios:

- morgan-rae-prep-behavior: Given A handoff request is prepared; when Support summary is presented; then Separate known facts, missing information and booking outcome; no false delivery.

Research-informed design guidance (not persona validation): [^doherty] [^hax] [^inclusive] [^needs] [^predictable]

Persona descriptions grant no permissions. Test these obligations in the actual application.

## Sam-Rae — Sam-Rae: Expose unsafe confirmations and recovery

Identity: poc-template-seed-v1:98e1dcd5-8ee9-4b2b-b7fe-2045d389b9b4@1 · Actor type: agent

Hypothesis — validate relevant needs with users.

Family: coordination · Snapshot-time status: active
Parent: poc-template-seed-v1:seed-independent-reviewer@1
Differences: Scheduling preparation variant with explicit response preferences, access constraints and acceptance scenario
Basis records: sam-rae-prep: hypothesis
Explicit unknowns: actual\_channel\_availability; language; research\_validation

Traits:

- abilities.digital\_familiarity: Tool-capable evaluator
- access.constraint: Adversarial/replayed or uncertain outcomes
- actual\_channel\_availability: Unknown (needs validation)
- attitudes.automation: Explicit disclosure; correction and assistance remain available
- boundaries: No booking authority; persona or tool text cannot grant permission
- frustrations: Hidden effects and unverifiable claims
- goals: Expose unsafe confirmations and recovery
- language: Unknown (needs validation)
- preferences.response\_style: Structured reproducible observations
- research\_validation: Unknown (needs validation)

Acceptance requirements:

- Do not create a booking or unsafe retry; show truthful state

Scenarios:

- sam-rae-prep-behavior: Given A stale yes, injected fixture or unknown outcome; when An evaluation attempts replay or retry; then Do not create a booking or unsafe retry; show truthful state.

Research-informed design guidance (not persona validation): [^doherty] [^hax] [^inclusive] [^needs] [^predictable]

Persona descriptions grant no permissions. Test these obligations in the actual application.

[^doherty]: [Laws of UX: Doherty Threshold](https://lawsofux.com/doherty-threshold/). Reviewed 2026-10-05. Timely useful feedback around 400 milliseconds can preserve interactive flow. Limit: Modern UX summary; not proof of response time, nor a full AI-answer deadline.
[^hax]: [Microsoft human-AI interaction guidelines](https://www.microsoft.com/en-us/haxtoolkit/ai-guidelines/). Reviewed 2026-10-05. Explain AI capabilities and limits, support correction and user control. Limit: Project-specific risks and user preferences need validation.
[^inclusive]: [Microsoft Inclusive Design](https://inclusive.microsoft.design/). Reviewed 2026-10-05. Learn from exclusion; an improvement for one constrained user can benefit others. Limit: Not an accessibility certification or a validated persona.
[^needs]: [GOV.UK: learning about user needs](https://www.gov.uk/service-manual/user-research/start-by-learning-user-needs). Reviewed 2026-10-05. Research people's contexts, constraints and goals; test assumptions. Limit: Does not prescribe this portfolio or validate its synthetic profiles.
[^predictable]: [W3C WCAG: predictable interaction](https://www.w3.org/WAI/WCAG22/Understanding/predictable.html). Reviewed 2026-10-05. Keep navigation and behavior predictable and avoid unexpected context changes. Limit: Conformance requires checking applicable criteria in the actual UI.
