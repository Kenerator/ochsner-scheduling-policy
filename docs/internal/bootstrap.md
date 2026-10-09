# Bootstrap: preview, execute, resume

Current UAT focus is targets **0 and 1**. Target 4 retains the cumulative runner; targets 5–6 remain experimental. Manual native stage prompts are available for all remaining stages. See [UAT quick start](uat.md).

Run from the template checkout with Python 3.11+. The baseline and target 0 need no model, SDK or Spec-Kit runtime. Targets 1–6 require the [isolated pinned tool profile](development.md#spec-kit-tool-profile), an installed Codex or Claude CLI, and its normal authentication/permissions.

```sh
PYTHONPATH=src .venv-speckit/bin/python -m poc_template bootstrap \
  --destination ../example-poc --name example-poc \
  --input YOUR_REQUIREMENTS.md --through 1 --integration codex
```

Default is a non-mutating preview. Add `--execute` to claim a new destination, copy the public template surface and run. Existing destinations and user-owned symlinks are refused; a partial project is preserved for inspection, never automatically deleted. Use target 0 to scaffold offline with ordinary Python instead. Install editable console commands in the generated project if desired; otherwise use `PYTHONPATH=src python -m ...` from its root.

The exported [policy worktree](../../policies/README.md) separates reviewed rule
sources, decision tables/models and synthetic decision scenarios. It is optional
and engine-neutral: scaffolding neither installs nor enables ZEN/CLIPSpy. Adopt
an engine in native Plan only when useful, with its pinned reviewer setup and
behavior tests; original client policies remain in the ignored RFP source tree.

`--input -` reads stdin once through EOF as UTF-8 Markdown, preserving its bytes and position among repeated file inputs. It works with interactive typing/pasting, quoted heredocs and pipes; see the [README examples](../../README.md#type-paste-or-pipe-intake). On macOS/Linux, finish interactive input with Ctrl-D on an empty line. At most one `-` is allowed. Empty/whitespace-only or invalid UTF-8 stdin and content over 1 MiB fail before destination creation; combined intakes retain the 16 MiB limit. Preview consumes stdin without saving a project, so supply it again on execution. The generated intake file, not stdin, supplies any subsequent native stage/resume.

## RFP directory intake

Use `--rfp DIRECTORY` alone or with `--input` files/stdin. The source directory
must exist and not itself be a symlink. All children are copied byte-for-byte
under `docs/product/RFP/source/`, retaining relative paths and empty directories;
source executable bits are not adopted. Symlinks, special files and unreadable
subtrees fail visibly before destination creation. Nothing is automatically
extracted, installed or executed. Intake plus RFP is limited to **16 MiB**, with
at most **1024 RFP entries** (files/directories); larger trees need explicit
preprocessing, not silent partial copying. Ordinary `--input` files retain their
separate 1 MiB per-file limit.

The tracked [generic index](../product/RFP/README.md) points to the ignored local
`manifest.json`: every file has a path, size, SHA-256 and text/attachment kind.
UTF-8 text includes reference code, not just Markdown. Binary/non-UTF-8
attachments are preserved and reported for explicit review/conversion; no claim
of PDF/image/archive understanding is made. Both automatic and manual Specify
receive the index alongside other input references; subsequent native stages use
the resulting feature context and original sources when needed. Sources and
manifest are hash-bound for automated continuation just like ordinary intake.
RFP text does not silently select a guidance profile: use the existing explicit
`--guidance-file` or marked ordinary `--input` mechanism if desired.

Originals/manifest are excluded from Template re-export and ignored by Git;
`.specify/bootstrap.json` is also local/ignored because it contains input
metadata. The generic index and derived specs/docs are tracked. This reduces
accidental disclosure, not confidentiality guarantees or permission to share.
Inspect derived content/history before external delivery; only deliberately copy
approved shareable material into tracked locations. Recipients of a repo alone
will not receive ignored originals: provide any needed permitted source material
separately or use sufficiently complete derived specs/runtime fixtures.

## Native stage selection

| Target | Attempted native stages, in order |
| --- | --- |
| 0 | None |
| 1 | Specify |
| 2 | Specify → Clarify |
| 3 | Specify → Clarify → Plan |
| 4 | Specify → Clarify → Plan → Tasks |
| 5 | Above → Analyze (read-only) |
| 6 | Above → Implement and feature-test verification |

Clarify is always invoked, even when it needs no questions. Pending questions, denied permission, unavailable CLI or invalid completion stop dependent stages. Stdout is one JSON report; stderr shows stage starts and native questions numbered n of N, with options/recommendations. The wrapper imposes no independent question-count limit; installed Spec-Kit owns that policy. Answer all pending IDs on resume. Response bytes and question fields remain bounded, and duplicate IDs are refused. Exits: 0 completed/preview or a valid running-state status query; 2 invalid create input; 3 input required; 4 blocked/failed/ambiguous. Read the JSON status: a running query's exit 0 is not completion, nor is a native paused run's exit 0.

Use the **exact run ID** from the output; the tool never guesses the latest run:

```sh
PYTHONPATH=src .venv-speckit/bin/python -m poc_template bootstrap status --project ../example-poc --run RUN_ID
PYTHONPATH=src .venv-speckit/bin/python -m poc_template bootstrap resume --project ../example-poc --run RUN_ID --answer 'QUESTION_ID=your response'
```

Answers are explicit developer input, not inferred from a persona or intake. Repeat for a subsequent question. A completed run is reported without rerunning stages. Target, intake, guidance, source pin, Constitution and bootstrap control bytes are immutable for that run; a deliberate change needs a fresh reviewed project/run. The native engine owns progress. The token-bound invocation intent/outcome only supplies missing question/result information and crash reconciliation—not an independent status ledger.

After interruption, inspect the reported run and any `poc-bootstrap.lock` owner. Do not remove a lock while its process may be alive. An absent/ambiguous final outcome is a recovery blocker, not permission to replay. Preserve native state; never edit it to claim completion. A verified completed outcome can be adopted without repeating its operation. This is bounded local development validation, not an authorization system or security sandbox.

After resolving the cause of a **recorded failed invocation**, use `bootstrap resume --project PATH --run RUN_ID --retry-failed`. Only the unfinished stage is retried; prior attempts are retained. This is explicit recovery, not an automatic repair loop or a way around denied permissions. Changed prerequisite/control bytes or an ambiguous interrupted outcome still require reconciliation rather than replay.

## Copy/paste native stages and mixed assistants

Stories or equivalent journeys/scenarios can be included in ordinary `--input` content; no special intake syntax is required. Stage 0 preserves the originals and creates [Persona-linked provisional drafts](../product/user-stories.md), always exposing Support/Admin coverage or a pending mapping. It does not determine whether arbitrary intake already contains stories. Both automatic and manual Specify receive the draft path as background; native Specify reconciles supplied content and infers missing stories. Keep origin separate from accepted scope, then link the native feature stories rather than duplicating their task status. No additional model call, role/permission inference, story approval gate or native template modification is added.

By default, a new scaffold has a local `main` Git repository with no commit or remote; `--no-git` opts out. Add `--git-extension` with the pinned tool profile to install native Spec-Kit Git branching/hooks offline. Its upstream auto-commit defaults remain off. Installation does not execute a stage, commit or push. Without that extension, Spec-Kit creates feature directories but does not create Git feature branches. Scoped local commits may be made independently; external delivery remains separate.

Every generated project contains `docs/internal/spec-kit-handoff.md`. Target 0 provides six separate blocks. A completed target 1 provides five; a completed target 4 provides Analyze and Implement. A failed or paused run retains prompts for its unfinished stage and all subsequent stages—not merely those beyond the selected target.

Blocks start with the installed native command: `$speckit-specify` in Codex or `/speckit-specify` in Claude, and the corresponding names for later stages. Specify references the copied intake; other stages use normal Spec-Kit feature context and prerequisite handling. No extra prerequisite/question workflow is imposed. The default guidance profile is `upstream-only`; deliberately supplied developer guidance is appended as native stage arguments.

Open the **generated project** in the chosen assistant. Both `.agents/skills` (Codex) and `.claude/skills` (Claude) are already present, so you may select a different assistant for every stage. They share `.specify/feature.json` and `specs/<feature>/` on disk; sequential use is required. Reload/discover skills in a newly opened assistant if needed. Claude's normal permission prompts and Codex's normal host controls still apply.

Display the saved remaining blocks with either syntax, without executing a stage:

```sh
PYTHONPATH=src python3 -m poc_template bootstrap prompts --project ../example-poc --integration claude
PYTHONPATH=src python3 -m poc_template bootstrap prompts --project ../example-poc --integration codex
```

Add `--run RUN_ID` to derive prompts from that exact native status instead of the saved handoff document (requires the tool profile). Manual stage execution does **not** silently change native automated completion. Stop/reconcile a live automated owner before switching to manual work, resolve pending questions/failures, then use the ordinary Spec-Kit documents as the continuation source. Do not resume an older automated run after changing its bound prerequisites manually.

## Guidance, personas and research

### Per-project native execution options

Leave model/effort unset to retain the configured native defaults. To select Codex explicitly, add `--model MODEL --reasoning-effort medium --stage-timeout 1800` to the creation command. These typed options are shown in preview and pinned in this project's bootstrap configuration for every stage/resume; they do not edit user/global settings or permissions. Model/effort must be available to your native CLI/account; unsupported choices fail visibly, never silently fall back. Explicit model/effort selection currently supports Codex only.

The default stage budget is 900 seconds. `--stage-timeout` accepts integer seconds from 1 through 86400. Each agent has its own finite budget; the outer workflow budget covers the selected stages plus five minutes of tooling overhead. Timeout preserves a failed run and partial files rather than claiming completion. Changing settings requires a fresh project/run, not alteration of the old bound configuration.[^codex-config][^codex-exec]

If several native CLI versions are installed, the developer may select a reviewed executable using upstream `SPECKIT_INTEGRATION_CODEX_EXECUTABLE=/absolute/path/to/codex` (or the corresponding `CLAUDE` setting). Keep that choice for resume. The bootstrap never automatically switches clients/accounts/models or installs an update when access fails. A model listed in a cache is not proof that an older client's account connection can execute it.

- `--persona namespace:id@revision` selects retained identities; repeat as needed. Omission emits a placeholder and a next-step entry.
- `--persona-catalog PATH` explicitly supplies a regular JSON catalog (maximum 1 MiB) for all selections. Requires at least one `--persona`. The generated catalog retains selected identities/history and their required ancestors; unrelated records are excluded and source/template catalogs remain unchanged. Namespace and pinned revisions must match. The retained catalog and source digest are bound in the bootstrap configuration; see [persona workflow](persona-workflow.md).
- `--guidance-file PATH` selects one strict JSON object with schema_version 1, profile (`poc-default`, `upstream-only`) and optional common/stages lists of short strings. The default is `upstream-only`: no extra template stage prompting. `poc-default` is an explicit opt-in to the richer PoC guidance. Custom fragments can augment either profile.
- Alternatively put that object in one fenced `poc-stage-guidance` block in an intake file. Competing blocks/files are refused. Effective fragments and their revision/digests are recorded at creation; no automatic preset, hook script or model selection.
- `--no-references`, repeated `--exclude-reference ID`, and `--reference-overrides JSON_FILE` control catalog-backed footnotes. Overrides change approved source fields, not commands or persona facts. Literal intake is never rewritten.

Arbitrary intake prose is reference material, never execution authority. Extra integration argv is rejected rather than inheriting an ambient permission bypass. Claude uses normal `acceptEdits` mode for local edits/common filesystem operations; other commands still need permission. No bypass mode or automatic general Bash grant is used. Project-local permissions belong in ignored `.claude/settings.local.json`, after reviewing the exact scripts/commands; do not copy personal rules into a shared template. Non-interactive Claude cannot display an approval dialog: inspect the retained `*-diagnostics.json` permission counts/tool names, resolve the actual cause and preserve an interrupted or failed run rather than blindly replay it.[^claude-permissions][^claude-rules][^claude-settings]

The Python starter verifies feature tests named `test_feature*.py`; alternative stacks/test tools require deliberately extending and qualifying the adapter, not accepting arbitrary commands returned by a model.

The approved plan may change application-owned package configuration such as CLI entry points in `pyproject.toml`. This is distinct from immutable bootstrap controls, the result schema, managed assets, tool permissions and Constitution; those cannot be rewritten to make the current run pass.

Agents report artifact paths, not invented cryptographic digests. The local verifier reads safe bounded prerequisite files and computes/stores SHA256. Missing files, wrong digests and binding drift remain errors. Wording/format checks are advisory, not semantic proof; Specify may leave explicit choices for normal Clarify. High/critical findings and unresolved plan-template fields stop advancement while preserving the findings/artifacts for developer review. The non-interactive runner adds only its result-transport/ownership boundary; the installed native skill owns the stage workflow. A question may mention a future output, but no absent file is counted as evidence.

## Optional convergence

After a completed target-6 run, an explicit follow-up may append remediation tasks:

```sh
PYTHONPATH=src .venv-speckit/bin/python -m poc_template bootstrap converge --project ../example-poc --run COMPLETED_IMPLEMENTATION_RUN_ID
```

This creates a separate native Converge run. It never automatically invokes Implement or declares the new tasks finished. Analyze itself never edits; high/critical findings block advancement and require a deliberate correction decision plus re-analysis. No automatic repair loop is installed.

## Qualification boundaries

Tests exercise native v1.1.0 and child-process failure/pause/recovery using a test-owned fake agent. That is not real-model proof. See `reference/bootstrap/qualification.md` for the actual clean-project integration results and known limits. Optional UI/docs/SDK profiles remain disabled adoption recipes until independently implemented and qualified. Local tools cannot certify general semantic correctness, clinical safety, production readiness or public-sharing rights.

[^claude-permissions]: [Claude non-interactive permission handling](https://code.claude.com/docs/en/headless). Reviewed 2026-10-06. Non-interactive execution retains permission controls and can report denied tools. Limit: A permission mode is not an OS sandbox or authority for external effects.
[^claude-rules]: [Claude fine-grained permission rules](https://code.claude.com/docs/en/permissions). Reviewed 2026-10-06. Review exact commands and grant narrow rules rather than general shell access. Limit: Actual command matching and managed policy must be checked in the installed release.
[^claude-settings]: [Claude project-local settings](https://code.claude.com/docs/en/settings). Reviewed 2026-10-06. Project-local settings can keep personal permissions out of shared configuration. Limit: Settings precedence and repository/worktree placement remain environment-dependent.
[^codex-config]: [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference#configtoml). Reviewed 2026-10-06. Model and reasoning choices can be selected explicitly for a native invocation. Limit: Actual model/effort availability depends on the account and installed client.
[^codex-exec]: [Codex native exec reference](https://learn.chatgpt.com/docs/cli/reference#codex-exec). Reviewed 2026-10-06. Non-interactive execution supports per-run configuration and structured final output. Limit: Structured output alone does not prove semantic completion; normal permissions remain.
