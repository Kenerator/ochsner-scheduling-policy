"""Transaction tests catch missing identity, stale assent and uncertain-write retries."""
import copy,unittest
from types import SimpleNamespace
from scheduling_assistant.core import Assistant
from scheduling_assistant.models import Conversation,Proposal
from scheduling_assistant.ports import IntentResult,ApiError
from test_scheduling_models import PATIENT,PROVIDER,SLOT,APPOINTMENT

class ScriptIntent:
    def __init__(self,*values):self.values=list(values)
    def interpret(self,text,context):
        value=self.values.pop(0) if self.values else IntentResult('unknown',{})
        if isinstance(value,Exception):raise value
        return value
class Proceed:
    def evaluate(self,facts):
        return SimpleNamespace(disposition='proceed',reason='test_boundary',rule='TEST',sources=(),as_dict=lambda:{'disposition':'proceed','reason':'test_boundary','rule':'TEST','sources':[]})
class Deny(Proceed):
    def evaluate(self,facts):
        d=super().evaluate(facts);d.disposition='stop';d.reason='policy_denied';return d
class API:
    def __init__(self):self.calls=[];self.matches=[dict(PATIENT)];self.offers=[dict(SLOT)];self.error=None;self.appointment=dict(APPOINTMENT)
    def providers(self,criteria):self.calls.append(('providers',copy.deepcopy(criteria)));return [dict(PROVIDER)]
    def patient_matches(self,phone,dob):self.calls.append(('patients',));return copy.deepcopy(self.matches)
    def availability(self,patient_id,criteria):self.calls.append(('availability',));return copy.deepcopy(self.offers)
    def book(self,patient_id,slot_id):
        self.calls.append(('book',patient_id,slot_id))
        if self.error:raise self.error
        return dict(self.appointment)

def booking(api=None,policy=None):
    api=api or API();intent=ScriptIntent(IntentResult('book',{'phone':'555-0101','dob':'1985-04-12','specialty':'primary_care','location':'downtown'}),IntentResult('book',{'selection':'1'}))
    a=Assistant(api,intent,policy=policy or Proceed());c=Conversation()
    first=a.handle(c,'Book primary care downtown with my identity');second=a.handle(c,'1')
    return a,c,api,first,second

class CoreTests(unittest.TestCase):
    def test_public_lookup_never_requires_identity(self):
        api=API();a=Assistant(api,ScriptIntent(IntentResult('provider_lookup',{'specialty':'primary_care','location':'downtown'})),policy=Proceed())
        r=a.handle(Conversation(),'Which primary care providers are downtown?')
        self.assertIn('Synthetic Doctor',r.message);self.assertEqual([x[0] for x in api.calls],['providers'])
    def test_no_booking_before_exact_proposal_and_current_yes_or_on_replay(self):
        a,c,api,first,proposal=booking()
        self.assertIn(PROVIDER['name'],first.message)
        self.assertIn(PROVIDER['name'],proposal.message)
        self.assertIn(SLOT['startTime'],first.message);self.assertEqual(c.state,'awaiting_confirmation')
        self.assertNotIn('book',[x[0] for x in api.calls]);self.assertIn(SLOT['startTime'],proposal.message)
        r=a.handle(c,'yes');self.assertEqual(r.outcome,'booked')
        a.handle(c,'yes');self.assertEqual([x[0] for x in api.calls].count('book'),1)
    def test_changed_preferences_invalidate_proposal_even_with_yes(self):
        a,c,api,_,_=booking();a.intent=ScriptIntent(IntentResult('book',{'location':'uptown'}))
        a.handle(c,'yes but change to uptown')
        self.assertIsNone(c.proposal);self.assertNotIn('book',[x[0] for x in api.calls])
    def test_unrecognized_change_or_model_failure_revokes_pending_consent_context(self):
        for interpretation in (IntentResult('book',{}), ApiError('model_unavailable')):
            with self.subTest(interpretation=type(interpretation).__name__):
                a,c,api,_,_=booking()
                revision=c.revision
                a.intent=ScriptIntent(interpretation,IntentResult('book',{}))
                a.handle(c,'2')
                self.assertIsNone(c.proposal)
                self.assertGreater(c.revision,revision)
                a.handle(c,'yes')
                self.assertNotIn('book',[call[0] for call in api.calls])

    def test_oversized_intervening_message_revokes_pending_proposal(self):
        a,c,api,_,_=booking()
        a.handle(c,'2'+' '*4000)
        self.assertIsNone(c.proposal)
        a.handle(c,'yes')
        self.assertNotIn('book',[call[0] for call in api.calls])

    def test_changed_choice_requests_selection_without_patient_values_in_model_context(self):
        a,c,api,_,_=booking()
        contexts=[]
        class Capture:
            def interpret(self,text,context):
                contexts.append(context)
                return IntentResult('book',{})
        a.intent=Capture()
        a.handle(c,'2')
        self.assertEqual(contexts,[{'state':'offering','intent':'book','needed':['selection']}])

    def test_local_recovery_context_distinguishes_information_and_real_effects(self):
        from scheduling_assistant.models import recovery_context
        api=API();c=Conversation()
        before=list(api.calls)
        initial=recovery_context(c)
        self.assertEqual(initial['missing'],['phone','dob','specialty'])
        self.assertEqual(initial['booking'],'not_attempted')
        self.assertEqual(initial['support_delivery'],'not_sent')
        self.assertEqual(api.calls,before)
        for error,effect in [(None,'confirmed'),(ApiError('slot_taken',status=409),'rejected'),(ApiError('unknown_write',unknown=True),'unknown')]:
            a,c,api,_,_=booking();api.error=error
            a.handle(c,'yes');calls=list(api.calls)
            context=recovery_context(c)
            self.assertEqual(context['booking'],effect)
            self.assertEqual(context['missing'],[])
            self.assertEqual(api.calls,calls)
            for private in ['555-0101','1985-04-12','Synthetic Person','pat_x','slot_x']:
                self.assertNotIn(private,str(context))
            if effect=='unknown':self.assertEqual(context['next_step'],'reconcile_before_retry')

    def test_foreign_proposal_and_forged_engine_proceed_cannot_book(self):
        a,c,api,_,_=booking();p=c.proposal
        c.proposal=Proposal('foreign',p.revision,p.patient_id,p.slot_id,p.criteria,p.slot_signature)
        a.handle(c,'yes');self.assertNotIn('book',[x[0] for x in api.calls])
        bare=Conversation();a.handle(bare,'yes');self.assertNotIn('book',[x[0] for x in api.calls])
    def test_policy_denial_blocks_actual_proposed_call(self):
        api=API();a=Assistant(api,ScriptIntent(IntentResult('provider_lookup',{})),policy=Deny())
        a.handle(Conversation(),'providers');self.assertEqual(api.calls,[])
    def test_no_match_and_duplicate_candidates_are_private(self):
        api=API();api.matches=[];a,c,api,first,_=booking(api)
        self.assertNotIn('availability',[x[0] for x in api.calls]);self.assertNotIn('Synthetic Person',first.message)
        api=API();api.matches=[dict(PATIENT,zipCode='11111'),dict(PATIENT,patientId='pat_other',zipCode='22222')]
        a,c,api,first,_=booking(api)
        self.assertIn('ZIP',first.message);self.assertNotIn('11111',first.message);self.assertNotIn('22222',first.message)
        a.intent=ScriptIntent(IntentResult('book',{'zip':'22222'}));a.handle(c,'22222')
        self.assertEqual(c.patient['patientId'],'pat_other');self.assertIn('availability',[x[0] for x in api.calls])
    def test_unknown_write_freezes_booking_and_reset_is_not_reconciliation(self):
        a,c,api,_,_=booking();api.error=ApiError('unknown_write',unknown=True)
        r=a.handle(c,'yes');self.assertEqual(r.outcome,'unknown')
        a.handle(c,'yes');a.handle(c,'reset');a.handle(c,'yes')
        self.assertTrue(c.unknown);self.assertEqual([x[0] for x in api.calls].count('book'),1)
    def test_conflict_invalidates_choice_without_auto_alternate_booking(self):
        a,c,api,_,_=booking();api.error=ApiError('slot_taken',status=409)
        r=a.handle(c,'yes');self.assertNotEqual(r.outcome,'booked');self.assertIsNone(c.proposal)
        self.assertIn(SLOT['slotId'],c.blocked_slots);a.handle(c,'yes')
        self.assertEqual([x[0] for x in api.calls].count('book'),1)
    def test_mismatched_success_is_unknown_not_booked(self):
        a,c,api,_,_=booking();api.appointment['providerId']='other'
        self.assertEqual(a.handle(c,'yes').outcome,'unknown')
    def test_malformed_interpretation_or_medical_advice_makes_no_calls(self):
        for value in [ApiError('invalid_model_output'),IntentResult('medical_advice',{}),IntentResult('book',{'patientId':'invented','confirmed':'true'})]:
            api=API();a=Assistant(api,ScriptIntent(value),policy=Proceed());a.handle(Conversation(),'test')
            self.assertEqual(api.calls,[])
    def test_sensitive_values_do_not_enter_diagnostics(self):
        events=[];a,c,api,_,_=booking();a.event_sink=events.append;a.handle(c,'yes')
        text=str(events)
        for x in ['555-0101','1985-04-12','70112','pat_x','slot_x','apt_x','Synthetic Person']:
            self.assertNotIn(x,text)
        self.assertTrue(events)
