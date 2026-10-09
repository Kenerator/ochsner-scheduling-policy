# Ochsner scheduling · Policy PoC

A synthetic AI scheduling assistant with **ZEN 2.1.2 policy decisions** and a **Marimo 0.25.1 interface**. A live OpenAI model extracts intent and user-supplied fields; the reusable Python core owns identity resolution, returned appointment choices, explicit consent and scheduling effects. The supplied reference service is the scheduling source of truth.

## Setup

Use Python **3.11+** on macOS ARM64 or Linux x86_64. Obtain authorized access to the [private review repository](https://github.com/Kenerator/ochsner-scheduling-policy), then clone from the directory where you want the checkout using your normal authenticated GitHub setup. No local SSH alias is required. Verify your selected interpreter; substitute `python3.11` or another compatible executable if needed.

```sh
git clone https://github.com/Kenerator/ochsner-scheduling-policy.git
cd ochsner-scheduling-policy
python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip install --no-build-isolation -e .
.venv/bin/python -m pip check
```

`requirements.lock` pins the runtime package set. ZEN contains a native extension; a compatible platform wheel is required. Clean private-clone qualification is recorded in the [validation guide](specs/001-appointment-scheduling/quickstart.md), separately from local tests.

In one terminal, start the unchanged supplied synthetic service:

```sh
.venv/bin/python reference/mock-api/server.py --port 4012
```

For live interpretation, set `OPENAI_API_KEY` through your usual secure environment mechanism. `OPENAI_MODEL` optionally overrides `gpt-5.4-mini`. Never put keys in source, command arguments or a committed file. No Bitwarden dependency is required to run the application.

```sh
PYTHONPATH=src .venv/bin/marimo run app.py --host 127.0.0.1 --port 28182
# Or use the shared core through the terminal:
PYTHONPATH=src .venv/bin/python -m scheduling_assistant
```

For a credential-free rehearsal, explicitly select simulated interpretation:

```sh
SCHEDULING_INTENT_MODE=offline PYTHONPATH=src .venv/bin/marimo run app.py --host 127.0.0.1 --port 28182
PYTHONPATH=src .venv/bin/python -m scheduling_assistant --intent-mode offline
```

Open the UI at the loopback address printed by Marimo; retain its access token. Try “Find primary care providers downtown” without identifying a patient. For booking, try “Book primary care downtown”, then synthetic phone `555-0101` and date of birth `1985-04-12`. Choose a displayed number and review the exact proposal before replying **yes**. **No** declines; **reset** starts a conversation, preserving server bookings. An unknown booking outcome freezes retry and requires reconciliation; reset is not reconciliation. Restart only your owned mock process to restore its synthetic state.

## Verification and repeatable demos

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python -m scheduling_assistant.demo --scenario provider_lookup
PYTHONPATH=src .venv/bin/python -m scheduling_assistant.demo --scenario success
PYTHONPATH=src .venv/bin/python -m scheduling_assistant.demo --scenario failure
PYTHONPATH=src .venv/bin/python -m poc_demo --scenario success
PYTHONPATH=src .venv/bin/python -m poc_demo --scenario failure
```

Scheduling demos own disposable supplied-service instances, use offline interpretation, emit sanitized summaries, and need no running service or key. Additional scenarios: `duplicate_identity`, `conflict`, `no_availability`, `outage`, `medical_advice`. The retained `poc_demo` commands are generic scaffold regressions, not scheduling acceptance evidence.

Actual live CLI and controlled-IAB provider lookup, multi-turn booking and no-match passed. Fresh private clones passed109tests and all demos on MacARM/Python3.11.13 and Linux/Python3.12.3. See the validation guide for measurements and recording limitations.

## Boundaries and document index

This PoC is not enterprise or clinical readiness evidence. Synthetic matching is not production authentication. State and duplicate-effect protection are per conversation and in memory; durable idempotency, distributed concurrency, production identity, clinical review and load testing remain future work. Only a matching actual 201 establishes booking. Uncertain writes freeze retry, 409 requires a new choice and confirmation, and human guidance does not claim a delivered ticket. No medical advice, appointment retrieval, cancellation or rescheduling is implemented.

- [Specification](specs/001-appointment-scheduling/spec.md), [plan](specs/001-appointment-scheduling/plan.md), [canonical tasks](specs/001-appointment-scheduling/tasks.md), [validation](specs/001-appointment-scheduling/quickstart.md).
- [Policy tables and provenance](policies/README.md), [reference provenance](reference/PROVENANCE.md), [UI assets](docs/internal/ui-assets.md).
- [Architecture](docs/internal/as-built/architecture.md), [code walkthrough](docs/internal/as-built/code-walkthrough.md), [video notes](docs/internal/video-notes.md).
- [Personas](docs/product/personas.md), [stories](docs/product/user-stories.md), [decisions](docs/product/decisions.md), [backlog](docs/product/backlog.md), [roadmap](docs/product/roadmap.md), [work increments](docs/product/sprint-planning.md), [next steps](docs/product/next-steps.md).
- [Credential guard](docs/internal/security.md), [review](docs/internal/reviews/adversarial-review.md), [milestones](docs/internal/milestones.md), [retained scaffold tooling](docs/internal/bootstrap.md).

Named Persona pins and recorded video remain pending. Private repository backup is authorized; public delivery remains Operator-owned.
