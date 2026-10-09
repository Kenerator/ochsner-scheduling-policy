# Bootstrap UAT quick start

Reviewed: 2026-10-06. Exercise a real small concept, not a perfect synthetic showcase. Python 3.11+; run commands from the template root. Use a new destination for each trial.

Before launch, verify the actual interpreter with `python3 --version`. If it is below 3.11, replace `python3` below with a verified compatible executable or existing project environment; no global Python change is needed. Use a lowercase `--name` slug even if the confirmed destination/display name uses uppercase. In chat UAT, present each decision in ordinary text with options/recommendation, not only question cards; preserve prior answers. Pass product requirements and labeled assumptions as intake, not setup prompts or pause/authorization records.

## 1. Offline scaffold and manual native continuation

```sh
PYTHONPATH=src python3 -m poc_template bootstrap \
  --destination ../my-poc --name my-poc --input /absolute/path/requirements.md \
  --through 0
```

Inspect the preview; repeat with `--execute`. No model call, credentials or Spec-Kit runtime is needed. Expect local Git on `main` (no commit/remote), a Constitution, intake, complementary docs, persona placeholder/next steps, `docs/internal/video-notes.md` and six separate prompts in the generated `docs/internal/spec-kit-handoff.md`. Optional private GitHub setup is a separate explicit step; see [Git setup and recovery](git-setup.md).

Open `../my-poc` as a project in Claude or Codex, paste the first block, and continue stages in order. Change assistant between stages if desired; change `$` to `/` on the command's first line for Claude, or use `bootstrap prompts --project ../my-poc --integration claude`. Keep the same feature files; do not run simultaneous writers. Spec-Kit owns clarifications, planning, analysis and implementation normally.

Personas composed in a task-owned external catalog can be selected with `--persona-catalog PATH --persona namespace:id@revision`. The generated project retains selected identities and their ancestors without changing the template. Use the exact returned selection IDs, not newly invented names/IDs. See [persona workflow](persona-workflow.md).

## 2. Optional automatic Specify

Install the [isolated tool profile](development.md#spec-kit-tool-profile) and authenticate your selected native CLI normally. No permission bypass is required.

```sh
PYTHONPATH=src .venv-speckit/bin/python -m poc_template bootstrap \
  --destination ../my-poc-auto --name my-poc-auto --input /absolute/path/requirements.md \
  --through 1 --integration codex --execute
```

Choose `--integration claude` to use Claude instead. Expect one actual Specify invocation, a spec/feature context, truthful completion or an actionable stop, and five remaining blocks after successful Specify. A pending question is answered with the exact `bootstrap resume` command described in the [guide](bootstrap.md). A failed attempt requires resolving its cause before explicit `--retry-failed`; manual continuation is also available after reconciling the automated owner.

## Acceptance observations

Development effort estimates are operator advice, not agent time limits or completion gates. Keep latency/usability targets separate from that planning estimate.

- Preview has no destination/model side effect; existing directories are never overwritten.
- The scaffold works without SDK/MCP/service credentials. Baseline success/failure demos and tests run using the [setup guide](development.md).
- Each remaining block invokes installed Spec-Kit normally and uses the correct assistant syntax. Switching assistants carries feature state through files, not assumed chat memory.
- Material questions/failures are visible; no failed call is presented as completed.
- Record friction or unclear instructions in `docs/product/next-steps.md`. Do not polish generated prose merely to qualify the bootstrapper.

Target 4 is an optional cumulative trial, not required for this UAT focus. Automatic Analyze/Implement and non-Python test adapters remain experimental. Optional profiles, real security/APIs/auth, public licensing and publication need their own project work.
