"""Integrated controller + actual ZEN + actual supplied HTTP API acceptance flows."""
import unittest
from urllib.request import urlopen
from scheduling_assistant.adapters.http import HttpSchedulingAPI
from scheduling_assistant.core import Assistant
from scheduling_assistant.models import Conversation
from scheduling_assistant.ports import IntentResult
from scheduling_test_support import supplied_server
from test_scheduling_core import ScriptIntent

BOOK = {'phone':'555-0101','dob':'1985-04-12','specialty':'primary_care','location':'downtown'}

class SchedulingAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.server = supplied_server()
        self.base,self.requests = self.server.__enter__()
        self.addCleanup(self.server.__exit__,None,None,None)

    def assistant(self,fields=None,api=None,intent='book'):
        self.intent = ScriptIntent(IntentResult(intent,dict(BOOK if fields is None else fields)))
        self.events = []
        self.a = Assistant(api or HttpSchedulingAPI(self.base),self.intent,event_sink=self.events.append)
        self.c = Conversation()
        return self.turn('Start request')

    def turn(self,text,fields=None,intent='unknown'):
        if fields is not None:
            self.intent.values.append(IntentResult(intent,fields))
        return self.a.handle(self.c,text)

    def writes(self): return [r for r in self.requests if r['method']=='POST']

    def assert_policy_used(self,result):
        self.assertTrue(result.policy)
        self.assertTrue(all(row['rule'] and row['sources'] for row in result.policy))

    def test_provider_lookup_is_public_and_uses_actual_policy_and_http(self):
        result = self.assistant({'specialty':'primary_care','location':'downtown'},intent='provider_lookup')
        self.assertTrue(result.options)
        self.assertIsNone(self.c.patient)
        self.assertEqual([r['path'] for r in self.requests],['/providers'])
        self.assert_policy_used(result)

    def test_multiturn_identity_then_selection_then_exact_201_and_replay(self):
        result = self.assistant({'specialty':'primary_care'})
        self.assertEqual(self.requests,[])
        self.assertIn('phone',result.message)
        self.turn('555-0101',{'phone':'555-0101'},'book')
        self.assertEqual(self.requests,[])
        options = self.turn('1985-04-12',{'dob':'1985-04-12'},'book')
        self.assertTrue(options.options)
        slot = options.options[0]
        proposed = self.turn('1',{'selection':'1'},'book')
        self.assertIn(slot['startTime'],proposed.message)
        self.assertEqual(self.writes(),[])
        self.assert_policy_used(proposed)
        booked = self.turn('yes')
        self.assertEqual(booked.outcome,'booked')
        self.assertEqual(self.writes()[0]['body'],{'patientId':'pat_1001','slotId':slot['slotId'],'confirmed':True})
        self.assertEqual(self.c.completed['startTime'],slot['startTime'])
        self.assertEqual(self.c.completed['providerId'],slot['providerId'])
        self.assert_policy_used(booked)
        self.assertEqual(self.turn('yes').outcome,'booked')
        self.assertEqual(len(self.writes()),1)
        diagnostics = str(self.events)
        for private in ('555-0101','1985-04-12','70112','Maya','pat_1001',slot['slotId']):
            self.assertNotIn(private,diagnostics)

    def test_no_match_never_reads_private_availability(self):
        result = self.assistant(dict(BOOK,phone='555-9999'))
        self.assertEqual(result.outcome,'no_match')
        self.assertIn('R-REPORT-NO-MATCH',[x['rule'] for x in result.policy])
        self.turn('yes')
        self.assertEqual([r['path'] for r in self.requests],['/patients/search'])
        self.assertEqual(self.writes(),[])

    def test_duplicate_identity_is_private_then_zip_resolves_locally(self):
        result = self.assistant(dict(BOOK,phone='555-0130',dob='1978-09-22'))
        self.assertEqual(result.outcome,'clarification')
        self.assertIn('R-REPORT-MULTIPLE',[x['rule'] for x in result.policy])
        for private in ('Avery','Patel','70115','70005','pat_1003','pat_1004'):
            self.assertNotIn(private,result.message+str(result.options))
        self.assertEqual([r['path'] for r in self.requests],['/patients/search'])
        options = self.turn('70005',{'zip':'70005'},'book')
        self.assertEqual(self.c.patient['patientId'],'pat_1004')
        self.assertTrue(options.options)
        self.assertEqual([r['path'] for r in self.requests],['/patients/search','/providers','/availability'])
        self.assertNotIn('zip',self.requests[0]['query'].lower())
        self.assertNotIn('70005',self.requests[0]['query'])

    def test_unresolved_duplicate_does_not_progress_or_retry_identity(self):
        self.assistant(dict(BOOK,phone='555-0130',dob='1978-09-22'))
        result = self.turn('99999',{'zip':'99999'},'book')
        self.assertEqual(result.outcome,'guidance')
        self.assertIsNone(self.c.patient)
        self.turn('yes')
        self.assertEqual([r['path'] for r in self.requests],['/patients/search'])
        self.assertEqual(self.writes(),[])

    def test_no_availability_is_truthful_and_does_not_book(self):
        result = self.assistant(dict(BOOK,specialty='dermatology'))
        self.assertEqual(result.outcome,'no_availability')
        self.assertEqual(result.options,[])
        self.assertIsNone(self.c.proposal)
        self.assertEqual(self.writes(),[])

    def test_outage_preserves_scenario_and_has_no_claimed_handoff(self):
        result = self.assistant(api=HttpSchedulingAPI(self.base,scenario='api_failure'))
        self.assertEqual(result.outcome,'failed')
        self.assertIn('No successful booking or queued handoff is confirmed',result.message)
        self.assertEqual([r['scenario'] for r in self.requests],['api_failure'])
        self.assertEqual(self.writes(),[])

    def test_real_permanent_conflict_requires_fresh_choice_and_confirmation(self):
        options = self.assistant()
        conflict_index = next(i for i,s in enumerate(options.options,1) if s['slotId']=='slot_conflict_001')
        self.turn(str(conflict_index),{'selection':str(conflict_index)},'book')
        conflict = self.turn('yes')
        self.assertEqual(conflict.outcome,'conflict')
        self.assertIsNone(self.c.proposal)
        self.assertIn('slot_conflict_001',self.c.blocked_slots)
        options = self.turn('yes')
        self.assertEqual(len(self.writes()),1)
        self.assertTrue(options.options)
        self.assertNotIn('slot_conflict_001',[s['slotId'] for s in options.options])
        fresh = options.options[0]
        self.turn('1',{'selection':'1'},'book')
        self.assertEqual(len(self.writes()),1)
        booked = self.turn('yes')
        self.assertEqual(booked.outcome,'booked')
        self.assertEqual(len(self.writes()),2)
        self.assertEqual(self.writes()[-1]['body']['slotId'],fresh['slotId'])

    def test_refusal_clears_consent_before_another_selection(self):
        options = self.assistant()
        self.turn('1',{'selection':'1'},'book')
        self.turn('no')
        self.assertIsNone(self.c.proposal)
        self.turn('yes')
        self.assertEqual(self.writes(),[])
        self.turn('2',{'selection':'2'},'book')
        self.assertEqual(self.writes(),[])
        self.assertEqual(self.turn('yes').outcome,'booked')
        self.assertEqual(self.writes()[0]['body']['slotId'],options.options[1]['slotId'])

    def test_changed_selection_replaces_proposal_and_requires_fresh_yes(self):
        options = self.assistant()
        self.turn('1',{'selection':'1'},'book')
        changed = self.turn('2',{'selection':'2'},'book')
        self.assertEqual(self.writes(),[])
        self.assertEqual(self.c.proposal.slot_id,options.options[1]['slotId'])
        self.assertIn(options.options[1]['startTime'],changed.message)
        self.assertEqual(self.turn('yes').outcome,'booked')
        self.assertEqual(self.writes()[0]['body']['slotId'],options.options[1]['slotId'])

    def test_interrupted_post_freezes_even_after_reset_or_repeated_yes(self):
        attempts = []
        def transport(request,timeout):
            if request.method=='POST':
                attempts.append(request)
                raise TimeoutError('sensitive transport content')
            return urlopen(request,timeout=timeout)
        self.assistant(api=HttpSchedulingAPI(self.base,transport=transport))
        self.turn('1',{'selection':'1'},'book')
        self.assertEqual(self.turn('yes').outcome,'unknown')
        self.assertEqual(self.turn('yes').outcome,'unknown')
        self.assertEqual(self.turn('reset').outcome,'unknown')
        self.assertEqual(self.turn('1',{'selection':'1'},'book').outcome,'unknown')
        self.assertTrue(self.c.unknown)
        self.assertEqual(len(attempts),1)
        self.assertEqual(self.writes(),[])

if __name__ == '__main__': unittest.main()
