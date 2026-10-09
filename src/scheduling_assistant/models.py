"""Validate service facts and keep identity/proposals private to one conversation."""
from dataclasses import dataclass,field
from datetime import date,datetime
from uuid import uuid4

SPECIALTIES={'primary_care','dermatology'}
LOCATIONS={'downtown','uptown','lakeside'}

def _strings(value,keys):
    if not isinstance(value,dict):raise ValueError('invalid service object')
    for key in keys:
        if not isinstance(value.get(key),str) or not value[key].strip():raise ValueError('missing service field')

def _time(value):
    try:t=datetime.fromisoformat(value)
    except (TypeError,ValueError):raise ValueError('invalid service timestamp') from None
    if t.tzinfo is None:raise ValueError('timestamp must have offset')

def validate_criteria(value,require_specialty=False):
    allowed={'specialty','location','startDate','endDate'}
    if not isinstance(value,dict) or set(value)-allowed:raise ValueError('unsupported criteria')
    result={k:v for k,v in value.items() if v is not None and v!=''}
    if require_specialty and not result.get('specialty'):raise ValueError('specialty required')
    if result.get('specialty') and result['specialty'] not in SPECIALTIES:raise ValueError('unsupported specialty')
    if result.get('location') and result['location'] not in LOCATIONS:raise ValueError('unsupported location')
    for k in ('startDate','endDate'):
        if k in result:
            try:
                if date.fromisoformat(result[k]).isoformat()!=result[k]:raise ValueError()
            except (ValueError,TypeError):raise ValueError('invalid date') from None
    if result.get('startDate') and result.get('endDate') and result['startDate']>result['endDate']:raise ValueError('reversed dates')
    return result

def validate_patient(v):
    keys=('patientId','firstName','lastName','phone','dateOfBirth','zipCode')
    _strings(v,keys)
    try:date.fromisoformat(v['dateOfBirth'])
    except ValueError:raise ValueError('invalid patient date') from None
    if type(v.get('establishedPatient')) is not bool:raise ValueError('invalid patient field')
    return {k:v[k] for k in (*keys,'establishedPatient')}

def validate_provider(v):
    _strings(v,('providerId','name','specialty'))
    if v['specialty'] not in SPECIALTIES:raise ValueError('unsupported provider specialty')
    for key in ('locations','modalities'):
        if not isinstance(v.get(key),list) or not all(isinstance(x,str) and x for x in v[key]):raise ValueError('invalid provider field')
    if not set(v['locations'])<=LOCATIONS:raise ValueError('unsupported provider location')
    return {k:v[k] for k in ('providerId','name','specialty','locations','modalities')}

def validate_slot(v):
    _strings(v,('slotId','providerId','specialty','location','startTime'))
    if {'conflictOnBooking','daysFromToday','time'}&set(v):raise ValueError('fixture-only field')
    validate_criteria({'specialty':v['specialty'],'location':v['location']},True);_time(v['startTime'])
    if type(v.get('available')) is not bool:raise ValueError('invalid availability')
    return {k:v[k] for k in ('slotId','providerId','specialty','location','startTime','available')}

def validate_appointment(v):
    keys=('appointmentId','patientId','providerId','specialty','location','startTime','status')
    _strings(v,keys);validate_criteria({'specialty':v['specialty'],'location':v['location']},True);_time(v['startTime'])
    if v['status']!='scheduled':raise ValueError('not a scheduled appointment')
    return {k:v[k] for k in keys}

@dataclass(frozen=True)
class Proposal:
    session_id:str
    revision:int
    patient_id:str
    slot_id:str
    criteria:tuple
    slot_signature:tuple

@dataclass
class Conversation:
    session_id:str=field(default_factory=lambda:uuid4().hex)
    state:str='collecting'
    intent:str='unknown'
    fields:dict=field(default_factory=dict,repr=False)
    patient:dict|None=field(default=None,repr=False)
    candidates:list=field(default_factory=list,repr=False)
    slots:list=field(default_factory=list,repr=False)
    providers:list=field(default_factory=list,repr=False)
    proposal:Proposal|None=field(default=None,repr=False)
    completed:dict|None=field(default=None,repr=False)
    unknown:bool=False
    booking_effect:str='not_attempted'
    revision:int=0
    blocked_slots:set=field(default_factory=set,repr=False)
    identity_attempts:int=0
    policy_trace:list=field(default_factory=list,repr=False)


def recovery_context(c):
    """Local categorical support context; no identity values, delivery or effects."""
    fields=('phone','dob','zip','specialty','location','startDate','endDate')
    known=[key for key in fields if c.fields.get(key)]
    missing=(['zip'] if len(c.candidates)>1 and not c.patient else
             [key for key in ('phone','dob','specialty')
              if not c.fields.get(key) and not (c.patient and key in {'phone','dob'})])
    if c.intent=='provider_lookup':missing=[]
    effect='unknown' if c.unknown else 'confirmed' if c.completed else c.booking_effect
    if effect not in {'not_attempted','confirmed','rejected','unknown'}:effect='unknown'
    next_step=('reconcile_before_retry' if effect=='unknown' else
               'keep_confirmation' if effect=='confirmed' else
               'provide_missing_information' if missing else
               'confirm_current_proposal' if c.proposal else
               'choose_returned_option' if c.slots else 'contact_scheduling')
    return {'known':known,'missing':missing,
            'identity':'verified' if c.patient else 'ambiguous' if len(c.candidates)>1 else 'unverified',
            'booking':effect,'support_delivery':'not_sent','next_step':next_step}
