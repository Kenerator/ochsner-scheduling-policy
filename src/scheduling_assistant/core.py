"""Guarded scheduling transactions. Models and policy decisions never create consent."""
from datetime import date
import re,time
from .models import Conversation,Proposal,validate_criteria,validate_patient,validate_provider,validate_slot,validate_appointment
from .ports import IntentResult,TurnResult,ApiError

FIELDS={'phone','dob','zip','specialty','location','startDate','endDate','selection'}
YES={'yes','confirm','yes confirm','yes, confirm'}
NO={'no','cancel','do not book','stop'}
CRITERIA={'specialty','location','startDate','endDate'}

class Assistant:
    def __init__(self,api,intent,policy=None,event_sink=None):
        if policy is None:
            from .policy import PolicyEngine
            policy=PolicyEngine()
        self.api,self.intent,self.policy,self.event_sink=api,intent,policy,event_sink

    def _event(self,c,operation,outcome,reason='',elapsed=0,status=None):
        from .diagnostics import build_event
        event=build_event(session=c.session_id,intent=c.intent,state=c.state,
                          operation=operation,outcome=outcome,reason=reason,
                          elapsed=elapsed,status=status)
        if self.event_sink:self.event_sink(event)

    def _result(self,c,message,outcome='',options=None):
        return TurnResult(message,c.state,options or [],list(c.policy_trace),outcome)

    def _decide(self,c,action,*,request='scheduling',api='not_called',consent='missing',selection=None,model='valid'):
        identity='verified' if c.patient else ('multiple' if len(c.candidates)>1 else 'no_match' if c.identity_attempts else 'not_checked')
        criteria=self._criteria(c)
        ready=(action=='providers' or (action=='identify' and bool(c.fields.get('phone') and c.fields.get('dob'))) or bool(criteria.get('specialty')))
        current=self._proposal_valid(c)
        facts={'action':action,'request':request,'criteria':'supported' if ready else 'missing',
            'identity':identity,'slots':'returned' if c.slots else 'not_fetched',
            'selection':'returned_option' if selection is not None or current else 'missing',
            'proposal':'current' if current else ('stale' if c.proposal else 'missing'),
            'consent':consent,'api':api,'model':model}
        d=self.policy.evaluate(facts)
        # Only validated policy adapter supplies safe immutable metadata.
        c.policy_trace.append({**d.as_dict(),'facts':dict(facts)});c.policy_trace=c.policy_trace[-25:]
        return d.disposition=='proceed'

    @staticmethod
    def _criteria(c):return {k:v for k,v in c.fields.items() if k in CRITERIA}

    @staticmethod
    def _signature(slot):return tuple((k,slot[k]) for k in ('slotId','providerId','specialty','location','startTime','available'))

    def _proposal_valid(self,c):
        p=c.proposal
        if p is None or c.patient is None or p.session_id!=c.session_id or p.revision!=c.revision:return False
        if p.patient_id!=c.patient['patientId'] or p.criteria!=tuple(sorted(self._criteria(c).items())):return False
        return any(s['slotId']==p.slot_id and s['available'] is True and self._signature(s)==p.slot_signature for s in c.slots)

    def _call(self,c,operation,fn):
        t=time.monotonic()
        try:value=fn()
        except ApiError as e:
            self._event(c,operation,'unknown' if e.unknown else 'failed',e.code,time.monotonic()-t,e.status)
            raise
        self._event(c,operation,'completed',elapsed=time.monotonic()-t)
        return value

    def handle(self,c,text):
        start=time.monotonic();diagnostic={};before=c.state
        result=self._handle_errors(c,text,diagnostic)
        category=('unknown' if result.outcome=='unknown' else 'failed' if result.outcome in {'failed','no_match','no_availability','conflict','guidance','stale'} else 'completed')
        if result.outcome=='guidance' and 'reason' not in diagnostic:
            diagnostic['reason']='identity_unresolved' if c.identity_attempts and not c.patient else 'policy_denied'
        reason=diagnostic.get('reason',{'no_match':'no_match','no_availability':'no_availability','conflict':'slot_taken','unknown':'unknown_write','stale':'stale_proposal'}.get(result.outcome,''))
        from .diagnostics import build_event
        if self.event_sink:self.event_sink(build_event(session=c.session_id,intent=c.intent,state=c.state,from_state=before,to_state=c.state,operation='turn',outcome=category,reason=reason,elapsed=time.monotonic()-start))
        return result

    def _handle_errors(self,c,text,diagnostic):
        c.policy_trace=[]
        try:return self._handle(c,text,diagnostic)
        except ApiError as e:
            diagnostic['reason']=e.code
            if e.unknown:
                c.unknown=True;c.state='unknown';c.proposal=None
                self._decide(c,'report',api='unknown_write')
                return self._result(c,'The booking outcome is unknown. Contact the scheduling team through your usual channel to reconcile it before trying again. Resetting this conversation or the mock does not establish what happened.','unknown')
            c.proposal=None;c.state='guidance'
            if e.status==409:
                return self._result(c,'That slot was taken; no booking was confirmed. Choose another returned option, or contact the scheduling team.','conflict')
            if e.code in {'invalid_model_output','model_unavailable'}:
                self._decide(c,'report',model='malformed' if e.code=='invalid_model_output' else 'unavailable')
                return self._result(c,'I could not safely interpret that message. No scheduling action was taken for it. Try a clearer request or contact the scheduling team.','failed')
            self._decide(c,'report',api='unavailable')
            return self._result(c,'The scheduling service could not complete the request. No successful booking or queued handoff is confirmed. Contact the scheduling team through your usual channel.','failed')
        except ValueError:
            diagnostic['reason']='invalid_parameter'
            c.proposal=None;c.state='guidance'
            return self._result(c,'The request or service data could not be validated. No confirmed booking can be reported. Check the information or contact the scheduling team.','failed')

    def _handle(self,c,text,diagnostic):
        if not isinstance(text,str) or len(text)>4000:return self._result(c,'Use a short scheduling request. No action was taken.','failed')
        literal=text.strip().lower().rstrip('.!')
        if c.unknown:
            self._decide(c,'report',api='unknown_write')
            return self._result(c,'The previous booking outcome is unknown. Contact scheduling to reconcile before retrying; reset is not reconciliation.','unknown')
        if literal=='reset':
            c.__dict__.update(Conversation().__dict__)
            return self._result(c,'New conversation. Mock bookings are unchanged. How can I help with provider lookup or booking?')
        if c.completed:
            return self._result(c,self._booked_message(c.completed)+' This is the existing result; no new booking was sent. Use reset for a new conversation.','booked')
        needed=['zip'] if c.state=='clarifying_identity' else [k for k in ('phone','dob','specialty') if not c.fields.get(k)]
        result=self.intent.interpret(text,{'state':c.state,'intent':c.intent,'needed':needed})
        if not isinstance(result,IntentResult) or result.intent not in {'provider_lookup','book','human_help','medical_advice','unsupported','unknown'} or not isinstance(result.fields,dict) or set(result.fields)-FIELDS:
            raise ApiError('invalid_model_output')
        if any(not isinstance(v,str) for v in result.fields.values()):raise ApiError('invalid_model_output')
        if result.intent in {'medical_advice','human_help','unsupported'}:
            c.intent=result.intent
            request={'human_help':'human_requested','medical_advice':'medical_advice','unsupported':'unsupported'}[result.intent]
            diagnostic['reason']=request
            self._decide(c,'report',request=request);c.proposal=None;c.state='guidance'
            msg='I cannot provide medical advice or triage. Contact a healthcare professional through your usual channel.' if result.intent=='medical_advice' else 'That request needs human assistance. Contact the scheduling team through your usual channel; no handoff has been queued.'
            return self._result(c,msg,'guidance')
        changes={k:v for k,v in result.fields.items() if k!='selection' and c.fields.get(k)!=v}
        if changes:
            c.revision+=1;c.proposal=None;c.slots=[];c.providers=[];c.blocked_slots.clear();c.state='collecting'
            if {'phone','dob'}&set(changes):c.patient=None;c.candidates=[];c.identity_attempts=0
            c.fields.update(changes)
        if result.intent in {'provider_lookup','book'}:
            if result.intent!=c.intent:c.proposal=None;c.state='collecting'
            c.intent=result.intent
        if c.intent=='unknown':return self._result(c,'Would you like to find providers or book an appointment?')
        validate_criteria(self._criteria(c))
        if c.intent=='provider_lookup':
            if not self._decide(c,'providers'):return self._result(c,'The policy decision stopped this provider request. Contact scheduling.','guidance')
            criteria={k:v for k,v in self._criteria(c).items() if k in {'specialty','location'}}
            rows=self._call(c,'providers',lambda:self.api.providers(criteria));rows=[validate_provider(x) for x in rows]
            rows=[x for x in rows if (not criteria.get('specialty') or x['specialty']==criteria['specialty']) and (not criteria.get('location') or criteria['location'] in x['locations'])]
            c.state='providers'
            return self._result(c,'Providers from the scheduling service:\n'+'\n'.join(f"- {x['name']} — {x['specialty']}, {', '.join(x['locations'])}" for x in rows) if rows else 'No providers matched. Change the search or contact scheduling.',options=rows)
        if literal in NO:
            c.proposal=None;c.state='offering' if c.slots else 'collecting'
            return self._result(c,'No booking was sent. Choose a returned option or change your search.')
        # Strict local syntax validation complements the untrusted interpreter.
        if c.fields.get('phone') and not re.fullmatch(r'[+0-9(). -]{5,24}',c.fields['phone']):
            c.fields.pop('phone');return self._result(c,'Please provide a valid phone number.')
        if c.fields.get('dob'):
            try:
                if date.fromisoformat(c.fields['dob']).isoformat()!=c.fields['dob']:raise ValueError()
            except ValueError:
                c.fields.pop('dob');return self._result(c,'Please provide date of birth as YYYY-MM-DD.')
        if c.patient is None:
            if c.candidates:
                zip_value=result.fields.get('zip')
                if not zip_value:return self._result(c,'Please provide your ZIP code privately to clarify the match.','clarification')
                c.identity_attempts+=1
                matches=[x for x in c.candidates if x['zipCode']==zip_value]
                if len(matches)!=1:
                    c.state='guidance';c.candidates=[]
                    return self._result(c,'Identity is still unclear. Contact scheduling through your usual channel. No patient-specific action was taken.','guidance')
                c.patient=matches[0];c.candidates=[]
            else:
                missing=[k for k in ('phone','dob') if not c.fields.get(k)]
                if missing:return self._result(c,'To identify your synthetic patient record, provide '+('phone number and date of birth (YYYY-MM-DD).' if len(missing)==2 else ('phone number.' if missing[0]=='phone' else 'date of birth (YYYY-MM-DD).')))
                if c.identity_attempts and not {'phone','dob'}&set(changes):
                    return self._result(c,'No unique patient was found. Check your phone/date of birth or contact scheduling. No patient-specific action was taken.','guidance')
                if not self._decide(c,'identify'):return self._result(c,'Policy stopped identification; contact scheduling.','guidance')
                c.identity_attempts+=1
                matches=self._call(c,'patient_search',lambda:self.api.patient_matches(c.fields['phone'],c.fields['dob']))
                matches=[validate_patient(x) for x in matches]
                if any(x['phone']!=c.fields['phone'] or x['dateOfBirth']!=c.fields['dob'] for x in matches):raise ApiError('malformed_response')
                if not matches:
                    c.state='guidance';self._decide(c,'report',api='ok');return self._result(c,'No patient matched. Check your phone/date of birth or contact scheduling through your usual channel. No patient-specific action was taken.','no_match')
                if len(matches)>1:
                    c.candidates=matches;c.state='clarifying_identity';self._decide(c,'report',api='ok')
                    return self._result(c,'More than one record matched. Please provide your ZIP code privately; I will not display candidate details.','clarification')
                c.patient=matches[0]
        if not c.fields.get('specialty'):return self._result(c,'Which specialty: primary care or dermatology?')
        criteria=validate_criteria(self._criteria(c),True)
        # A newly extracted choice invalidates the displayed proposal even on a yes turn.
        if result.fields.get('selection') and c.proposal:
            c.proposal=None;c.revision+=1;c.state='offering'
        if c.proposal and literal in YES:return self._book(c)
        if c.proposal:return self._result(c,self._proposal_message(c)+' Reply yes to confirm or no to decline.')
        if not c.slots:
            if not c.providers:
                if not self._decide(c,'providers'):return self._result(c,'Policy stopped provider lookup; contact scheduling.','guidance')
                provider_criteria={k:v for k,v in criteria.items() if k in {'specialty','location'}}
                c.providers=[validate_provider(x) for x in self._call(c,'providers',lambda:self.api.providers(provider_criteria))]
            if not self._decide(c,'availability'):return self._result(c,'Policy stopped availability; contact scheduling.','guidance')
            rows=self._call(c,'availability',lambda:self.api.availability(c.patient['patientId'],criteria))
            c.slots=[validate_slot(x) for x in rows]
            c.slots=[x for x in c.slots if x['available'] is True and x['slotId'] not in c.blocked_slots and x['specialty']==criteria['specialty'] and (not criteria.get('location') or x['location']==criteria['location'])]
            if not c.slots:
                c.state='guidance';return self._result(c,'No available slots matched. Change the search or contact scheduling; no booking was sent.','no_availability')
            c.state='offering'
            return self._result(c,self._options(c),options=list(c.slots))
        selection=result.fields.get('selection')
        if selection:
            idx=0 if selection.lower() in {'earliest','first'} else (int(selection)-1 if selection.isdigit() else -1)
            if idx<0 or idx>=len(c.slots):return self._result(c,'Choose a numbered option from the displayed scheduling results. No booking was sent.',options=list(c.slots))
            slot=c.slots[idx]
            if not self._decide(c,'propose',api='ok',selection=slot):return self._result(c,'Policy stopped that proposal; choose a valid returned option.','guidance')
            c.proposal=Proposal(c.session_id,c.revision,c.patient['patientId'],slot['slotId'],tuple(sorted(criteria.items())),self._signature(slot));c.state='awaiting_confirmation'
            return self._result(c,self._proposal_message(c)+' Reply yes to confirm this exact appointment or no to decline.',options=[dict(slot)])
        return self._result(c,self._options(c),options=list(c.slots))

    @staticmethod
    def _provider_name(c,provider_id):
        return next((p['name'] for p in c.providers if p['providerId']==provider_id),'provider '+provider_id)

    def _options(self,c):
        return 'Available appointments from the scheduling service:\n'+'\n'.join(f"{i}. {s['specialty']} — {s['location']} — {s['startTime']} ({self._provider_name(c,s['providerId'])})" for i,s in enumerate(c.slots,1))+'\nChoose a numbered option. Nothing is booked yet.'

    def _proposal_message(self,c):
        if not self._proposal_valid(c):return 'The previous proposal is stale. Choose again; no booking was sent.'
        slot=next(s for s in c.slots if s['slotId']==c.proposal.slot_id)
        return f"Confirm for {c.patient['firstName']} {c.patient['lastName']}: {slot['specialty']} at {slot['location']}, {slot['startTime']}, {self._provider_name(c,slot['providerId'])}."

    def _book(self,c):
        # This guard remains authoritative even if an engine is replaced or defective.
        if not self._proposal_valid(c) or c.unknown or c.completed:
            c.proposal=None;c.state='offering';return self._result(c,'That proposal is no longer current. Choose again; nothing was sent.','stale')
        if not self._decide(c,'book',consent='current_explicit'):
            return self._result(c,'The policy decision stopped booking. No booking was sent.','guidance')
        slot=next(s for s in c.slots if s['slotId']==c.proposal.slot_id)
        pid,sid=c.proposal.patient_id,c.proposal.slot_id
        c.state='booking'
        try:appointment=self._call(c,'book',lambda:self.api.book(pid,sid))
        except ApiError as e:
            if e.status==409:
                c.blocked_slots.add(sid);c.slots=[s for s in c.slots if s['slotId']!=sid];c.proposal=None
                self._decide(c,'report',api='conflict_409')
            raise
        try:
            appointment=validate_appointment(appointment)
            if appointment['patientId']!=pid or any(appointment[k]!=slot[k] for k in ('providerId','specialty','location','startTime')):raise ValueError()
        except (ValueError,TypeError,KeyError):raise ApiError('unknown_write',unknown=True) from None
        c.completed=appointment;c.proposal=None;c.state='completed'
        self._decide(c,'report',api='created_201')
        return self._result(c,self._booked_message(appointment),'booked')

    @staticmethod
    def _booked_message(a):return f"Booked: {a['specialty']} at {a['location']}, {a['startTime']}. Appointment {a['appointmentId']}."
