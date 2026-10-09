"""Diagnostics are bounded metadata, including on controlled failure paths."""
import contextlib
import io
import json
import math
import unittest
from scheduling_assistant.diagnostics import build_event
from scheduling_assistant.core import Assistant
from scheduling_assistant.models import Conversation
from scheduling_assistant.ports import ApiError,IntentResult
from test_scheduling_core import API,Proceed,ScriptIntent

class DiagnosticFactoryTests(unittest.TestCase):
    def test_valid_event_preserves_only_documented_metadata(self):
        event=build_event(session='a'*32,intent='book',state='unknown',operation='book',outcome='unknown',reason='unknown_write',elapsed=.125,status=503,from_state='booking',to_state='unknown')
        self.assertEqual(event,{'session':'a'*32,'intent':'book','state':'unknown','operation':'book','outcome':'unknown','reason':'unknown_write','elapsedMs':125.0,'status':503,'fromState':'booking','toState':'unknown'})
    def test_untrusted_values_are_replaced_not_stringified(self):
        class Sensitive:
            def __str__(self):raise AssertionError('must not stringify arbitrary object')
        for value in ('SENSITIVE-SECRET',{'phone':'SENSITIVE-PHONE'},['SENSITIVE-DOB'],Sensitive()):
            event=build_event(session=value,intent=value,state=value,operation=value,outcome=value,reason=value,elapsed=value,status=value,from_state=value,to_state=value)
            self.assertNotIn('SENSITIVE',json.dumps(event))
            self.assertEqual(set(event),{'session','intent','state','operation','outcome','reason','elapsedMs'})
    def test_nonfinite_negative_and_boolean_timings_are_safe(self):
        for value in (float('inf'),float('nan'),-1,True,None):
            event=build_event(session='a'*32,intent='book',state='booking',operation='book',outcome='attempted',elapsed=value,status=True)
            self.assertEqual(event['elapsedMs'],0)
            self.assertNotIn('status',event)
            self.assertTrue(math.isfinite(event['elapsedMs']))
    def test_no_arbitrary_payload_extension(self):
        with self.assertRaises(TypeError):
            build_event(session='a'*32,intent='book',state='booking',operation='book',outcome='attempted',phone='SENSITIVE-PHONE')

class CoreDiagnosticsTests(unittest.TestCase):
    def run_case(self,case):
        api=API()
        # Service and utterance sentinels must never enter events or stderr.
        api.matches=[dict(api.matches[0],patientId='SENSITIVE-PATIENT',firstName='SENSITIVE-NAME',zipCode='70112')]
        api.appointment.update(patientId='SENSITIVE-PATIENT',appointmentId='SENSITIVE-APPOINTMENT')
        if case=='no_match':api.matches=[]
        if case=='outage':
            def unavailable(phone,dob):raise ApiError('downstream_unavailable',status=503)
            api.patient_matches=unavailable
        if case=='unknown':api.error=ApiError('unknown_write',unknown=True)
        intent=ScriptIntent(IntentResult('book',{'phone':'555-0101','dob':'1985-04-12','zip':'70112','specialty':'primary_care','location':'downtown'}),IntentResult('book',{'selection':'1'}))
        events=[];output=io.StringIO()
        a=Assistant(api,intent,policy=Proceed(),event_sink=events.append);c=Conversation()
        with contextlib.redirect_stdout(output),contextlib.redirect_stderr(output):
            result=a.handle(c,'SENSITIVE-UTTERANCE SENSITIVE-KEY')
            if case in {'success','unknown'}:
                a.handle(c,'1');result=a.handle(c,'yes')
        rendered=json.dumps(events)+output.getvalue()
        for private in ('SENSITIVE','555-0101','1985-04-12','70112','slot_x','apt_x'):
            self.assertNotIn(private,rendered)
        self.assertTrue(events)
        self.assertTrue(all(set(e)<= {'session','intent','state','operation','outcome','reason','elapsedMs','status','fromState','toState'} for e in events))
        return result,events
    def test_success_has_actual_book_completion(self):
        result,events=self.run_case('success')
        self.assertEqual(result.outcome,'booked')
        self.assertTrue(any(e['operation']=='book' and e['outcome']=='completed' for e in events))
    def test_no_match_has_no_private_read_or_write(self):
        result,events=self.run_case('no_match')
        self.assertEqual(result.outcome,'no_match')
        self.assertEqual(events[-1]['operation'],'turn')
        self.assertEqual(events[-1]['outcome'],'failed')
        self.assertEqual(events[-1]['reason'],'no_match')
        self.assertFalse(any(e['operation'] in {'availability','book'} for e in events))
    def test_outage_has_fixed_reason_and_status(self):
        result,events=self.run_case('outage')
        self.assertEqual(result.outcome,'failed')
        self.assertEqual(events[-1]['outcome'],'failed')
        self.assertEqual(events[-1]['reason'],'downstream_unavailable')
        self.assertTrue(any(e['reason']=='downstream_unavailable' and e['status']==503 and e['outcome']=='failed' for e in events))
    def test_unknown_write_is_reported_as_unknown(self):
        result,events=self.run_case('unknown')
        self.assertEqual(result.outcome,'unknown')
        self.assertEqual(events[-1]['outcome'],'unknown')
        self.assertEqual(events[-1]['reason'],'unknown_write')
        self.assertTrue(any(e['operation']=='book' and e['outcome']=='unknown' and e['reason']=='unknown_write' for e in events))
