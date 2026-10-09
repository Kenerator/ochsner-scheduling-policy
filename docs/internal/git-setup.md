# Git setup and recovery

Reviewed: 2026-10-07. Local scaffolding and optional remote setup are separate operations.

## Local repository and native hooks

Bootstrap initializes local `main` by default, without a commit or remote. `--no-git` opts out. Spec-Kit 1.1.0's bundled Git extension is optional (`--git-extension`) and requires the isolated [tool profile](development.md#spec-kit-tool-profile). Normal feature stages do not install it implicitly.

The separate [credential guard](security.md) is a local Git pre-commit hook, not a Spec-Kit stage hook. It is installed by Git-enabled bootstrap unless existing hook configuration conflicts; no configuration is overwritten. Clones need explicit local installation. Its manual scan reads the staged index and redacts findings. Resolve actual findings or scan errors before committing; existing-hook conflicts may use a manual scan or deliberate integration, not removal of another safeguard.

Each native extension/integration setup command has a 60-second limit and no automatic retry. A timeout, launch error or nonzero exit reports the failed operation and preserves the scaffold, local repository and continuation prompts. Dependent Spec-Kit execution does not start. No global tool installation, network catalog fallback, forced replacement or automatic commit is introduced.

For recovery, keep the preserved directory. Inspect `.specify/extensions/git/`, `.specify/integration.json`, `.specify/init-options.json` and the selected assistant's skills before changing anything. From that project's root, use the **absolute path to the same reviewed tool interpreter** in place of `TOOL_PYTHON`:

```sh
TOOL_PYTHON=/absolute/path/to/.venv-speckit/bin/python
"$TOOL_PYTHON" -c 'from specify_cli import main; main()' extension list
"$TOOL_PYTHON" -c 'from specify_cli import main; main()' integration list
```

Resolve the reported cause (tool access, local filesystem error or confirmed stalled process) first. If the extension is absent, explicitly install the bundled `git` extension; if already registered, do not reinstall or use `--force`. Resume only unfinished integration setup, preserving existing customizations:

```sh
# Only when the previous inspection confirms the extension is absent:
"$TOOL_PYTHON" -c 'from specify_cli import main; main()' extension add git
# Register both assistants; restore the actual selected default last.
# Shown for a Codex default; reverse the two commands for Claude.
"$TOOL_PYTHON" -c 'from specify_cli import main; main()' integration use claude
"$TOOL_PYTHON" -c 'from specify_cli import main; main()' integration use codex
# Native switching rewrites script modes. Restore only the six executable
# declarations in the pinned 1.1.0 asset record, then verify all managed bytes.
chmod +x .specify/scripts/bash/check-prerequisites.sh \
  .specify/scripts/bash/common.sh .specify/scripts/bash/create-new-feature.sh \
  .specify/scripts/bash/resolve-template.sh .specify/scripts/bash/setup-plan.sh \
  .specify/scripts/bash/setup-tasks.sh
PYTHONPATH=src "$TOOL_PYTHON" -m poc_template.spec_kit_assets --root .
```

The final check must pass before automated stages. Do not rehash changed assets or claim bootstrap completed merely because files exist. An extension failure does not erase useful offline/manual UAT; retain the recorded incomplete setup until verified recovery. A fresh scaffold without `--git-extension` is an explicit alternative, not a silent fallback or overwrite.

## Optional new private GitHub repository

After local scaffold review, use an explicitly chosen owner/name and existing authenticated GitHub CLI. This is a separate developer/Agent setup step—not a network side effect of Stage 0. This guide does not itself grant remote creation or push authority; use the current project's grant.

GitHub API authentication and SSH authentication are separate. Confirm that the API account may create in the chosen owner and that the SSH alias accesses **that same repository**. Never silently switch owner/account. First inspect any existing `origin` and the exact GitHub destination; an existing repository/remote is a conflict to resolve, not permission to overwrite or adopt it.

```sh
# Run in the generated project; replace these values before running.
POC_OWNER=your-github-owner
POC_REPO=my-poc
POC_SSH_HOST=your-configured-github-ssh-alias
gh api user --jq .login
git remote -v
gh repo view "$POC_OWNER/$POC_REPO" --json nameWithOwner,isPrivate,url
```

Stop and inspect those results. Proceed only after confirming no existing `origin` and no existing destination; an access/network error is **not** proof of absence. Then create and verify:

```sh
gh repo create "$POC_OWNER/$POC_REPO" --private
gh repo view "$POC_OWNER/$POC_REPO" --json nameWithOwner,isPrivate,url
```

Only after confirming the exact owner/name and `isPrivate=true`, configure the local remote and test access:

```sh
git remote add origin "git@$POC_SSH_HOST:$POC_OWNER/$POC_REPO.git"
git ls-remote origin
```

An empty successful `ls-remote` is normal for a new empty repo; check its exit status. On ambiguous creation failure, inspect the exact destination before considering another create attempt. If the preferred SSH alias fails, resolve authentication or use an approved fallback alias only after verifying it can access the same owner/repo; do not change the destination. Local commits and the first non-force push are separate authorized steps. Do not include credentials in URLs, files or video notes.

## When private milestone delivery is authorized

Commit reviewed meaningful baseline content (explicit stubs are fine), then prepare/verify the private remote and push the initial commit. Continue coherent commits and non-force pushes at useful milestones; do not wait until the final demo to discover remote-access problems. Spec-Kit auto-commit hooks are unnecessary for this developer/Agent cadence. Prefer logical changesets and useful messages over commits per tool call.[^commits]

```sh
# In the confirmed project root, after scoped review/staging:
git diff --cached --check
PYTHONPATH=src python3 -m poc_template secrets scan --project .
git commit -m "Scaffold project baseline"
# Then configure/verify the private remote as above before the first push:
git push -u origin main
# At later milestones, review/stage only the intended changes, commit, then:
git push
```

Use the actual approved branch if different from `main`. Do not stage secrets, confidential assignment intake, environments or private native state. Private visibility is not permission to put them in history: a later public switch exposes code and Actions history/logs.[^visibility] Stop/reconcile ambiguous external outcomes before retry; continue unaffected local work. Only the authorized owner changes public visibility or submits the repo.

Use annotated immutable tags at meaningful checkpoints as described in [milestones](milestones.md). Push only named tags under the current remote grant; bootstrap does not create tags, releases or public visibility.

[^commits]: [Git: contributing to a project](https://git-scm.com/book/en/v2/Distributed-Git-Contributing-to-a-Project). Checked 2026-10-07; logical changesets simplify review and reversion.
[^visibility]: [GitHub: repository visibility](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility). Checked 2026-10-07.
