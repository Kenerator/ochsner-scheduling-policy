"""Loopback callback-only Marimo UI; use synthetic data.
Run with PYTHONPATH=src .venv/bin/marimo run app.py --host 127.0.0.1 --port 28182.
Default is live; SCHEDULING_INTENT_MODE=offline explicitly selects rehearsal.
"""
import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="Ochsner scheduling · Policy")

with app.setup:
    import html
    import os
    from pathlib import Path
    import re
    from threading import Lock
    import marimo as mo
    from scheduling_assistant.policy import ENUMS as POLICY_FACT_ENUMS
    from scheduling_assistant.models import recovery_context

    def normalized_trace(rows):
        """Display the fixed normalized policy shape, never arbitrary engine fields."""
        result = []
        if not isinstance(rows, list):
            return result
        for row in rows[-25:]:
            if not isinstance(row, dict):
                continue
            disposition, reason, rule, sources = (row.get(k) for k in ('disposition', 'reason', 'rule', 'sources'))
            if (disposition not in {'proceed', 'clarify', 'stop', 'reconcile'} or
                not isinstance(reason, str) or not re.fullmatch(r'[a-z_]{1,80}', reason) or
                not isinstance(rule, str) or not re.fullmatch(r'R-[A-Z0-9-]{1,80}', rule) or
                not isinstance(sources, (list, tuple)) or not sources or
                any(not isinstance(s, str) or not re.fullmatch(r'[A-Z][A-Z0-9-]{1,60}', s) for s in sources)):
                continue
            decision = {'disposition': disposition, 'reason': reason, 'rule': rule, 'sources': list(sources)}
            facts = row.get('facts')
            # Only controller-derived enum snapshots are inspectable. Keep a valid
            # legacy decision without inventing facts or exposing invalid nested data.
            if (type(facts) is dict and set(facts) == set(POLICY_FACT_ENUMS) and
                all(type(facts[key]) is str and facts[key] in allowed
                    for key, allowed in POLICY_FACT_ENUMS.items())):
                decision['facts'] = {key: facts[key] for key in POLICY_FACT_ENUMS}
            result.append(decision)
        return result


    def build_assistant(config):
        """Construct adapters without calling either scheduling or model services."""
        from scheduling_assistant.core import Assistant
        from scheduling_assistant.adapters.http import HttpSchedulingAPI
        from scheduling_assistant.adapters.intent import OfflineIntent
        if config['mode'] == 'live':
            from scheduling_assistant.adapters.intent import OpenAIIntent
            intent = OpenAIIntent(model=config['model'])
        else:
            intent = OfflineIntent()
        return Assistant(HttpSchedulingAPI(config['api']), intent)


    class UISession:
        """One app-client conversation; no transcript, global session, or file writes."""
        def __init__(self, assistant=None, environ=None):
            from scheduling_assistant.models import Conversation
            env = os.environ if environ is None else environ
            self.conversation = Conversation()
            self._lock = Lock()
            self._blocked = False
            self._assistant = None
            self._config = {'mode': env.get('SCHEDULING_INTENT_MODE', 'live'),
                            'model': env.get('OPENAI_MODEL', 'gpt-5.4-mini'),
                            'api': env.get('SCHEDULING_API_BASE', 'http://127.0.0.1:4012')}
            self._last = {'message': 'How can I help? Find a provider or book a synthetic appointment. I will ask for missing information and confirm the exact choice before booking.',
                          'state': 'collecting', 'outcome': '', 'policy': []}
            try:
                if (self._config['mode'] not in {'live', 'offline'} or
                    not isinstance(self._config['model'], str) or
                    not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,99}', self._config['model'])):
                    raise ValueError('invalid configuration')
                self._assistant = assistant if assistant is not None else build_assistant(self._config)
            except Exception:
                # Keys, downstream errors and environment values never reach the page.
                self._config = {'mode': 'live', 'model': 'not configured', 'api': ''}
                self._last = {'message': 'The assistant is not configured. Check the documented local API and model setup, then restart the app. No scheduling action was taken.',
                              'state': 'configuration', 'outcome': 'failed', 'policy': []}

        def view(self):
            """Pure snapshot: rerendering cannot interpret text or perform an effect."""
            return {**self._last, 'policy': normalized_trace(self._last['policy']),
                    'mode': self._config['mode'], 'model': self._config['model'],
                    'intent': self.conversation.intent, 'recovery': recovery_context(self.conversation)}

        def submit(self, text):
            if text is None or isinstance(text, str) and not text.strip():
                return self.view()
            # The shared core rejects invalid/oversized input under this lock;
            # rejection must also revoke any pending appointment proposal.
            if self._assistant is None or self._blocked:
                return self.view()
            if not self._lock.acquire(blocking=False):
                return {**self.view(), 'message': 'Your current turn is still running. Wait for its result before sending another message.'}
            try:
                result = self._assistant.handle(self.conversation, text)
                self._last = {'message': result.message, 'state': result.state,
                              'outcome': result.outcome, 'policy': normalized_trace(result.policy)}
            except Exception:
                # An unexpected exception can follow a write. Freeze this UI session;
                # neither rerender nor reset is evidence that an attempted write failed.
                self._blocked = True
                unknown = self.conversation.state == 'booking' or self.conversation.unknown
                self._last = {'message': 'An unexpected application error stopped this session. No successful outcome can be inferred. Contact scheduling through your usual channel to reconcile any attempted booking before trying again.',
                              'state': 'unknown' if unknown else 'application_error',
                              'outcome': 'unknown' if unknown else 'failed', 'policy': []}
            finally:
                self._lock.release()
            return self.view()


    def submit_callback(session, set_view):
        """The form commits a value only on Submit; reactive render cells never handle."""
        def on_submit(value):
            if isinstance(value, str) and value.strip():
                set_view(session.submit(value))
        return on_submit


    def brand_html():
        assets = Path(__file__).resolve().parent / 'assets/ui'
        logo = (assets / 'branding/ochsner-health-observed.svg').read_text()
        # The adopted source has intrinsic dimensions but no viewBox. Supply its
        # coordinate system only at render time so responsive sizing cannot crop it.
        logo = logo.replace('<svg ', '<svg viewBox="0 0 222 26" preserveAspectRatio="xMinYMid meet" ', 1)
        theme = (assets / 'themes/ochsner-observed-theme.css').read_text()
        return '<style>' + theme + '''
        .policy-hero{border-top:5px solid var(--brand-accent);padding:16px 0 4px;color:var(--text)}
        .policy-logo{line-height:0}
        .policy-logo svg{display:block;width:222px;max-width:100%;height:auto;aspect-ratio:222/26}
        .policy-hero h1{color:var(--brand-primary);font:700 clamp(24px,4vw,30px)/1.2 var(--font-ui);margin:16px 0 8px}
        .policy-hero p{margin:6px 0;line-height:1.5}
        .policy-reply{background:var(--surface);color:var(--text);border:1px solid #c7d1dc;border-left:5px solid var(--brand-primary);border-radius:8px;padding:16px;margin:10px 0;white-space:pre-wrap;line-height:1.6}
        .policy-meta{color:#394957;font-size:13px;line-height:1.5;margin:0 0 8px;overflow-wrap:anywhere}
        .policy-inspector{margin:12px 0 0;border:1px solid #c7d1dc;border-radius:8px;padding:14px;color:var(--text);background:var(--surface)}
        .policy-recovery{margin-top:12px}
        .policy-recovery dt{font-weight:600;margin-top:8px}
        .policy-recovery dd{margin:2px 0 8px}
        .policy-inspector summary{cursor:pointer;font-weight:600;color:var(--brand-primary)}
        .policy-table-scroll{overflow-x:auto;max-width:100%}
        .policy-inspector table{width:100%;min-width:580px;border-collapse:collapse;font-size:13px;margin-top:12px}
        .policy-inspector th,.policy-inspector td{min-width:80px;text-align:left;vertical-align:top;padding:8px;border-bottom:1px solid #d7dfe7;overflow-wrap:anywhere}
        .policy-inspector pre{min-width:210px;white-space:pre-wrap;font-size:12px;line-height:1.5}
        .policy-inspector :focus-visible{outline:3px solid var(--brand-primary);outline-offset:3px}
        </style><header class="policy-hero"><div class="policy-logo" role="img" aria-label="Ochsner Health">''' + logo + '''</div>
        <h1>Let's find your appointment</h1><p>AI scheduling assistant · synthetic demonstration</p>
        <p>Find providers, explore returned appointments, and confirm your choice. Use synthetic information only. I cannot provide medical advice.</p></header>'''


    def recovery_html(snapshot):
        """Render only the shared core's categorical context, never arbitrary values."""
        labels={'phone':'phone','dob':'date of birth','zip':'ZIP','specialty':'specialty',
                'location':'location','startDate':'start date','endDate':'end date'}
        effects={'not_attempted':'Not attempted in this conversation','confirmed':'Confirmed',
                 'rejected':'Rejected by scheduling service','unknown':'Unknown — reconcile before retry'}
        steps={'reconcile_before_retry':'Contact scheduling through your usual channel to reconcile before retrying.',
               'keep_confirmation':'Keep the confirmed appointment details. Reset does not undo booking.',
               'provide_missing_information':'For booking, provide or correct the missing information.',
               'confirm_current_proposal':'Review the exact proposal; send yes to confirm or no to decline.',
               'choose_returned_option':'Choose a returned numbered option, or contact scheduling.',
               'contact_scheduling':'Contact scheduling through your usual channel.'}
        if (not isinstance(snapshot,dict) or
            snapshot.get('booking') not in effects or snapshot.get('next_step') not in steps or
            snapshot.get('identity') not in {'verified','ambiguous','unverified'} or
            snapshot.get('support_delivery')!='not_sent' or
            any(not isinstance(snapshot.get(k),list) or
                any(not isinstance(v,str) or v not in labels for v in snapshot[k]) for k in ('known','missing'))):
            return ''
        fields=lambda key: ', '.join(labels[v] for v in snapshot[key]) or 'None'
        values=[('Information supplied (field names only)',fields('known')),
                ('Missing for booking',fields('missing')),('Patient match',snapshot['identity']),
                ('Booking outcome',effects[snapshot['booking']]),('Support contact','Not sent'),
                ('Next step',steps[snapshot['next_step']])]
        return '<details class="policy-recovery"><summary>Recovery context</summary><dl>'+''.join(
            '<dt>'+html.escape(k)+'</dt><dd>'+html.escape(v)+'</dd>' for k,v in values)+'</dl></details>'


    def view_html(view):
        esc = lambda value: html.escape(str(value), quote=True)
        mode = 'Live AI interpretation' if view['mode'] == 'live' else 'Offline rehearsal · deterministic interpretation'
        model = ' · Model: ' + esc(view['model']) if view['mode'] == 'live' else ''
        rows = normalized_trace(view.get('policy', []))
        table_rows = ''
        for row in rows:
            facts = row.get('facts')
            snapshot = ('<details><summary>Action facts</summary><pre>'+esc('\n'.join(key+': '+value for key,value in facts.items()))+'</pre></details>'
                        if facts is not None else 'Snapshot unavailable')
            table_rows += '<tr><td>'+esc(row['disposition'])+'</td><td>'+esc(row['reason'])+'</td><td>'+esc(row['rule'])+'</td><td>'+esc(', '.join(row['sources']))+'</td><td>'+snapshot+'</td></tr>'
        table = ('<div class="policy-table-scroll" role="region" aria-label="Policy decision table" tabindex="0"><table><thead><tr><th scope="col">Decision</th><th scope="col">Reason</th><th scope="col">Rule</th><th scope="col">Sources</th><th scope="col">Facts</th></tr></thead><tbody>'+table_rows+'</tbody></table></div>' if rows else '<p>No policy-gated action was proposed in this turn.</p>')
        return '<div class="policy-meta">'+esc(mode)+model+' · State: '+esc(view['state'])+' · Intent: '+esc(view.get('intent','unknown'))+'</div><section class="policy-reply" role="status" aria-live="polite" aria-label="Assistant response">'+esc(view['message'])+'</section><details class="policy-inspector"><summary>Inspect this turn’s policy decisions</summary><p>ZEN 2.1.2 gates proposed actions. The shared core independently checks identity, current confirmation and booking outcomes.</p>'+table+recovery_html(view.get('recovery'))+'</details>'


@app.cell
def _(UISession, mo, submit_callback):
    # This cell runs once for each client kernel. No module-global conversation.
    _session = UISession()
    get_view, _set_view = mo.state(_session.view())
    message_form = mo.ui.text_area(
        label="Your message",
        placeholder="Which primary care providers are downtown?",
        max_length=4000,
        rows=3,
        full_width=True,
    ).form(
        submit_button_label="Send message",
        clear_on_submit=True,
        on_change=submit_callback(_session, _set_view),
    )
    return get_view, message_form


@app.cell
def _(brand_html, get_view, message_form, mo, view_html):
    # Pure rendering: reading state or toggling the inspector has no API effect.
    mo.vstack([
        mo.Html(brand_html()),
        mo.Html(view_html(get_view())),
        message_form,
        mo.md("Booking requires **yes** after the exact appointment is displayed. Send **no** to decline, or **reset** for a new conversation. Reset does not undo a booking or resolve an unknown outcome."),
    ], gap=1)
    return


if __name__ == "__main__":
    app.run()
