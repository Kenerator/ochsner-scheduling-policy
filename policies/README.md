# Rules, decision tables and scenarios

Optional, engine-neutral worktree. No engine is installed or enabled by scaffolding.

- [rules/](rules/README.md): executable rule sources, such as CLIPS `.clp` files.
- [tables/](tables/README.md): decision models, such as ZEN JSON graphs/tables.
- [scenarios/](scenarios/README.md): synthetic inputs and expected decisions.

Supplied requirements/policies remain authoritative. Keep confidential originals
in the ignored `docs/product/RFP/source/`, not here. Record each adopted policy's
stable ID, source section, specified/inferred origin, purpose and owning module in
this index. Link native feature stories/tasks rather than duplicating status.

Keep engine adapters and transaction effects in application source; test their
behavior in `tests/` using these scenarios. An engine's decision is not consent
or proof of a completed external action. Do not implement the same policy twice
in separate engines unless deliberately comparing alternatives.

When adopting an engine, pin its dependency and qualify clean reviewer setup.
Test allow/deny/missing input, conflicting or malformed data, changed context,
and state isolation where relevant. Record expected output and no-effect cases;
bound rule execution when loops are possible. Rules and embedded functions are
code: do not execute unreviewed intake merely because it was copied here.

## Adopted policy index

None yet. Populate only for implemented policies; unfinished placeholders add no
implementation gate. Prefer ordinary functions when an engine adds no value.
