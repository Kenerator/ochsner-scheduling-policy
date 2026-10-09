# Development

Updated: 2026-10-09. [README](../../README.md) owns actual Python3.11+ setup, pinned dependencies, launch and verification commands. [Feature tasks](../../specs/001-appointment-scheduling/tasks.md) own progress; [validation](../../specs/001-appointment-scheduling/quickstart.md) owns measured evidence.

Use a project-local virtual environment. ZEN2.1.2 and Marimo0.25.1 are required. Preserve the supplied backend, reference fixtures, hooks and credential guard. Write meaningful tests before behavior changes. Run `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v`, generic success/failure demos and affected scheduling demos. Use disposable service state for tests; do not mutate another lane's process.

The [walkthrough](as-built/code-walkthrough.md) explains actual symbols and a modification exercise; [architecture](as-built/architecture.md) explains boundaries. Re-version policy tables/source IDs deliberately. A model cannot grant identity or consent, and a policy proceed cannot bypass independent transaction checks. See [security](security.md) before committing and [milestones](milestones.md) before tagging. Retained generic scaffold tooling is documented in [bootstrap](bootstrap.md); it is separate from scheduling runtime behavior.
