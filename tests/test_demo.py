"""Catch missing confirmation, replayed effects and unbounded failure loops."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from poc_demo.core import DemoService
from poc_demo.adapters import SyntheticAdapter
from poc_demo import run_scenario


class DemoTests(unittest.TestCase):
    def test_cancel_does_not_call_adapter(self):
        adapter = SyntheticAdapter()
        service = DemoService(adapter)
        proposal = service.propose("Synthetic operation")
        self.assertEqual(service.confirm(proposal.id, False)["state"], "cancelled")
        self.assertEqual(adapter.calls, 0)

    def test_repeat_confirmation_returns_original_without_second_effect(self):
        adapter = SyntheticAdapter()
        service = DemoService(adapter)
        proposal = service.propose("Synthetic operation")
        first = service.confirm(proposal.id, True)
        self.assertEqual(first["state"], "complete")
        self.assertEqual(service.confirm(proposal.id, True), first)
        self.assertEqual(adapter.calls, 1)
        first["state"] = "tampered"
        self.assertEqual(service.confirm(proposal.id, True)["state"], "complete")

    def test_cancel_is_terminal_even_if_confirmed_later(self):
        adapter = SyntheticAdapter()
        service = DemoService(adapter)
        proposal = service.propose("Synthetic operation")
        service.confirm(proposal.id, False)
        self.assertEqual(service.confirm(proposal.id, True)["state"], "cancelled")
        self.assertEqual(adapter.calls, 0)

    def test_confirmation_requires_known_proposal_and_actual_boolean(self):
        adapter = SyntheticAdapter()
        service = DemoService(adapter)
        proposal = service.propose("Synthetic operation")
        for identifier, answer in [("unknown", True), (proposal.id, 1), (proposal.id, "yes"), (proposal.id, None)]:
            with self.subTest(identifier=identifier, answer=answer), self.assertRaises(ValueError):
                service.confirm(identifier, answer)
        self.assertEqual(adapter.calls, 0)

    def test_confirmation_of_one_proposal_does_not_execute_another(self):
        adapter = SyntheticAdapter()
        service = DemoService(adapter)
        first = service.propose("First operation")
        second = service.propose("Second operation")
        self.assertEqual(service.confirm(second.id, True)["label"], "Second operation")
        self.assertEqual(service.confirm(first.id, False)["state"], "cancelled")
        self.assertEqual(adapter.calls, 1)

    def test_failure_hands_off_once_without_automatic_retry(self):
        adapter = SyntheticAdapter(fail=True)
        service = DemoService(adapter)
        proposal = service.propose("Synthetic operation")
        result = service.confirm(proposal.id, True)
        self.assertEqual(result["state"], "handoff")
        self.assertIn("support", result["message"].lower())
        self.assertEqual(service.confirm(proposal.id, True), result)
        self.assertEqual(adapter.calls, 1)

    def test_reset_does_not_allow_an_old_confirmation_on_a_new_service(self):
        old = DemoService(SyntheticAdapter()).propose("Old operation")
        adapter = SyntheticAdapter()
        fresh = DemoService(adapter)
        fresh.propose("New operation")
        with self.assertRaises(ValueError):
            fresh.confirm(old.id, True)
        self.assertEqual(adapter.calls, 0)

    def test_invalid_labels_do_not_create_effects(self):
        service = DemoService(SyntheticAdapter())
        for label in ("", "  ", None, 3):
            with self.subTest(label=label), self.assertRaises(ValueError):
                service.propose(label)

    def test_scenarios_are_repeatable_and_disclose_simulation(self):
        for name, state, calls in [("success", "complete", 1), ("cancel", "cancelled", 0),
                                   ("failure", "handoff", 1), ("handoff", "handoff", 1)]:
            with self.subTest(name=name):
                for _ in range(2):
                    result = run_scenario(name)
                    self.assertEqual(result["state"], state)
                    self.assertEqual(result["adapter_calls"], calls)
                    self.assertIs(result["simulated"], True)
        with self.assertRaises(ValueError):
            run_scenario("unknown")

    def test_real_cli_emits_finite_failure_and_rejects_unknown_scenario(self):
        root = Path(__file__).resolve().parents[1]
        env = dict(os.environ, PYTHONPATH=str(root / "src"))
        for name, code in [("failure", 0), ("unknown", 2)]:
            process = subprocess.run([sys.executable, "-m", "poc_demo", "--scenario", name],
                                     cwd=root, env=env, capture_output=True, text=True, timeout=5)
            self.assertEqual(process.returncode, code, process.stderr)
            if code == 0:
                self.assertEqual(json.loads(process.stdout)["state"], "handoff")


if __name__ == "__main__":
    unittest.main()
