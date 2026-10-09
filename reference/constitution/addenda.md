# Optional Constitution addenda

Reviewed: 2026-10-07. None is active merely because a domain is mentioned.

Adoption: name the chosen addendum, accountable decision, rationale and verification in `docs/product/decisions.md`; append its concrete obligations to the Constitution and affected spec/plan/tasks.

| Option | Concrete obligations and evidence |
| --- | --- |
| Privacy / regulated data | Data inventory, minimization, access/retention rules and appropriate qualified review; test no unintended exposure. No automatic regulatory claim. |
| Real authentication | Separate authentication from action authorization; test denied/expired/wrong-subject access and recovery. |
| Agentic / external effects | Identity/delegation scopes, explicit consequential confirmation, durable duplicate protection and bounded handoff; reconcile uncertain outcomes before retry. Test spoofing, replay, interrupted operations and ambiguous outcomes; never report a handoff as delivered without evidence. |
| Reliability | Declare failure modes, retry limits, persistence and recovery; exercise restart and interrupted-effect cases, including reconciliation after unknown outcomes. |
| Multi-agent collaboration | Assign implementation/state ownership and delegation boundaries; parallelize dependency-independent work with disjoint files or isolated repos. Preserve checkpoints, integrate/test combined results, and use concise milestone/blocker handoffs instead of per-tool reporting. Test interruption/conflicting-writer recovery where relevant; no particular private orchestration infrastructure is required. |
| Conversational / AI interfaces | Disclose known AI interactions; select interaction style and accessible alternatives from persona needs. Define reachable human assistance and truthful delivery states. Test ambiguity, correction, cancellation, confirmation and handoff without inferring authority from persona text or human-ish names. |
| Performance | Name interactions/environment/load/percentiles; measure feedback and completion, with explicit unmet-target reporting. |
| Accessibility | Applicable criteria and selected persona constraints; actual keyboard/assistive/constrained-use evaluation. |
| Production readiness | Threat model, secret handling, backups/rollback, observability and deployment approval; actual deployment/security evidence, not PoC tests alone. |
