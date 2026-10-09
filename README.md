# PoC-Template

A lean starting point for human-centered, reviewable proof-of-concept projects.

For developers and teams turning concepts and requirements into small, demonstrable projects. Human-centered means reducing friction for users, support staff and administrators—including people with constrained abilities, devices or circumstances—not making AI pretend to be human.

## What you get

- A Python library/CLI starter with synthetic adapters, repeatable demos and meaningful tests.
- A baseline Constitution, complementary user/developer docs, decisions and next steps.
- A composable [persona portfolio](reference/personas/README.md) and configurable research references.
- Input-driven scaffolding, Codex/Claude Spec-Kit assets and separate native continuation prompts.

Requires **Python 3.11+**. The baseline demo, personas and offline scaffolding have no runtime dependencies, online service or SDK credential requirement. Marimo, UI/docs tooling, other languages and nxusKit are [optional adoption recipes](reference/profiles/index.md), disabled by default—not installed extensions.

## Contents

- [Bootstrap quick start](#bootstrap-quick-start), including [stdin intake](#type-paste-or-pipe-intake)
- [Model and effort guidance](#model-and-effort-guidance)
- [Demo and development](#demo-and-development)
- [Diagnostics and clean setup checks](#diagnostics-and-clean-setup-checks)
- [Persona quick start](#persona-quick-start)
- [Project documents](#project-documents)

## Project documents

- Product: [brief](docs/product/brief.md), [client requirements/RFP](docs/product/RFP/README.md), [personas](docs/product/personas.md), [User Stories](docs/product/user-stories.md), [decisions](docs/product/decisions.md).
- Planning: [backlog](docs/product/backlog.md), [roadmap](docs/product/roadmap.md), [sprint planning](docs/product/sprint-planning.md), [next steps](docs/product/next-steps.md).
- Use and review: [user setup](docs/user/getting-started.md), [developer setup](docs/internal/development.md), [demo runbook](docs/internal/demo.md), [video notes](docs/internal/video-notes.md).
- As-built navigation: [code walkthrough](docs/internal/as-built/code-walkthrough.md), [architecture and diagrams](docs/internal/as-built/architecture.md).
- UI and checkpoints: [asset/theme index](docs/internal/ui-assets.md), [milestone tags and optional refinement](docs/internal/milestones.md).
- Policy artifacts: [rules, decision tables and scenarios](policies/README.md), independent of engine adoption.
- Operations: [launch/recovery/delivery checklist](docs/internal/operations.md), [trusted qualification profile](docs/internal/qualification.json).
- Hygiene and review: [staged credential guard](docs/internal/security.md), [optional adversarial report](docs/internal/reviews/adversarial-review.md).

Planning files start as explicit placeholders, not invented commitments. Use feature Spec-Kit `spec.md`, `plan.md` and `tasks.md` as the detailed work source; link them rather than maintaining a second task checklist. When adopting the scaffold, replace Template-specific README guidance with the actual project's quickstart and preserve a short contents/document index.

As-built files also start as stubs. Spec-Kit Tasks schedules their population near the end of implementation, after the relevant code stabilizes—not as a gate before coding. Execute independent work in parallel where practical, respecting dependencies and avoiding competing writers on shared files or native state.

## Bootstrap quick start

Run from this repository root. Use a new destination and replace the example requirements path with your own. Repeat `--input` for multiple documents.

First run `python3 --version`: examples assume it is **3.11 or newer**. Some macOS shells select Xcode Python 3.9 instead. If yours does, substitute a verified compatible executable (for example `python3.11` or an existing `.venv/bin/python`) in every command. To create a new environment, use that compatible executable for `-m venv`; don't replace system Python. See [environment setup](docs/internal/development.md).

`--name` is a lowercase technical slug such as `poc-uat-001-01`; the destination folder and human-facing name may retain `PoC-UAT-001-01`. The tool reports invalid slugs rather than silently renaming them.

```sh
# Stage 0: preview only; no files created or model calls
PYTHONPATH=src python3 -m poc_template bootstrap \
  --destination ../my-poc --name my-poc \
  --input /absolute/path/requirements.md --through 0

# Create the scaffold without executing any Spec-Kit stage
PYTHONPATH=src python3 -m poc_template bootstrap \
  --destination ../my-poc --name my-poc \
  --input /absolute/path/requirements.md --through 0 --execute
```

Stage 0 produces six separate copy/paste blocks in the generated `docs/internal/spec-kit-handoff.md`. Open the generated project in Codex or Claude and use its native stages sequentially. You may switch assistants between stages; shared project files carry the feature context. When no persona is selected, the scaffold includes an explicit placeholder and next-step entry.

### Use a client requirements directory

`--rfp` recursively copies a local directory into `docs/product/RFP/source/`,
preserving names, structure, empty directories and file bytes. It can be the
only input, or accompany repeated `--input` files/stdin:

```sh
# RFP-only offline scaffold (omit --execute for a preview)
PYTHONPATH=src python3 -m poc_template bootstrap \
  --destination ../client-poc --name client-poc \
  --rfp /absolute/path/client-requirements --through 0 --execute

# RFP plus your own additional requirements
PYTHONPATH=src python3 -m poc_template bootstrap \
  --destination ../client-poc-extended --name client-poc-extended \
  --rfp /absolute/path/client-requirements \
  --input /absolute/path/augmentation.md --through 0 --execute
```

Automatic Specify and manual Specify prompts reference the [RFP index](docs/product/RFP/README.md)
and its local manifest; native stages reconcile those sources with additional
input. UTF-8 text and reference code participate as requirements input, **not
commands to execute**. Attachments/non-UTF-8 files are preserved and visibly
counted for explicit review/conversion, not silently understood. See
[limits and privacy](docs/internal/bootstrap.md#rfp-directory-intake).

Originals, their manifest and `.specify/bootstrap.json` stay **Git-ignored** by
default; the generic index is tracked. Derived specs/docs can still expose
client details—review before sharing, especially before making a repo public.

Supplied User Stories (or journeys/scenarios) may arrive through any `--input` file or stdin and are preserved verbatim. Stage 0 also exports `docs/product/user-stories.md` with **inferred, provisional** seeds from selected Personas and explicit Support/Admin coverage. It does not claim to understand arbitrary input or approve new scope. Native Specify reconciles supplied stories first and infers missing ones; afterward the document links to native `spec.md` stories rather than duplicating task progress. Story origin and implementation scope are separate. Support/Admin may use existing help, diagnostics or docs, not an automatically added console.

New scaffolds initialize **local Git on `main`**, without a commit or remote, and install a basic staged-credential pre-commit guard when no existing hook configuration conflicts. Existing safeguards are preserved with an explicit warning. See [credential hygiene](docs/internal/security.md) for manual scan/install, interpreter selection and limitations. Git must be available; `--no-git` explicitly opts out. Preview never initializes Git. Generated applications contain starter behavior tests, not the template-maintainer test suite.

Spec-Kit 1.1.0 makes branching/commit hooks an optional bundled extension. To include those native hooks, use the isolated tool profile and add `--git-extension` (also works with Stage 0):

```sh
PYTHONPATH=src .venv-speckit/bin/python -m poc_template bootstrap \
  --destination ../my-poc-git --name my-poc-git \
  --input /absolute/path/requirements.md --through 0 --git-extension --execute
```

The extension is installed locally from the pinned runtime, with no network fallback. Upstream auto-commit is disabled by default; choose its settings deliberately or make scoped commits yourself. No GitHub remote, push or publication is created. Failed/timed-out setup preserves the project and identifies the operation; see [Git setup and recovery](docs/internal/git-setup.md), including the explicit new-private-repository setup step. See the [Git extension](https://github.com/github/spec-kit/tree/v1.1.0/extensions/git).

For personas composed in a separate catalog, add `--persona-catalog /absolute/path/personas.json --persona namespace:id@revision` (repeat `--persona` as needed). All selections in that invocation use that catalog. The generated catalog retains only selected identities, their revision histories and required ancestors; unrelated records and the template/source catalogs are not modified. See [persona workflow](docs/internal/persona-workflow.md).

### Type, paste or pipe intake

Use `--input -` once to read UTF-8 text from stdin until EOF. For interactive entry, run this command, type/paste your requirements, then press **Ctrl-D on an empty line** (macOS/Linux):

```sh
PYTHONPATH=src python3 -m poc_template bootstrap \
  --destination ../my-poc-typed --name my-poc-typed \
  --input - --through 0 --execute
```

Or use a quoted heredoc; the shell treats its contents literally rather than expanding `$variables`, backticks or command substitutions:

```sh
PYTHONPATH=src python3 -m poc_template bootstrap \
  --destination ../my-poc-heredoc --name my-poc-heredoc \
  --input - --through 0 --execute <<'POC_INPUT'
# My PoC
Demonstrate one core workflow and one recoverable failure.
Use synthetic data and document assumptions and next steps.
POC_INPUT
```

Pipes work too: `cat requirements.md | PYTHONPATH=src python3 -m poc_template bootstrap --destination ../my-poc-piped --name my-poc-piped --input - --through 0 --execute`.

Stdin is preserved as an ordered Markdown intake file in the generated project and may be combined with other `--input` files. Empty/invalid UTF-8 input and content over 1 MiB are rejected; the existing 16 MiB combined limit still applies. Do not supply secrets. Omitting `--execute` previews only, but still consumes stdin—provide it again for execution or use a saved file for repeatable trials. Automatic stages receive the saved intake, not the exhausted stdin stream.

```sh
# Display remaining native prompts without executing a stage
PYTHONPATH=src python3 -m poc_template bootstrap prompts \
  --project ../my-poc --integration claude
# Use --integration codex for Codex syntax instead
```

For **automatic Specify**, first set up the [isolated Spec-Kit tool profile](docs/internal/development.md#spec-kit-tool-profile) and authenticate the selected native CLI normally:

```sh
PYTHONPATH=src .venv-speckit/bin/python -m poc_template bootstrap \
  --destination ../my-poc-auto --name my-poc-auto \
  --input /absolute/path/requirements.md \
  --through 1 --integration codex \
  --model gpt-6.1-sol --reasoning-effort medium --execute
```

Successful Specify leaves five continuation blocks. Claude is also supported via `--integration claude`, omitting the Codex-only `--model`/`--reasoning-effort` options. Normal permissions apply; failures and developer questions stop dependent stages. Default guidance is `upstream-only`, preserving native Spec-Kit behavior. See the [bootstrap guide](docs/internal/bootstrap.md) for preview, exact-run status/resume, explicit retries and custom guidance.

**Support boundary:** current UAT focus is Stage 0/1. Selecting Stage 4 attempts Specify → Clarify → Plan → Tasks cumulatively; it remains an optional trial. Automatic Analyze/Implement (5–6) remain experimental. See [qualification limits](reference/bootstrap/qualification.md) and the [UAT quick start](docs/internal/uat.md). Synthetic fixtures are not real authentication, clinical-safety or production-readiness implementations.

## Model and effort guidance

Suggested starting points, reviewed **2026-10-06**, not enforced defaults:

| Work | Suggested GPT-6.1 Sol effort |
| --- | --- |
| Collect input, operate Stage 0, inspect scaffold/demos | Low |
| Specify, Clarify and Plan | Medium |
| Tasks from a straightforward plan | Low; Medium for dependencies |
| Analyze and bounded implementation | Medium |
| A demonstrated hard defect or design conflict | High temporarily |

Avoid Extra High for initial UAT unless a concrete comparison justifies it. Lower effort generally reduces latency and reasoning-token use; scope control still depends on clear requirements and stopping criteria, not effort alone. These recommendations are workload hypotheses, not guaranteed quality or subscription-cost ratios. See [OpenAI effort guidance](https://developers.openai.com/api/docs/guides/deployment-checklist#set-up-reasoningeffort).

The **project agent's UI setting and an automatically launched child CLI's setting are separate**. Explicit Codex `--model`/`--reasoning-effort` choices bind the automated run; omission retains native configured defaults. Manual stages may each use a different assistant/model/effort. Account/client availability must be verified; unsupported choices fail visibly rather than silently switching.

## Demo and development

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m poc_demo --scenario success
PYTHONPATH=src python3 -m poc_demo --scenario failure
```

Every scenario resets. The CLI fixtures simulate confirmation; an actual UI must collect explicit confirmation of the exact proposal. See [user setup](docs/user/getting-started.md), [recovery](docs/user/recovery.md), [developer/admin setup](docs/internal/development.md), [five-minute demo script](docs/internal/demo.md), [video production notes](docs/internal/video-notes.md), [decisions](docs/product/decisions.md) and [next steps](docs/product/next-steps.md).

Follow the [Constitution](.specify/memory/constitution.md). [Optional profiles](reference/profiles/index.md) are disabled adoption recipes, not installed extensions. Choose a license and review public-sharing scope before publication.

## Diagnostics and clean setup checks

Run these from the Template/tool environment with a verified Python 3.11+ interpreter:

```sh
# Read-only: local interpreter, managed assets, native tools, Git root and locks
PYTHONPATH=src python3 -m poc_template doctor --project ../my-poc

# Preview the candidate's committed qualification profile; no installation
PYTHONPATH=src python3 -m poc_template qualify --project ../my-poc

# Export committed source, install in its own disposable environment and run checks
PYTHONPATH=src python3 -m poc_template qualify --project ../my-poc --execute
```

Commit the trusted `docs/internal/qualification.json` profile with the candidate first. Adapt its checks to the actual application: the default only tests the generic starter. Uncommitted edits are excluded. These helpers make no model calls or GitHub writes and do not certify semantic acceptance or reviewer access. See the short [operations checklist](docs/internal/operations.md) for recovery and delivery limits.

## Persona quick start

Run from this repository root. Optionally use `python3 -m venv .venv` and `.venv/bin/python -m pip install -e .` for the `poc-template` command. Editable installation uses setuptools as a build tool; the utility itself has no runtime dependencies.

```sh
PYTHONPATH=src python3 -m poc_template personas validate
PYTHONPATH=src python3 -m poc_template personas list
PYTHONPATH=src python3 -m poc_template personas reuse --selection namespace:persona-id@1
PYTHONPATH=src python3 -m poc_template personas render --selection namespace:persona-id@1
PYTHONPATH=src python3 -m poc_template personas render --defer
```

Use a shared catalog for permanent cross-project reservations. Existing seed identities remain reusable offline; new independent allocations are provisional. Never reference a floating `latest`. Retiring a persona preserves its name and old revisions. See [workflow](docs/internal/persona-workflow.md), [selected sample cards](docs/product/personas.md) and [next steps](docs/product/next-steps.md).

Research guidance is configurable in `reference/research/sources.json`. `render --no-references` suppresses markers and definitions; repeated `--exclude-reference ID` omits individual sources. Editing a source does not silently rewrite existing documents or persona facts. Regenerate explicitly, and never relabel a hypothesis as researched evidence.

<!-- Bootstrap: replace project name, purpose, audience and pain addressed. -->
<!-- Bootstrap: add setup, core/failure demo flows, decisions, limits and next steps. -->
<!-- Bootstrap: add user/admin documentation links and licensing before publication. -->
