# Persona portfolio

Small components combine roles, abilities, access, preferences and constraints into deterministic profiles. These original profiles are hypotheses, not researched people. Names imply neither demographics nor authority.

Recipes: constrained-operator, assisted-digital-consumer, acute-care-professional, longitudinal-care-consumer, enterprise-support; coordinator, domain-executor, workflow-planner, transport-relay, observer, independent-reviewer; unknown-caller.

Select relevant constraints explicitly. Adapt components rather than assuming every clinician, older adult or regional resident has the same needs. Relevant unspecified traits stay unknown. Public research supports design principles, not persona validation.

`components/` contains versioned inputs; `recipes/` pins them. Material conflicts require explicit overrides. The single `catalog.json` retains identities; cards are generated, not independently edited facts. Application scenarios are obligations for the actual PoC to implement and test—not safety guarantees from this utility.

Names and aliases share one NFKC/casefold/separator-normalized namespace. Retired entries never release their names. Reuse keeps identity; behavioral variants get a new ID/name and a pinned parent, family and explicit differences. Editorial revisions preserve behavior and every old snapshot.

The seed catalog has namespace `poc-template-seed-v1`; keep that namespace when reusing its personas. New independent allocations are provisional until reconciled with the shared portfolio. Names are unique within that portfolio, not globally across unrelated forks. Run catalog validation after Git merges.

Writers take one local lock around read/validate/write and atomically replace one file. A busy or leftover lock is reported, never silently removed. Inspect the catalog and whether the writer is active before recovery; do not blindly replay a possibly completed allocation. The lock does not serialize independent Git copies.
