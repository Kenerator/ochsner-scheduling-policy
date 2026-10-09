"""Thin UI callbacks exercise the actual guarded core, without browser effects."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from scheduling_assistant.core import Assistant
from scheduling_assistant.ports import IntentResult,TurnResult
from test_scheduling_core import API,ScriptIntent

ROOT=Path(__file__).resolve().parents[1]

class SchedulingUITests(unittest.TestCase):
    def setUp(self):
        path=ROOT/'app.py'
        self.assertTrue(path.exists(),'Required thin Marimo app is not implemented')
        spec=importlib.util.spec_from_file_location('scheduling_policy_ui',path)
        self.ui=importlib.util.module_from_spec(spec)
        sys.modules[spec.name]=self.ui
        spec.loader.exec_module(self.ui)

    def session(self,*intents):
        api=API()
        core=Assistant(api,ScriptIntent(*intents))
        session=self.ui.UISession(assistant=core,environ={'SCHEDULING_INTENT_MODE':'offline'})
        return session,api

    def test_render_and_empty_form_events_do_not_execute_core(self):
        session,api=self.session(IntentResult('provider_lookup',{'specialty':'primary_care'}))
        results=[];callback=self.ui.submit_callback(session,results.append)
        callback(None);callback('  ')
        for _ in range(4):self.ui.view_html(session.view())
        self.assertEqual(api.calls,[])
        self.assertEqual(results,[])
        callback('Find primary care providers')
        self.assertEqual([x[0] for x in api.calls],['providers'])
        for _ in range(4):self.ui.view_html(session.view())
        self.assertEqual(len(api.calls),1)

    def test_client_conversations_are_independent(self):
        first,api=self.session(IntentResult('book',{'phone':'555-0101'}))
        second,other=self.session()
        first.submit('book, phone 555-0101')
        self.assertNotEqual(first.conversation.session_id,second.conversation.session_id)
        self.assertNotIn('phone',second.conversation.fields)
        self.assertEqual(other.calls,[])
        self.assertNotIn('555-0101',str(second.view()))

    def test_actual_core_booking_only_on_explicit_submit_and_no_render_replay(self):
        session,api=self.session(
            IntentResult('book',{'phone':'555-0101','dob':'1985-04-12','specialty':'primary_care','location':'downtown'}),
            IntentResult('book',{'selection':'1'}),IntentResult('book',{}))
        session.submit('Book primary care downtown with my synthetic identity')
        proposal=session.submit('1')
        self.assertIn('Reply yes',proposal['message'])
        self.assertNotIn('book',[x[0] for x in api.calls])
        self.ui.view_html(session.view())
        booked=session.submit('yes')
        self.assertEqual(booked['outcome'],'booked')
        for _ in range(6):self.ui.view_html(session.view())
        session.submit('yes')
        self.assertEqual([x[0] for x in api.calls].count('book'),1)
        self.assertTrue(booked['policy'])
        from scheduling_assistant.policy import ENUMS
        for row in booked['policy']:
            self.assertEqual(set(row['facts']),set(ENUMS))
            for key,value in row['facts'].items():self.assertIn(value,ENUMS[key])
        book_decision=next(row for row in booked['policy'] if row['facts']['action']=='book')
        self.assertEqual(book_decision['facts']['consent'],'current_explicit')
        self.assertEqual(book_decision['facts']['proposal'],'current')
        rendered=self.ui.view_html(booked)
        self.assertIn('action: book',rendered)
        self.assertIn('consent: current_explicit',rendered)
        self.assertNotIn('555-0101',rendered)
        self.assertNotIn('1985-04-12',rendered)

    def test_no_match_is_truthful_and_private(self):
        session,api=self.session(IntentResult('book',{'phone':'555-9999','dob':'1990-01-01','specialty':'primary_care'}))
        api.matches=[]
        result=session.submit('Book with my synthetic no-match identity')
        self.assertEqual(result['outcome'],'no_match')
        self.assertNotIn('availability',[x[0] for x in api.calls])
        self.assertNotIn('555-9999',self.ui.view_html(result))

    def test_latest_reply_only_and_html_escaped(self):
        class Replies:
            def handle(self,conversation,text):return TurnResult('<script>alert(1)</script>','collecting',policy=[{'disposition':'stop','reason':'safe_reason','rule':'R-TEST','sources':['POL-ID-01'],'raw':'secret-sentinel'}])
        session=self.ui.UISession(assistant=Replies(),environ={'SCHEDULING_INTENT_MODE':'offline'})
        view=session.submit('private-raw-utterance')
        self.assertNotIn('private-raw-utterance',str(session.__dict__))
        html=self.ui.view_html(view)
        self.assertNotIn('<script>',html)
        self.assertIn('&lt;script&gt;',html)
        self.assertNotIn('secret-sentinel',html)
        self.assertNotIn('history',session.__dict__)
        self.assertNotIn('transcript',session.__dict__)

    def test_trace_rejects_arbitrary_field_values(self):
        rows=[{'disposition':'proceed','reason':'<script>secret</script>','rule':'R-TEST','sources':['POL-ID-01']},
              {'disposition':'stop','reason':'safe_reason','rule':'R-TEST','sources':['secret identity value']}]
        self.assertEqual(self.ui.normalized_trace(rows),[])

    def test_trace_displays_exact_categorical_snapshot_with_its_decision(self):
        facts={'action':'book','request':'scheduling','criteria':'supported',
               'identity':'verified','slots':'returned','selection':'returned_option',
               'proposal':'current','consent':'current_explicit','api':'not_called','model':'valid'}
        row={'disposition':'proceed','reason':'booking_confirmed','rule':'R-TEST',
             'sources':['SPEC-FR022'],'facts':facts,'raw':'private-sentinel'}
        normalized=self.ui.normalized_trace([row])
        self.assertEqual(normalized[0]['facts'],facts)
        self.assertIsNot(normalized[0]['facts'],facts)
        view={'mode':'offline','model':'test','state':'awaiting_confirmation',
              'message':'Confirm the displayed appointment.','policy':[row]}
        rendered=self.ui.view_html(view)
        for key,value in facts.items():self.assertIn(key+': '+value,rendered)
        self.assertIn('R-TEST',rendered)
        self.assertNotIn('private-sentinel',rendered)

    def test_trace_omits_invalid_nested_facts_without_inventing_legacy_snapshot(self):
        facts={'action':'book','request':'scheduling','criteria':'supported',
               'identity':'verified','slots':'returned','selection':'returned_option',
               'proposal':'current','consent':'current_explicit','api':'not_called','model':'valid'}
        base={'disposition':'stop','reason':'safe_reason','rule':'R-TEST','sources':['SPEC-FR022']}
        variants=[{**facts,'identity':'private-sentinel'}, {**facts,'phone':'private-sentinel'},
                  {k:v for k,v in facts.items() if k!='consent'}, {**facts,'identity':{'raw':'private-sentinel'}},
                  {**facts,'action':['book']}, 'private-sentinel', None]
        for invalid in variants:
            with self.subTest(invalid=invalid):
                rows=self.ui.normalized_trace([{**base,'facts':invalid}])
                self.assertEqual(rows,[base])
                self.assertNotIn('private-sentinel',str(rows))
        self.assertEqual(self.ui.normalized_trace([base]),[base])

    def test_default_live_mode_and_explicit_offline_configuration(self):
        with patch.object(self.ui,'build_assistant',return_value=object()) as build:
            live=self.ui.UISession(environ={})
            self.assertEqual(live.view()['mode'],'live')
            self.assertEqual(build.call_args.args[0]['model'],'gpt-5.4-mini')
        with patch.object(self.ui,'build_assistant',return_value=object()):
            offline=self.ui.UISession(environ={'SCHEDULING_INTENT_MODE':'offline','OPENAI_MODEL':'review-model'})
            self.assertEqual(offline.view()['mode'],'offline')
            self.assertEqual(offline.view()['model'],'review-model')

    def test_bad_configuration_and_unexpected_errors_are_safe(self):
        invalid=self.ui.UISession(environ={'SCHEDULING_INTENT_MODE':'arbitrary-secret'})
        self.assertEqual(invalid.view()['outcome'],'failed')
        self.assertNotIn('arbitrary-secret',self.ui.view_html(invalid.view()))
        class Exploding:
            def handle(self,conversation,text):
                conversation.state='booking'
                raise RuntimeError('secret-sentinel')
        session=self.ui.UISession(assistant=Exploding(),environ={'SCHEDULING_INTENT_MODE':'offline'})
        result=session.submit('yes')
        self.assertEqual(result['outcome'],'unknown')
        self.assertNotIn('secret-sentinel',str(result))
        self.assertEqual(session.submit('reset')['outcome'],'unknown')

    def test_simultaneous_client_callback_cannot_execute_two_turns(self):
        class Counting:
            def __init__(self):self.calls=0
            def handle(self,conversation,text):self.calls+=1;return TurnResult('ok','collecting')
        core=Counting();session=self.ui.UISession(assistant=core,environ={'SCHEDULING_INTENT_MODE':'offline'})
        session._lock.acquire()
        try:session.submit('yes')
        finally:session._lock.release()
        self.assertEqual(core.calls,0)

    def test_local_branding_has_no_remote_tracking(self):
        html=self.ui.brand_html()
        self.assertIn('#13477d',html.lower())
        self.assertIn('#e0a42e',html.lower())
        self.assertIn('Ochsner Health',html)
        self.assertNotIn('<script',html.lower())
        self.assertNotIn('https://',html)
