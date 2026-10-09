# Getting started

This baseline is a synthetic demonstration, not a deployed service. Python 3.11+ is sufficient; no account or SDK credential is required.

From the repository root:

```sh
PYTHONPATH=src python3 -m poc_demo --scenario success
PYTHONPATH=src python3 -m poc_demo --scenario cancel
PYTHONPATH=src python3 -m poc_demo --scenario failure
```

The scenarios simulate explicit confirmation. For an interactive interface, show the exact proposal and collect a real yes/no before calling the core. Cancellation performs no operation. Failure returns a finite support/handoff message, not an automatic retry loop.

Run any command again to reset: every scenario starts fresh. See [recovery and limitations](recovery.md). Project-specific user instructions belong here when the template is adopted.
