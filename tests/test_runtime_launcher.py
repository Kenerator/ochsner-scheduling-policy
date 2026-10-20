"""Consumer routing tests: real Policy constructors, fake model transport only."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "tools" / "poc-runtime"
CANARY = "launcher-test-canary"


def load_entrypoint(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class RuntimeLauncherTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((RUNTIME / "launch.py").is_file(),
                        "Reviewed shared launcher is not installed")
        self.assertTrue((ROOT / "poc-launch.json").is_file(),
                        "Policy model-first launcher configuration is missing")
        with patch.object(sys, "path", [str(RUNTIME), *sys.path]):
            self.launch = load_entrypoint(RUNTIME / "launch.py", "policy_runtime_launch")
            self.adapters = load_entrypoint(RUNTIME / "adapters.py", "policy_runtime_adapters")
        self.config = self.launch.load_config(ROOT / "poc-launch.json")

    def specs(self, arguments, environment=None):
        environment = environment or {}
        request = self.launch.resolve_request(self.config, arguments, environment)
        with patch.dict(os.environ, environment, clear=True):
            specs = self.adapters.process_specs(ROOT, self.config, request,
                                                key=CANARY if request.mode == "model" else None)
        return request, specs

    def test_default_is_actual_live_adapter_and_exact_credential(self):
        request, specs = self.specs(["--interface", "cli"])
        self.assertEqual("model", request.mode)
        self.assertEqual("gpt-5.4-mini", request.model)
        self.assertEqual("[Env] OPENAI_API_KEY", self.config["credential"]["item"])
        self.assertEqual("notes", self.config["credential"]["field"])
        self.exercise_cli(specs, "gpt-5.4-mini")

    def test_environment_and_explicit_override_reach_real_cli_model(self):
        for arguments, expected in [([], "configured-model"),
                                    (["--model", "chosen-model"], "chosen-model")]:
            with self.subTest(arguments=arguments):
                request, specs = self.specs(["--interface", "cli", *arguments],
                                           {"OPENAI_MODEL": "configured-model"})
                self.assertEqual(expected, request.model)
                self.exercise_cli(specs, expected)

    def exercise_cli(self, specs, expected):
        from scheduling_assistant.__main__ import run
        from scheduling_assistant.adapters.intent import OpenAIIntent, FIELDS
        from test_scheduling_core import API
        host = next(spec for spec in specs if spec.role == "model")
        self.assertIn("scheduling_assistant", host.argv)
        args = list(host.argv[host.argv.index("scheduling_assistant") + 1:])
        requests = []
        def transport(request, timeout):
            requests.append(json.loads(request.data))
            value = {"intent": "provider_lookup", "fields": dict.fromkeys(FIELDS)}
            return {"status": "completed", "output": [{"type": "message", "content": [
                {"type": "output_text", "text": json.dumps(value)}]}]}
        def factory(**kwargs):
            return OpenAIIntent(transport=transport, **kwargs)
        with patch.dict(os.environ, host.environment, clear=True), patch(
                "scheduling_assistant.adapters.intent.OpenAIIntent", side_effect=factory):
            out, err = io.StringIO(), io.StringIO()
            code = run(args, api=API(), input_stream=io.StringIO("Find providers\nquit\n"),
                       output=out, error=err)
        self.assertEqual(0, code)
        self.assertEqual([expected], [request["model"] for request in requests])
        self.assertIn("Synthetic Doctor", out.getvalue())
        self.assertNotIn(CANARY, out.getvalue() + err.getvalue())

    def test_browser_wrapper_is_rejected_and_direct_ui_constructor_is_unchanged(self):
        from scheduling_assistant.adapters.intent import OpenAIIntent
        with self.assertRaises(self.launch.LaunchError):
            self.specs(["--interface", "browser"])
        requests, constructed = [], []
        def factory(**kwargs):
            instance = OpenAIIntent(transport=lambda *args: requests.append(args), **kwargs)
            constructed.append(instance)
            return instance
        environment = {"SCHEDULING_INTENT_MODE": "live", "OPENAI_MODEL": "browser-model",
                       "OPENAI_API_KEY": CANARY}
        with patch.dict(os.environ, environment, clear=True), patch(
                "scheduling_assistant.adapters.intent.OpenAIIntent", side_effect=factory):
            ui = load_entrypoint(ROOT / "app.py", "policy_launcher_ui")
            session = ui.UISession()
        self.assertEqual("live", session.view()["mode"])
        self.assertEqual("browser-model", constructed[0].model)
        self.assertEqual(CANARY, constructed[0]._api_key)
        self.assertEqual([], requests)

    def test_mock_is_secret_free_and_offline_has_no_model_key(self):
        environment = {"OPENAI_API_KEY": "stale-parent-canary", "BW_SESSION": "vault-canary"}
        for arguments in [[], ["--offline"]]:
            with self.subTest(arguments=arguments):
                request, specs = self.specs(["--interface", "cli", *arguments], environment)
                self.assertTrue(any(spec.role == "mock" for spec in specs))
                for spec in specs:
                    self.assertNotIn("BW_SESSION", spec.environment)
                    self.assertNotIn(CANARY, " ".join(spec.argv))
                    self.assertNotIn("stale-parent-canary", repr(spec.environment))
                    if spec.role != "model" or request.mode == "offline":
                        self.assertNotIn("OPENAI_API_KEY", spec.environment)
                if request.mode == "offline":
                    host = next(spec for spec in specs if "scheduling_assistant" in spec.argv)
                    self.assertIn("offline", host.argv)

    def test_installed_runtime_matches_reviewed_manifest(self):
        manifest = json.loads((RUNTIME / "export-manifest.json").read_text())
        self.assertEqual("20e3dd56747797b35c082d109ac3bb0a7d7b1ebe", manifest["source_revision"])
        self.assertEqual("clean", manifest["source_worktree_state"])
        self.assertEqual(4, len(manifest["files"]))
        for name, digest in manifest["files"].items():
            self.assertEqual(digest, hashlib.sha256((ROOT / name).read_bytes()).hexdigest())

    def test_bad_modes_models_ports_fail_without_substitution(self):
        for args in (["--model", ""], ["--model", "two words"], ["--api-port", "1"],
                     ["--unlimited-today"], ["--unknown"]):
            with self.subTest(args=args), self.assertRaises(self.launch.LaunchError):
                self.specs(args)
        for args in (["--ui-port", "29450"], ["--transport-port", "29451"]):
            with self.subTest(args=args), self.assertRaises(self.launch.LaunchError):
                self.specs(args)

    def test_help_and_doctor_never_resolve_credentials_or_start_children(self):
        with tempfile.TemporaryDirectory() as directory, socket.socket() as probe:
            helper = Path(directory) / "helper"
            helper.write_text("#!/bin/sh\nexit 99\n")
            helper.chmod(0o700)
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
            probe.close()
            environment = {**os.environ, "POC_SECRET_HELPER": str(helper)}
            with patch.dict(os.environ, environment, clear=True), patch.object(
                    self.launch.credentials, "resolve_key", side_effect=AssertionError("credential call")), \
                    patch("processes.run_owned", side_effect=AssertionError("child startup")), \
                    patch.object(sys, "path", [str(RUNTIME), *sys.path]), \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(0, self.launch.main(["--help"]))
                self.assertEqual(0, self.launch.main(["--config", str(ROOT / "poc-launch.json"),
                                                    "--doctor", "--api-port", str(port)]))

    def test_occupied_port_preserves_foreign_listener(self):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            port = listener.getsockname()[1]
            request = self.launch.resolve_request(self.config, ["--api-port", str(port)], {})
            with self.assertRaises(self.launch.LaunchError):
                self.adapters.preflight(ROOT, self.config, request)
            self.assertEqual(port, listener.getsockname()[1])
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                pass

    def test_real_offline_launch_reaps_owned_mock_on_cli_exit(self):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        environment = {**os.environ, "OPENAI_API_KEY": "stale-parent-canary",
                       "POC_SECRET_HELPER": "/nonexistent/no-helper"}
        result = subprocess.run([sys.executable, str(RUNTIME / "launch.py"), "--offline",
                                 "--api-port", str(port)], input="quit\n", text=True,
                                capture_output=True, cwd=ROOT, env=environment, timeout=20)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("simulated; no model calls", result.stdout)
        self.assertNotIn("stale-parent-canary", result.stdout + result.stderr)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", port))

    def test_missing_dedicated_helper_fails_before_startup_despite_inherited_key(self):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        environment = {**os.environ, "OPENAI_API_KEY": CANARY,
                       "POC_SECRET_HELPER": "/nonexistent/no-helper"}
        out, err = io.StringIO(), io.StringIO()
        with patch.dict(os.environ, environment, clear=True), \
                patch("processes.run_owned", side_effect=AssertionError("child startup")), \
                patch.object(sys, "path", [str(RUNTIME), *sys.path]), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.launch.main(["--config", str(ROOT / "poc-launch.json"),
                                     "--api-port", str(port)])
        self.assertEqual(2, code)
        self.assertNotIn(CANARY, out.getvalue() + err.getvalue())
        self.assertNotIn("offline", out.getvalue())

    def test_explicit_own_key_selection_uses_only_exact_notes_without_fallback(self):
        credential = dict(self.config["credential"], item="[Env] OPENAI_API_KEY", field="notes")
        with tempfile.TemporaryDirectory() as directory:
            helper = Path(directory) / "helper"
            helper.write_text("#!/bin/sh\nexit 99\n")
            helper.chmod(0o700)
            calls = []
            def fake_run(argv, **kwargs):
                calls.append(argv)
                self.assertNotIn("OPENAI_API_KEY", kwargs["env"])
                self.assertNotIn("BW_SESSION", kwargs["env"])
                return subprocess.CompletedProcess(argv, 0, stdout=CANARY, stderr="")
            environment = {"POC_SECRET_HELPER": str(helper), "OPENAI_API_KEY": "stale-parent-canary"}
            with patch.dict(os.environ, environment, clear=True):
                try:
                    key = self.launch.credentials.resolve_key(credential, run=fake_run)
                except self.launch.LaunchError:
                    self.fail("Explicit Operator-selected own-key notes binding is rejected")
            self.assertEqual(CANARY, key)
            self.assertEqual([[str(helper), "[Env] OPENAI_API_KEY", "notes"]], calls)
            calls.clear()
            def failed_run(argv, **kwargs):
                calls.append(argv)
                return subprocess.CompletedProcess(argv, 1, stdout="", stderr="private helper detail")
            with patch.dict(os.environ, {"POC_SECRET_HELPER": str(helper)}, clear=True):
                with self.assertRaises(self.launch.LaunchError) as failure:
                    self.launch.credentials.resolve_key(credential, run=failed_run)
            self.assertEqual([[str(helper), "[Env] OPENAI_API_KEY", "notes"]], calls)
            self.assertNotIn("private helper detail", str(failure.exception))

    def test_own_key_wrong_fields_and_unselected_items_fail_before_helper(self):
        for item, field in [("[Env] OPENAI_API_KEY", "password"),
                            ("[Env] OPENAI_API_KEY", "auto"),
                            ("unselected-item", "notes")]:
            credential = dict(self.config["credential"], item=item, field=field)
            with self.subTest(item=item, field=field), self.assertRaises(self.launch.LaunchError):
                self.launch.credentials.resolve_key(credential, run=lambda *a, **k: self.fail("helper called"))
