"""Small application contracts; adapters never establish booking authority."""
from dataclasses import dataclass, field
from typing import Protocol

class ApiError(Exception):
    """Categorized safe error: never retain a downstream body or request URL."""
    CODES={'api_error','api_failure','downstream_unavailable','invalid_request','missing_parameter','invalid_parameter','unknown_patient','unknown_slot','confirmation_required','invalid_json','slot_taken','malformed_response','unknown_write','model_unavailable','invalid_model_output','bad_configuration','read_failure'}
    def __init__(self,code,status=None,unknown=False):
        self.code=code if code in self.CODES else 'api_error'
        self.status=status if type(status) is int else None
        self.unknown=bool(unknown)
        super().__init__(self.code)

@dataclass(frozen=True)
class IntentResult:
    intent: str = 'unknown'
    fields: dict[str,str] = field(default_factory=dict,repr=False)

@dataclass(frozen=True)
class TurnResult:
    message: str
    state: str
    options: list[dict] = field(default_factory=list)
    policy: list[dict] = field(default_factory=list)
    outcome: str = ''

class IntentPort(Protocol):
    def interpret(self,text:str,safe_context:dict)->IntentResult: ...

class SchedulingPort(Protocol):
    def providers(self,criteria:dict)->list[dict]: ...
    def patient_matches(self,phone:str,dob:str)->list[dict]: ...
    def availability(self,patient_id:str,criteria:dict)->list[dict]: ...
    def book(self,patient_id:str,slot_id:str)->dict: ...
