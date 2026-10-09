"""Actual ZEN policy behavior; facts are synthetic normalized controller state."""
import dataclasses
import importlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

BASE = dict(action='book', request='scheduling', criteria='supported',
            identity='verified', slots='returned', selection='returned_option',
            proposal='current', consent='current_explicit', api='not_called', model='valid')

class SchedulingPolicyTests(unittest.TestCase):
    def setUp(self):
        try:
            self.policy = importlib.import_module('scheduling_assistant.policy')
        except ModuleNotFoundError:
            self.policy = None
        self.assertIsNotNone(self.policy, 'Required actual ZEN PolicyEngine is not implemented')
        self.engine = self.policy.PolicyEngine()

    def decide(self, **changes):
        return self.engine.evaluate({**BASE, **changes})

    def test_real_engine_positive_actions(self):
        cases = [
            ({}, 'R-BOOK'),
            ({'action':'providers','identity':'not_checked'}, 'R-PROVIDERS'),
            ({'action':'identify','identity':'not_checked'}, 'R-IDENTIFY'),
            ({'action':'availability'}, 'R-AVAILABILITY'),
            ({'action':'propose','api':'ok'}, 'R-PROPOSE'),
            ({'action':'report','api':'created_201'}, 'R-REPORT-CREATED'),
        ]
        for changes, rule in cases:
            with self.subTest(rule=rule):
                result = self.decide(**changes)
                self.assertEqual((result.disposition,result.rule), ('proceed',rule))
                self.assertTrue(result.sources)
        self.assertIsNotNone(self.engine._decision, 'No detached/token engine integration')

    def test_identity_before_each_private_action(self):
        for action in ('availability','propose','book','report'):
            for identity, reason in [('not_checked','identity_required'),('no_match','no_patient_match'),('multiple','private_identity_clarification')]:
                with self.subTest(action=action,identity=identity):
                    result=self.decide(action=action,identity=identity)
                    self.assertEqual((result.disposition,result.reason),('clarify',reason))
                    self.assertIn('POL-ID-0'+str(['not_checked','no_match','multiple'].index(identity)+1), result.sources)

    def test_failure_rules_and_sources(self):
        cases=[
          ({'request':'medical_advice'},'stop','medical_advice','POL-MED-01'),
          ({'request':'human_requested'},'stop','human_requested','POL-HANDOFF-01'),
          ({'request':'unsupported'},'stop','unsupported_request','POL-HANDOFF-02'),
          ({'criteria':'unsupported'},'stop','unsupported_criteria','POL-HANDOFF-06'),
          ({'model':'malformed'},'stop','interpretation_unavailable','CON-TEST-01'),
          ({'model':'unavailable'},'stop','interpretation_unavailable','CON-TEST-01'),
          ({'api':'unavailable'},'stop','api_unavailable','POL-HANDOFF-04'),
          ({'api':'unknown_write'},'reconcile','booking_outcome_unknown','CON-REQ-03'),
          ({'api':'conflict_409'},'clarify','slot_conflict','POL-BOOK-04'),
          ({'api':'invalid_response'},'stop','invalid_api_response','POL-BOOK-03'),
        ]
        for changes, disposition, reason, source in cases:
            with self.subTest(changes=changes):
                result=self.decide(**changes)
                self.assertEqual((result.disposition,result.reason),(disposition,reason))
                self.assertIn(source,result.sources)

    def test_focused_missing_context_and_consent(self):
        cases=[({'criteria':'missing'},'missing_criteria'),
               ({'slots':'empty'},'no_availability'),
               ({'selection':'missing'},'selection_required'),
               ({'selection':'invalid'},'invalid_slot_selection'),
               ({'proposal':'missing'},'proposal_required'),
               ({'proposal':'stale'},'stale_confirmation')]
        cases += [({'consent':v},'confirmation_required') for v in ('missing','declined','ambiguous')]
        for changes,reason in cases:
            with self.subTest(changes=changes):
                decision=self.decide(**changes)
                self.assertEqual(decision.reason,reason)
                self.assertNotEqual(decision.disposition,'proceed')

    def test_first_hit_priority_and_changed_context(self):
        self.assertEqual(self.decide(api='unknown_write',request='medical_advice',model='malformed').rule,'R-UNKNOWN')
        self.assertEqual(self.decide(request='medical_advice',model='malformed').rule,'R-MEDICAL')
        self.assertEqual(self.decide(identity='multiple',consent='current_explicit').reason,'private_identity_clarification')
        self.assertEqual(self.decide(proposal='stale',consent='current_explicit').reason,'stale_confirmation')
        self.assertEqual(self.decide().rule,'R-BOOK')
        self.assertEqual(self.decide(proposal='stale').reason,'stale_confirmation')
        self.assertEqual(self.decide().rule,'R-BOOK', 'Engine must not retain facts across calls')

    def test_every_required_fact_is_strict_and_no_unknown_fields(self):
        for key in BASE:
            for value in (None,False,[],{},'unknown-enum','phone-secret-sentinel'):
                with self.subTest(key=key,value=value):
                    self.assertEqual(self.engine.evaluate({**BASE,key:value}).reason,'invalid_policy_facts')
            incomplete=dict(BASE);incomplete.pop(key)
            self.assertEqual(self.engine.evaluate(incomplete).reason,'invalid_policy_facts')
        for field in ('patientId','slotId','phone','dob','zip','confirmed','raw_text'):
            self.assertEqual(self.engine.evaluate({**BASE,field:'secret-sentinel'}).reason,'invalid_policy_facts')
        for bad in (None,[],{},'text'):
            self.assertEqual(self.engine.evaluate(bad).disposition,'stop')

    def test_catchall_fails_closed_for_unmatched_valid_facts(self):
        result=self.decide(slots='not_fetched')
        self.assertEqual((result.disposition,result.rule),('stop','R-FAIL-CLOSED'))

    def test_decision_immutable_and_only_safe_output(self):
        result=self.decide()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.reason='changed'
        self.assertIsInstance(result.sources,tuple)
        trace=result.as_dict()
        self.assertEqual(set(trace),{'disposition','reason','rule','sources'})
        self.assertIsInstance(trace['sources'],list)
        self.assertNotIn('patient',json.dumps(trace).lower())

    def test_engine_failure_and_invalid_output_stop_without_echoing(self):
        class Broken:
            def evaluate(self,*args):
                raise RuntimeError('secret-sentinel')
        class BadOutput:
            def evaluate(self,*args):
                return {'result':{'disposition':'proceed','reason':'forged','rule':'R-BOOK','sources':[], 'raw':'secret-sentinel'}}
        for broken in (Broken(),BadOutput()):
            with patch.object(self.engine,'_decision',broken):
                result=self.decide()
                self.assertEqual((result.disposition,result.reason),('stop','policy_engine_unavailable'))
                self.assertNotIn('secret-sentinel',json.dumps(result.as_dict()))
        # Loading a missing or malformed developer-selected model never falls back to Python rules.
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'bad.json'
            path.write_text('{not-json')
            for candidate in (path,Path(directory)/'missing.json'):
                result=self.policy.PolicyEngine(candidate).evaluate(dict(BASE))
                self.assertEqual((result.disposition,result.reason),('stop','policy_engine_unavailable'))

    def test_committed_graph_and_source_registry_are_complete(self):
        folder=Path(self.policy.__file__).parent/'policy_models'
        graph=json.loads((folder/'scheduling.json').read_text())
        registry=json.loads((folder/'sources.json').read_text())
        table=next(n['content'] for n in graph['nodes'] if n['type']=='decisionTableNode')
        self.assertEqual(table['hitPolicy'],'first')
        self.assertEqual(table['rules'][-1]['_id'],'R-FAIL-CLOSED')
        self.assertEqual({n['type'] for n in graph['nodes']},{'inputNode','decisionTableNode','outputNode'})
        ids=[]
        for row in table['rules']:
            ids.append(row['_id'])
            for source in json.loads(row['sources']):
                self.assertIn(source,registry)
                self.assertTrue({'document','section','bullet','spec'} <= set(registry[source]))
                self.assertTrue(registry[source]['spec'].startswith('specs/001-appointment-scheduling/spec.md#'))
        self.assertEqual(len(ids),len(set(ids)))

if __name__=='__main__':
    unittest.main()

class SchedulingPolicyGraphBoundaryTests(unittest.TestCase):
    def test_proposal_clarifications_use_actual_zen(self):
        from scheduling_assistant.policy import PolicyEngine
        engine=PolicyEngine()
        for change,rule in [('empty','R-PROPOSE-EMPTY'),('missing','R-PROPOSE-SELECT'),('invalid','R-PROPOSE-INVALID-SELECT')]:
            facts={**BASE,'action':'propose','api':'ok'}
            facts['slots' if change=='empty' else 'selection']=change
            self.assertEqual(engine.evaluate(facts).rule,rule)

    def test_non_table_or_expression_model_is_rejected(self):
        import scheduling_assistant.policy as policy
        path=Path(policy.__file__).parent/'policy_models/scheduling.json'
        graph=json.loads(path.read_text())
        variants=[]
        extra=json.loads(json.dumps(graph));extra['nodes'].append({'id':'code','type':'functionNode','name':'unreviewed','content':'return secret'})
        variants.append(extra)
        expression=json.loads(json.dumps(graph));expression['nodes'][1]['content']['rules'][0]['api']='contains("secret", "s")'
        variants.append(expression)
        output=json.loads(json.dumps(graph));output['nodes'][1]['content']['rules'][0]['reason']='"secret-sentinel"'
        variants.append(output)
        with tempfile.TemporaryDirectory() as directory:
            candidate=Path(directory)/'unreviewed.json'
            for variant in variants:
                candidate.write_text(json.dumps(variant))
                decision=policy.PolicyEngine(candidate).evaluate(dict(BASE))
                self.assertEqual(decision.reason,'policy_engine_unavailable')
                self.assertNotIn('secret',json.dumps(decision.as_dict()))
