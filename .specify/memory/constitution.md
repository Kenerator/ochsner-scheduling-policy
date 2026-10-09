# Project Constitution

Version: 0.2.1 · Reviewed: 2026-10-07

Produce a credible, understandable proof of concept quickly without disguising limitations. Addenda apply only when explicitly adopted.

## I Empathy and useful outcomes

Design for the user's purpose and pain, including support and administration. Document personas, situational constraints and observable success scenarios. Research assumptions remain hypotheses until validated.[^needs] Select a constraint-rich persona when practical; otherwise keep a placeholder and next-steps entry to select and validate one soon. Names and demographics do not determine abilities or preferences.

Use Persona-linked User Stories or equivalent journeys with observable acceptance scenarios. Preserve supplied sources; mark inferred wording/basis explicitly and keep origin separate from scope approval. Always document Support/Admin needs and corresponding Personas, or a visible pending/deferred mapping and next step. This is empathy coverage, not an implicit admin feature or new implementation gate. Native feature specifications own reconciled stories; supporting indexes link instead of duplicating task status.

## II Predictable and accessible interaction

Keep workflows coherent, reversible where practical, and free from navigation, retry or handoff loops.[^predictable] Confirm the actual consequential action explicitly. Errors explain the next useful step without blaming the user. Make assistance reachable. Disclose known AI interactions; human-ish names do not imply a human representative. Respect selected personas' interaction constraints.

Surface consequential unanswered questions visibly; honor existing answers and approvals within their scope. Distinguish attempted, completed and unknown outcomes; uncertain effects require reconciliation before retry, not an assumption that reset means failure.

## III Responsive behavior with honest measurement

Target useful feedback within the 400 ms Doherty Threshold where feasible; set separate completion targets for longer work.[^doherty] Performance claims need a scenario, environment, load and measurement. Benchmark when warranted by the PoC's goals. Record unmet targets and user impact instead of inventing compliance.

## IV Small core and explicit boundaries

Prefer reusable library logic, thin interfaces and effects at adapters. Encourage a CLI for useful setup, diagnostics and repeatable demos, not every UI operation. Explain contracts, failures, assumptions and important tradeoffs in concise comments. Optional integrations must not make the baseline depend on accounts, credentials or services.

## V Meaningful verification

Write behavior tests before new behavior or defect repairs. Tests catch meaningful failures, not coverage percentages. Include success, negative, boundary, recovery and appropriate persona-linked acceptance cases. Use real local components and synthetic external fixtures. Verify setup and demo from a clean generated project; passing tests alone do not prove user outcomes or real integrations.

Verify documented setup and core/failure flows from a clean checkout or explicitly labeled clean-copy equivalent using declared prerequisites. Prefer project-local installation; never silently alter global tooling, shell configuration or security controls.

## VI Safe and truthful exploration

Use synthetic data and mocks by default. Never commit credentials, personal data or private operational material. Distinguish simulation from live behavior, actor type from authenticated identity, and identity from authorization. A PoC shortcut cannot certify compliance or production security. Real data, external effects and sensitive deployment need project authorization and controls.

Preparation and synthetic-trial evidence do not prove assignment outcomes. Demonstrations and video claims must identify what actually ran; reusable generic assets must not masquerade as product execution or delivered handoffs.

## VII Repeatable demonstration and complementary documentation

Provide setup, core flow, failure/handoff, reset, decisions, limitations and next steps. Keep user and developer/admin docs complementary, linking shared facts. Include a demo script suitable for a video up to five minutes and a small team modification exercise. Keep research footnotes editable and tied to supported findings.

Treat maintainers, reviewers and support staff as users too: provide a concise as-built architecture and file/symbol walkthrough with relevant tests. Schedule population near the end of implementation; stubs do not gate its start. Verify navigation and actual design at the completion handoff, record the reviewed revision, and update affected sections when behavior changes.

## VIII Deliberate debt and lightweight governance

Allow reversible experiments and explicit shortcuts that aid discovery. Record important debt, risk and the next sensible action in a small next-steps memo, not a parallel management system. Use proportionate specs/plans/tasks. Amend the Constitution or adopt an addendum with a brief rationale and affected artifact updates; no fixed waiting period or blanket coverage threshold.

Keep one authoritative source for each requirement/task/status fact; link supporting views instead of duplicating ledgers. The human developer/operator owns compliance with external effort budgets and estimates, including on-the-spot tradeoffs. Agents report timing but must not independently halt, shrink scope, omit required behavior or replan because of elapsed or estimated time. Honor explicit human pauses and actual tool execution timeouts; product response-time targets and appointment times remain separate constraints. Execute independent tasks and PoC lanes in parallel whenever practical, preserving dependencies, tests-first order and safe writer ownership. Synthetic trials qualify reusable mechanisms; refine their work products only when findings reveal a transferable defect or material project risk. Do not perfect a sample in place of completing the agreed capability.

See [optional addenda](../../reference/constitution/addenda.md).

[^doherty]: [Laws of UX: Doherty Threshold](https://lawsofux.com/doherty-threshold/). Reviewed 2026-10-05. Timely useful feedback around 400 milliseconds can preserve interactive flow. Limit: Modern UX summary; not proof of response time, nor a full AI-answer deadline.
[^needs]: [GOV.UK: learning about user needs](https://www.gov.uk/service-manual/user-research/start-by-learning-user-needs). Reviewed 2026-10-05. Research people's contexts, constraints and goals; test assumptions. Limit: Does not prescribe this portfolio or validate its synthetic profiles.
[^predictable]: [W3C WCAG: predictable interaction](https://www.w3.org/WAI/WCAG22/Understanding/predictable.html). Reviewed 2026-10-05. Keep navigation and behavior predictable and avoid unexpected context changes. Limit: Conformance requires checking applicable criteria in the actual UI.
