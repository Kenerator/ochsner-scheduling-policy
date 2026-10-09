"""Independent review regressions for explainability and escalation evidence."""
import unittest
from scheduling_assistant.core import Assistant
from scheduling_assistant.models import Conversation
from scheduling_assistant.ports import IntentResult
from test_scheduling_core import API,ScriptIntent,Deny

class ReviewRegressions(unittest.TestCase):
    def test_escalation_intent_and_reason_are_present_without_sensitive_text(self):
        for intent,reason in [('human_help','human_requested'),('medical_advice','medical_advice'),('unsupported','unsupported')]:
            with self.subTest(intent=intent):
                events=[];api=API();a=Assistant(api,ScriptIntent(IntentResult(intent,{})),event_sink=events.append)
                a.handle(Conversation(),'private-sentinel')
                self.assertEqual(events[-1]['intent'],intent)
                self.assertEqual(events[-1]['reason'],reason)
                self.assertEqual(events[-1]['outcome'],'failed')
                self.assertNotIn('private-sentinel',str(events));self.assertEqual(api.calls,[])
    def test_policy_denial_has_fixed_reason(self):
        events=[];a=Assistant(API(),ScriptIntent(IntentResult('provider_lookup',{})),policy=Deny(),event_sink=events.append)
        a.handle(Conversation(),'providers')
        self.assertEqual(events[-1]['reason'],'policy_denied')
    def test_inspectable_facts_are_the_actual_bounded_engine_input(self):
        a=Assistant(API(),ScriptIntent(IntentResult('provider_lookup',{})))
        r=a.handle(Conversation(),'providers')
        facts=r.policy[0]['facts']
        self.assertEqual(set(facts),{'action','request','criteria','identity','slots','selection','proposal','consent','api','model'})
        self.assertEqual(facts['action'],'providers');self.assertEqual(facts['identity'],'not_checked')
        self.assertNotIn('phone',str(facts))
