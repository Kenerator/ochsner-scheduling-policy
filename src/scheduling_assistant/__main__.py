"""Text adapter; every scheduling effect is delegated to the shared core."""
import argparse
import json
import os
import sys
from .core import Assistant
from .models import Conversation
from .adapters.http import HttpSchedulingAPI

def run(argv=None, *, input_stream=None, output=None, error=None, api=None, intent=None):
    parser=argparse.ArgumentParser(description='Synthetic AI scheduling assistant')
    parser.add_argument('--api-base',default='http://127.0.0.1:4012')
    parser.add_argument('--intent-mode',choices=('live','offline'),default='live')
    parser.add_argument('--model',default=os.environ.get('OPENAI_MODEL','gpt-5.4-mini'))
    args=parser.parse_args(argv)
    input_stream=input_stream or sys.stdin;output=output or sys.stdout;error=error or sys.stderr
    if intent is None:
        from .adapters.intent import OfflineIntent,OpenAIIntent
        if args.intent_mode=='live' and not os.environ.get('OPENAI_API_KEY'):
            print('Set OPENAI_API_KEY for live interpretation, or explicitly select --intent-mode offline.',file=error)
            return 2
        intent=OfflineIntent() if args.intent_mode=='offline' else OpenAIIntent(model=args.model)
    try:api=api or HttpSchedulingAPI(args.api_base)
    except (ValueError,TypeError):
        print('Invalid local scheduling service configuration.',file=error);return 2
    assistant=Assistant(api,intent,event_sink=lambda event:print(json.dumps(event,sort_keys=True),file=error))
    conversation=Conversation()
    print('AI scheduling assistant — synthetic data only. Interpretation: '+args.intent_mode+(' (simulated; no model calls).' if args.intent_mode=='offline' else '.')+' Type reset for a new conversation or quit to exit.',file=output)
    for line in input_stream:
        text=line.rstrip('\n')
        if text.strip().lower() in {'quit','exit'}:return 0
        result=assistant.handle(conversation,text)
        print(result.message,file=output,flush=True)
    return 0

def main():raise SystemExit(run())
if __name__=='__main__':main()
