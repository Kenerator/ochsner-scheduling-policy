# Persona workflow

Use the smallest relevant set of roles and context components. Include abilities, access, attitudes and preferences that matter to observable scenarios—not fictional biography. Do not infer traits from age, profession, regional identity or a human-ish name. Agent names always retain an agent label. Unknown caller type is separate from authentication and permission.

## Choose, retain, pin

1. Reuse an existing `namespace:id@revision` when its saved behavior fits.
2. Otherwise adapt a recipe with exact component versions and explicit overrides. Conflicts fail; relevant unspecified values stay unknown.
3. Compose a new identity or derive a variant with an unused name, a pinned parent, the same family and explicit differences. A variant must change resolved actor type, traits, requirements or scenarios; unchanged behavior belongs to reuse, even if its prose or provenance differs.
4. Render selected cards. Link scenarios into specifications and acceptance tests; validate actual needs with intended users/support staff.

```sh
# Use a separate project catalog if not allocating in the shared portfolio.
PYTHONPATH=src python3 -m poc_template personas --catalog reference/personas/project-catalog.json compose --recipe reference/personas/recipes/observer.json --name Rowan --family coordination
# For derivation, substitute the exact selection returned by compose/list.
PYTHONPATH=src python3 -m poc_template personas --catalog reference/personas/project-catalog.json derive --parent NAMESPACE:ID@1 --recipe PATH-TO-ADAPTED-RECIPE.json --name Rowan-Lee --difference 'Describe the actual behavioral change'
```

Default allocation uses the first available name from `names.json`; exhaustion fails visibly. Aliases and canonical names share one normalized reservation namespace. Same-persona reuse is allowed; reassigning a name to another identity is not. Similar spelling is a mnemonic, not computed behavioral distance. Families/parents are explicit.

To bootstrap using an external catalog without changing the template, add `--persona-catalog /absolute/path/personas.json --persona namespace:id@revision` to the bootstrap command. All selected identities resolve against that catalog. Only selected identity records (all retained revisions) and required ancestors are copied into the generated `reference/personas/catalog.json`; source/template catalogs remain untouched. This intentionally replaces the generated seed catalog, rather than merging namespaces. Source and retained-catalog digests are recorded in `.specify/bootstrap.json`; the retained catalog is bound for automated runs. Missing/mismatched identities or invalid/oversized/symlinked catalogs fail before creation. Independent allocations remain provisional, not newly validated research.

`catalog.json` is the single source of retained facts. Generated cards are not another editable source. Same-identity revisions can change editorial description only; behavioral changes need new identity. Snapshot-time status in a card is not current availability; inspect `list` for that. An `authoritative` allocation label describes portfolio reconciliation intent and grants no runtime authority.

## Recovery and collaboration

One exclusive lock spans catalog read/validate/change/atomic replacement. Busy or leftover locks fail without silent retry. Inspect both the catalog and whether a writer is active before manually recovering a stale lock. A completed-but-unacknowledged write must not be replayed blindly. Independent Git copies do not share this lock: validate merged catalogs and reconcile provisional identities before treating them as shared allocations.

No name-renaming or tombstone-deletion command is provided. Existing revisions remain resolvable after retirement. Keep namespaces when copying saved personas; qualify references across independent catalogs.

## Cards and research

`render --selection ...` accepts several pinned selections. `--defer` creates a clear placeholder and reports an unresolved next step. No constraint-rich selection adds the same next step without blocking exploration. The command never edits an existing next-steps memo for you.

Output goes to stdout unless `--output PATH` is explicit. Existing files are refused unless `--replace` is deliberate; symlinked outputs are refused. References use credential-free HTTPS URLs. `--no-references`, repeated `--exclude-reference ID`, editable source records and Python `render_card(..., overrides={...})` control footnotes. Markers and definitions remain paired and deduplicated. Optional documentation-site rendering still needs its actual build check.

Research records state a finding, limitation and review date. They support guidance, not validation of a synthesized person. Components may carry supplied validation records; the utility preserves these labels but does not independently verify research. Application authentication, delegation, retry/idempotency, clinical safety and production readiness must be implemented and tested in that application's domain.

New compositions use schema 2, retaining explicit overrides and unknowns. Recipe constraints are overrides. These additions are hypotheses, not validation inherited from the underlying component; an aggregate validation label requires all components to carry evidence and no unvalidated additions. Catalog validation requires evidence records to match the pinned components exactly. Original schema-1 hypothesis revisions remain readable without mutation, with a visible warning that override provenance was not recorded. Recompose explicitly for a new allocation; never silently migrate or relabel an old revision.
