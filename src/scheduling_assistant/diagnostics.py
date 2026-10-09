"""Allowlisted diagnostic metadata: never accept patient objects or raw errors."""
import math
import re
from .ports import ApiError

_INTENTS=frozenset({'provider_lookup','book','human_help','medical_advice','unsupported','unknown'})
_STATES=frozenset({'collecting','clarifying_identity','offering','awaiting_confirmation','booking','completed','guidance','providers','unknown'})
_OPERATIONS=frozenset({'turn','providers','patient_search','availability','propose','book','report','reset'})
_OUTCOMES=frozenset({'attempted','completed','failed','unknown','booked','no_match','no_availability','conflict','guidance','clarification','stale','providers'})
_REASONS=frozenset(ApiError.CODES)|frozenset({'','no_match','multiple_matches','no_availability','human_requested','medical_advice','unsupported','policy_denied','stale_proposal','declined','ambiguous_consent','identity_unresolved'})


def _enum(value,allowed,fallback):
    # Type-check before membership; arbitrary values are never stringified.
    return value if type(value) is str and value in allowed else fallback


def build_event(*,session,intent,state,operation,outcome,reason='',elapsed=0,
                status=None,from_state=None,to_state=None):
    """Build bounded metadata; elapsed is seconds, optional status is HTTP integer.

    Explicit arguments prevent callers from forwarding an API/model payload.
    The opaque session token is local correlation only, never a patient ID.
    """
    token=session if type(session) is str and re.fullmatch(r'[a-f0-9]{32}',session) else 'unavailable'
    milliseconds=0.0
    if type(elapsed) in (int,float):
        try:
            candidate=elapsed*1000
            if candidate>=0 and math.isfinite(candidate):milliseconds=round(candidate,2)
        except (OverflowError,ValueError):pass
    event={'session':token,'intent':_enum(intent,_INTENTS,'unknown'),
           'state':_enum(state,_STATES,'unknown'),'operation':_enum(operation,_OPERATIONS,'unknown'),
           'outcome':_enum(outcome,_OUTCOMES,'unknown'),'reason':_enum(reason,_REASONS,''),
           'elapsedMs':milliseconds}
    if type(status) is int and 100<=status<=599:event['status']=status
    if type(from_state) is str and from_state in _STATES:event['fromState']=from_state
    if type(to_state) is str and to_state in _STATES:event['toState']=to_state
    return event
