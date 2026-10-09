"""Repeatable offline scenarios; no network, real user data or AI required."""
from .adapters import SyntheticAdapter
from .core import DemoService


def run_scenario(name: str) -> dict:
    if name not in {"success", "cancel", "failure", "handoff"}:
        raise ValueError("Choose success, cancel, failure or handoff")
    adapter = SyntheticAdapter(fail=name in {"failure", "handoff"})
    service = DemoService(adapter)  # Each scenario resets its state.
    proposal = service.propose("Run a synthetic operation")
    result = service.confirm(proposal.id, name != "cancel")
    return {"scenario": name, "simulated": True, **result, "adapter_calls": adapter.calls}
