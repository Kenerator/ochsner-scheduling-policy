"""A small business boundary, deliberately in-memory and synthetic."""
from dataclasses import dataclass
import uuid


class SyntheticUnavailable(Exception):
    """Known fixture failure; unexpected implementation errors are not hidden."""


@dataclass(frozen=True)
class Proposal:
    id: str
    label: str


class DemoService:
    """Confirm exact proposals once per service instance, not across machines."""

    def __init__(self, adapter):
        self.adapter = adapter
        self._scope = uuid.uuid4().hex
        self._proposals: dict[str, Proposal] = {}
        self._results: dict[str, dict] = {}

    def propose(self, label: str) -> Proposal:
        if not isinstance(label, str) or not label.strip():
            raise ValueError("Describe the operation before asking for confirmation")
        proposal = Proposal(f"{self._scope}:{len(self._proposals) + 1}", label.strip())
        self._proposals[proposal.id] = proposal
        return proposal

    def confirm(self, proposal_id: str, confirmed: bool) -> dict:
        if type(confirmed) is not bool or proposal_id not in self._proposals:
            raise ValueError("Confirm a known proposal with an explicit yes/no")
        if proposal_id in self._results:
            return dict(self._results[proposal_id])
        if not confirmed:
            result = {"state": "cancelled", "message": "No operation performed"}
        else:
            try:
                result = self.adapter.execute(self._proposals[proposal_id])
            except SyntheticUnavailable:
                # Do not retry an ambiguous or rejected effect behind the user's back.
                result = {"state": "handoff", "message": "Service unavailable; use the documented support path"}
        self._results[proposal_id] = dict(result)
        return dict(result)
