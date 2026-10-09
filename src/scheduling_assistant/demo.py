"""Fresh supplied-service demonstrations; only sanitized summaries are emitted."""
import argparse,importlib.util,json,platform,time
from contextlib import contextmanager
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from .core import Assistant
from .models import Conversation
from .adapters.http import HttpSchedulingAPI

SCENARIOS=('provider_lookup','success','failure','duplicate_identity','conflict','no_availability','outage','medical_advice')

@contextmanager
def disposable_service():
    source=Path(__file__).resolve().parents[2]/'reference/mock-api/server.py'
    spec=importlib.util.spec_from_file_location('supplied_demo_service',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    calls=[]
    class Handler(module.Handler):
        store=module.Store()
        def route(self,method,parsed):
            calls.append((method,parsed.path))
            return super().route(method,parsed)
        def audit(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield 'http://127.0.0.1:'+str(server.server_port),calls
    finally:server.shutdown();server.server_close();thread.join(2)

def run_scenario(scenario,*,intent=None,mode='offline'):
    if scenario not in SCENARIOS:raise ValueError('unknown_scenario')
    if intent is None:
        from .adapters.intent import OfflineIntent
        intent=OfflineIntent()
    events=[];rules=[];c=Conversation();start=time.monotonic()
    with disposable_service() as (base,calls):
        api=HttpSchedulingAPI(base,scenario='api_failure' if scenario=='outage' else None)
        assistant=Assistant(api,intent,event_sink=events.append)
        def turn(text):
            result=assistant.handle(c,text);rules.extend(x['rule'] for x in result.policy);return result
        if scenario=='provider_lookup':r=turn('Find primary care providers downtown')
        elif scenario=='medical_advice':r=turn('What medicine should I take for chest pain?')
        else:
            r=turn('Book '+('dermatology lakeside' if scenario=='no_availability' else 'primary care downtown'))
            phone,dob=('555-9999','1990-01-01') if scenario=='failure' else (('555-0130','1978-09-22') if scenario=='duplicate_identity' else ('555-0101','1985-04-12'))
            r=turn('My phone is '+phone);r=turn('My date of birth is '+dob)
            if scenario=='duplicate_identity':r=turn('My ZIP code is 70115')
            if c.slots:
                r=turn(str(len(c.slots)) if scenario=='conflict' else '1');r=turn('yes')
        outcome=r.outcome or ('providers' if c.state=='providers' else c.state)
        return {'scenario':scenario,'mode':mode,'python':platform.python_version(),'outcome':outcome,
                'bookRequests':sum(method=='POST' and path=='/appointments' for method,path in calls),
                'policyRules':sorted(set(rules)),'elapsedMs':round((time.monotonic()-start)*1000,2),
                'events':events}

def main(argv=None):
    parser=argparse.ArgumentParser(description='Disposable supplied-service scheduling demos')
    parser.add_argument('--scenario',choices=SCENARIOS,required=True)
    args=parser.parse_args(argv)
    print(json.dumps(run_scenario(args.scenario),sort_keys=True))
if __name__=='__main__':main()
