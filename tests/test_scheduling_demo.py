"""Repeatable demos must exercise the supplied HTTP service and real policy."""
import unittest
from scheduling_assistant.demo import run_scenario
class DemoTests(unittest.TestCase):
    def test_required_scenarios_repeat_from_fresh_service_state(self):
        expected={'provider_lookup':'providers','success':'booked','failure':'no_match','duplicate_identity':'booked','conflict':'conflict','no_availability':'no_availability','outage':'failed','medical_advice':'guidance'}
        for scenario,outcome in expected.items():
            with self.subTest(scenario=scenario):
                for _ in range(2):
                    result=run_scenario(scenario)
                    self.assertEqual(result['outcome'],outcome)
                    self.assertEqual(result['mode'],'offline')
                    self.assertTrue(result['policyRules'])
                    self.assertEqual(result['bookRequests'],1 if scenario in {'success','duplicate_identity','conflict'} else 0)
