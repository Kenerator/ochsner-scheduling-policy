# Milestones and optional UX refinement

Updated: 2026-10-09. Annotated immutable checkpoints backed up to the approved private origin; public delivery is separate.

| Tag | Source commit | Purpose / timing | Relevant docs or demo |
| --- | --- | --- | --- |
| `poc/planned` | `dcfe38834133eb17b054b6097cecfcaaa6ce834f` | Reconciled required dependencies and native planning; Analyze corrections applied before implementation | [Tasks](../../specs/001-appointment-scheduling/tasks.md) |
| `poc/mvp` | `49c5ad5706988be77770f646f202637d7f7acf43` | Independent review closed;109tests and all demos on fresh MacARM/Linux clones; real model integration | [Validation](../../specs/001-appointment-scheduling/quickstart.md), [review](reviews/adversarial-review.md) |
| `poc/scaffold` | `42e6bb0bab4b934c6361a59fcab17b64d080adf1` | Isolated scaffold and unchanged selectively supplied reference mock; no product qualification | [Provenance](../../reference/PROVENANCE.md), [video notes](video-notes.md) |

Create **annotated, immutable tags** for useful reviewed milestones—not each tool call. Suggested names: `poc/scaffold`, `poc/planned`, `poc/mvp`, `poc/ux-01-before`, `poc/ux-01-after`, `poc/submitted`. Use `poc/budget-baseline` only when the Operator directs capture of an actual agreed work-window baseline. Names are suggestions, not mandatory gates; tags do not confer release/publication authority.[^tagging]

After committing the intended source and verifying the tag is unused:

```sh
git tag -a poc/mvp -m "Working MVP checkpoint"
git rev-parse 'poc/mvp^{commit}'
# Only with push authority to the confirmed remote:
git push origin refs/tags/poc/mvp
```

Record the tag, resolved commit and purpose here in the next documentation commit; do not move a tag to include its own record. Use a new numbered tag for a later checkpoint. Never force-update tags or push all unrelated tags. See [Git setup](git-setup.md) for remote/commit cadence.

## Optional refinement

During Spec-Kit Tasks, consider an **optional post-MVP** task for a bounded UI/UX flow/polish pass. It cannot delay a working required slice, weaken acceptance, or substitute for core correctness. Follow the Operator's scope and timing decisions; agents must not silently stop or shrink work based on estimated elapsed time.

If selected, retain the working baseline with a pre-refinement tag, make the focused changes, test affected behavior, and tag the post-refinement result. Document the user benefit/trade-off in the existing decisions/next-steps files. Comparable synthetic-data screenshots or short clips may help the review; use the same scenario/view and disclose any separately permitted later work. If not selected, put a brief deferred item in next steps—no unfinished mandatory gate.

Link relevant tags from as-built docs and video notes instead of duplicating this table. Budget compliance and permission for supplemental work remain Operator decisions; never imply all versions were built within an agreed time window.

## Optional adversarial review

Consider one near-final or explicitly deferred task to populate the [review report](reviews/adversarial-review.md). Reuse a sufficient existing independent review. Preserve the source commit reviewed; commit sanitized findings and useful synthetic regressions. A suggested immutable tag is `poc/review-01`; record its source here and push that named tag only under existing destination/privacy authority. No raw consultation transcript, new mandatory gate or extra publication grant.

[^tagging]: [Git: tagging](https://git-scm.com/book/en/v2/Git-Basics-Tagging). Reviewed 2026-10-07. Use annotated tags for meaningful source checkpoints and explicitly push selected tags. Limit: A checkpoint is not release/publication authority or a budget-compliance claim.

Operator-selected +2h/+3h checkpoints are dispatched centrally at the actual marks. No future checkpoint tag or exact-time compliance is claimed here; future captures must preserve their actual timestamps and immutable source.
