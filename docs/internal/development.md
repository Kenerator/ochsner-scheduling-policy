# Development and administration

Python 3.11+, standard-library runtime. From the repository root:

Check `python3 --version` first. On macOS, `/usr/bin/python3` may be Xcode Python 3.9; select a verified 3.11+ executable such as `python3.11` instead when creating the environment. An existing `.venv/bin/python --version` may already satisfy the requirement. No system/global interpreter replacement is required.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
.venv/bin/poc-demo --scenario success
.venv/bin/poc-demo --scenario failure
```

Editable installation uses setuptools; source execution needs no package download. No real admin/auth/storage operations are implemented. Keep settings and credentials out of version control. Replace synthetic adapters behind the core and qualify real failure/duplicate/authorization boundaries before live use.

See [demo runbook](demo.md), [persona workflow](persona-workflow.md), and [optional profiles](../../reference/profiles/index.md). User-facing commands are documented in [getting started](../user/getting-started.md), not duplicated here.

For code review and modification, use the [code walkthrough](as-built/code-walkthrough.md)
and [as-built architecture](as-built/architecture.md). Bootstrap provides stubs;
populate them in near-final Spec-Kit implementation tasks, not as prerequisites
for coding. Prefer file/symbol navigation and small useful diagrams. Execute
dependency-independent tasks in parallel where practical with safe writer ownership.

## Spec-Kit tool profile

Managed v1.1.0 assets are copied offline from a reviewed source build. The cumulative runner needs an isolated tool environment; the baseline demo does not.

```sh
python3 -m venv .venv-speckit
.venv-speckit/bin/python -m pip install -r reference/bootstrap/tooling-requirements.txt
PYTHONPATH=src .venv-speckit/bin/python -m poc_template.spec_kit_assets --root .
```

The native installer verifies runtime bytes and managed asset hashes. Existing/modified assets are preserved, not force-overwritten. An update is explicit: review the new release, stage its assets, preserve the Constitution/specs/tasks and local customizations, qualify both integrations, then update the source/runtime/asset record and tool lock. Do not update active runs or substitute a shared/global CLI update.

Python script composition is bound to the tool interpreter. Install only template-owned reviewed steps; workflow declarations and plugins are not security sandboxes. Bootstrap may not treat a zero exit as completion when native JSON says paused.

See the [bootstrap guide](bootstrap.md) for cumulative stages, normal permission handling, feature-test naming and explicit resume/convergence. Real integration qualification is recorded separately from synthetic boundary tests.
