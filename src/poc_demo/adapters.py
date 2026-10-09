"""Replace this synthetic boundary, not the core, when adopting a real API."""
from .core import Proposal, SyntheticUnavailable


class SyntheticAdapter:
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.calls = 0

    def execute(self, proposal: Proposal) -> dict:
        self.calls += 1
        if self.fail:
            raise SyntheticUnavailable("Controlled demo fixture")
        return {"state": "complete", "message": "Synthetic operation completed", "label": proposal.label}
