"""CLI exercises the real core; input and diagnostic streams stay separate."""
import io, unittest
from unittest.mock import patch
from scheduling_assistant.ports import IntentResult
from test_scheduling_core import ScriptIntent,API
from scheduling_assistant.__main__ import run

class CliTests(unittest.TestCase):
    def test_lookup_discloses_mode_and_keeps_raw_input_out_of_diagnostics(self):
        out,err=io.StringIO(),io.StringIO()
        intent=ScriptIntent(IntentResult('provider_lookup',{}))
        code=run(['--intent-mode','offline'],input_stream=io.StringIO('secret-request\nquit\n'),output=out,error=err,api=API(),intent=intent)
        self.assertEqual(code,0);self.assertIn('AI',out.getvalue());self.assertIn('offline',out.getvalue());self.assertIn('Synthetic Doctor',out.getvalue())
        self.assertNotIn('secret-request',err.getvalue());self.assertIn('elapsedMs',err.getvalue())
    def test_unknown_booking_reset_does_not_suggest_safe_retry(self):
        from scheduling_assistant.ports import ApiError
        api=API();api.error=ApiError('unknown_write',unknown=True)
        intent=ScriptIntent(IntentResult('book',{'phone':'555-0101','dob':'1985-04-12','specialty':'primary_care'}),IntentResult('book',{'selection':'1'}))
        out,err=io.StringIO(),io.StringIO()
        run(['--intent-mode','offline'],input_stream=io.StringIO('book\n1\nyes\nreset\nquit\n'),output=out,error=err,api=api,intent=intent)
        self.assertIn('reconcile',out.getvalue());self.assertEqual(sum(x[0]=='book' for x in api.calls),1)
    def test_live_configuration_failure_is_safe(self):
        with patch.dict('os.environ',{},clear=True):
            out,err=io.StringIO(),io.StringIO()
            self.assertEqual(run([],input_stream=io.StringIO('quit\n'),output=out,error=err),2)
            self.assertIn('OPENAI_API_KEY',err.getvalue())
