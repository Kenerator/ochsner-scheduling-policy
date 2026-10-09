# Marimo — optional, off

Reviewed: 2026-10-05. Import the reusable core in a thin reactive notebook/application. Keep consequential effects behind explicit core-bound confirmation; reactive reruns must not repeat effects. Notebook/package isolation is not an OS security sandbox or full authentication/RBAC.

At adoption: pin a reviewed release, build/run a tiny core-importing app, test confirmation/re-execution/failure, and retain the deterministic CLI demo. No Marimo dependency or app is installed by this baseline.[^marimo]

[^marimo]: [Marimo documentation](https://docs.marimo.io/). Reviewed 2026-10-05. Optional reactive Python presentation can import a reusable application core. Limit: Reactivity is not action authorization; notebook isolation is not an OS security sandbox.
