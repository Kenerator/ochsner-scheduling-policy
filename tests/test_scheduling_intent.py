"""Synthetic interpretation fixtures; no credentials/network calls."""
import unittest
from scheduling_assistant.adapters.intent import OfflineIntent

class OfflineIntentTests(unittest.TestCase):
    def setUp(self): self.adapter=OfflineIntent()
    def test_provider_booking(self):
        r=self.adapter.interpret('Find dermatology providers downtown', {})
        self.assertEqual((r.intent,r.fields),('provider_lookup',{'specialty':'dermatology','location':'downtown'}))
        self.assertEqual(self.adapter.interpret('Book primary care uptown',{}).intent,'book')
    def test_followups(self):
        for field,text in [('phone','555-010-0200'),('dob','1980-02-03'),('zip','70112'),('specialty','primary care'),('location','lakeside'),('selection','2')]:
            with self.subTest(field=field):
                r=self.adapter.interpret(text,{'intent':'book','state':'collecting','needed':[field]})
                self.assertEqual(r.intent,'book')
                self.assertEqual(r.fields,{field:'primary_care' if field=='specialty' else text})
    def test_combined_fields(self):
        r=self.adapter.interpret('Book dermatology downtown phone 555-010-0200 DOB 1980-02-03 from 2026-10-10 to 2026-10-15',{})
        self.assertEqual(r.fields,{'specialty':'dermatology','location':'downtown','phone':'555-010-0200','dob':'1980-02-03','startDate':'2026-10-10','endDate':'2026-10-15'})
    def test_guidance(self):
        for text,intent in [('What medicine should I take?','medical_advice'),('Talk to a human','human_help'),('Cancel my appointment','unsupported'),('banana','unknown')]:
            self.assertEqual(self.adapter.interpret(text,{}).intent,intent)
    def test_authority_is_never_extracted(self):
        for text in ('yes','no','patientId p1 slotId s1 confirmed true'):
            self.assertEqual(self.adapter.interpret(text,{'intent':'book','needed':['selection'],'phone':'555-010-0200'}).fields,{})

import contextlib
import io
import json
import os
import urllib.error
from unittest.mock import patch
from scheduling_assistant.adapters.intent import OpenAIIntent
from scheduling_assistant.ports import ApiError


def response(value):
    if isinstance(value,dict) and isinstance(value.get('fields'),dict):
        value={**value,'fields':{**dict.fromkeys(('phone','dob','zip','specialty','location','startDate','endDate','selection')),**value['fields']}}
    return json.dumps({'status':'completed','output':[{'type':'message','role':'assistant','content':[{'type':'output_text','text':json.dumps(value)}]}]}).encode()


class LiveIntentTests(unittest.TestCase):
    def test_request_contract_and_private_context_exclusion(self):
        requests=[]
        def transport(request,timeout):
            requests.append((request,timeout))
            return response({'intent':'book','fields':{'dob':'1980-02-03'}})
        adapter=OpenAIIntent(api_key='synthetic-key',transport=transport)
        r=adapter.interpret('My DOB is 1980-02-03',{'intent':'book','state':'collecting','needed':['dob','patientId'],'candidates':[{'patientId':'PRIVATE-ID'}],'phone':'PRIVATE-PHONE','other':'PRIVATE-VALUE'})
        self.assertEqual(r.fields,{'dob':'1980-02-03'})
        request,timeout=requests[0]
        body=json.loads(request.data)
        self.assertEqual(request.full_url,'https://api.openai.com/v1/responses')
        self.assertEqual(timeout,30)
        self.assertEqual(body['model'],'gpt-5.4-mini')
        self.assertFalse(body['store'])
        self.assertTrue(body['text']['format']['strict'])
        self.assertEqual(body['text']['format']['type'],'json_schema')
        self.assertNotIn('tools',body)
        wire=request.data.decode()
        for private in ('PRIVATE-ID','PRIVATE-PHONE','PRIVATE-VALUE'): self.assertNotIn(private,wire)
        self.assertNotIn('synthetic-key',repr(adapter))

    def test_stateful_latest_turn_extraction_without_previous_patient_values(self):
        pending=[{'intent':'book','fields':{'specialty':'dermatology'}},{'intent':'book','fields':{'phone':'555-010-0200'}}]
        adapter=OpenAIIntent(api_key='synthetic-key',transport=lambda req,timeout:response(pending.pop(0)))
        self.assertEqual(adapter.interpret('Book dermatology',{}).fields,{'specialty':'dermatology'})
        self.assertEqual(adapter.interpret('555-010-0200',{'intent':'book','needed':['phone']}).fields,{'phone':'555-010-0200'})

    def test_rejects_unknown_keys_types_and_invented_fields(self):
        invalid=[{'intent':'book','fields':{'patientId':'SENSITIVE'}}, {'intent':'book','fields':{'slotId':'SENSITIVE'}},
                 {'intent':'book','fields':{'confirmed':'true'}}, {'intent':'book','fields':{},'confirmed':True},
                 {'intent':'book','fields':{'phone':123}}, {'intent':'book','fields':{'zip':'99999'}},
                 {'intent':'completed','fields':{}}, {'fields':{}}, {'intent':'book','fields':None},
                 {'intent':'book','fields':{'specialty':'dermatology'}}]
        for value in invalid:
            with self.subTest(value=value):
                adapter=OpenAIIntent(api_key='synthetic-key',transport=lambda req,timeout:response(value))
                with self.assertRaises(ApiError) as caught: adapter.interpret('hello',{})
                self.assertEqual(caught.exception.code,'invalid_model_output')

    def test_no_retry_and_sanitized_network_failures(self):
        for error in [TimeoutError('SENSITIVE-PHONE'),urllib.error.URLError('SENSITIVE-DOB'),urllib.error.HTTPError('SENSITIVE-URL',429,'SENSITIVE-KEY',{},None)]:
            calls=[]
            def transport(req,timeout):
                calls.append(req)
                raise error
            output=io.StringIO()
            with contextlib.redirect_stdout(output),contextlib.redirect_stderr(output):
                with self.assertRaises(ApiError) as caught:
                    OpenAIIntent(api_key='synthetic-key',transport=transport).interpret('SENSITIVE-UTTERANCE',{})
            self.assertEqual(len(calls),1)
            self.assertEqual(caught.exception.code,'model_unavailable')
            self.assertNotIn('SENSITIVE',str(caught.exception))
            self.assertEqual(output.getvalue(),'')
            self.assertTrue(caught.exception.__suppress_context__)

    def test_refusal_incomplete_and_malformed_outputs_fail_closed(self):
        malformed=[b'not json',json.dumps({'status':'incomplete','output':[]}).encode(),json.dumps({'status':'completed','output':[{'type':'message','content':[{'type':'refusal','refusal':'SENSITIVE'}]}]}).encode()]
        for raw in malformed:
            with self.assertRaises(ApiError) as caught:
                OpenAIIntent(api_key='synthetic-key',transport=lambda req,timeout:raw).interpret('hello',{})
            self.assertEqual(caught.exception.code,'invalid_model_output')

    def test_configuration_env_and_invalid_timeout_no_network(self):
        captured=[]
        with patch.dict(os.environ,{'OPENAI_API_KEY':'synthetic-env-key','OPENAI_MODEL':'explicit-env-model'}):
            adapter=OpenAIIntent(transport=lambda req,timeout:(captured.append(json.loads(req.data)) or response({'intent':'unknown','fields':{}})))
            adapter.interpret('hello',{})
        self.assertEqual(captured[0]['model'],'explicit-env-model')
        for timeout in (0,-1,float('inf'),float('nan'),True):
            with self.assertRaises(ApiError): OpenAIIntent(api_key='synthetic-key',timeout=timeout)
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(ApiError) as caught: OpenAIIntent().interpret('hello',{})
            self.assertEqual(caught.exception.code,'bad_configuration')

class IntentBoundaryRegressionTests(unittest.TestCase):
    def test_offline_supplied_mock_phone_and_choice_words(self):
        adapter=OfflineIntent()
        self.assertEqual(adapter.interpret('phone 555-0101 DOB 1985-04-12',{'intent':'book'}).fields,{'phone':'555-0101','dob':'1985-04-12'})
        for text in ('first','earliest','choice1'):
            self.assertEqual(adapter.interpret(text,{'intent':'book','state':'offering'}).fields,{'selection':'1'})
        for text in ('yes','no'):
            self.assertEqual(adapter.interpret(text,{'intent':'book'}).intent,'unknown')

    def test_context_values_never_crash_or_leak_when_not_enums(self):
        captured=[]
        adapter=OpenAIIntent(api_key='synthetic-key',transport=lambda req,timeout:(captured.append(req.data.decode()) or response({'intent':'unknown','fields':{}})))
        adapter.interpret('hello',{'state':['SENSITIVE'],'intent':{'SENSITIVE':'value'},'needed':['phone',{'SENSITIVE':'value'}]})
        self.assertNotIn('SENSITIVE',captured[0])

    def test_live_exact_schema_rejects_missing_field_names(self):
        raw=json.dumps({'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':'{"intent":"unknown","fields":{}}'}]}]}).encode()
        with self.assertRaises(ApiError):
            OpenAIIntent(api_key='synthetic-key',transport=lambda req,timeout:raw).interpret('hello',{})

class OfflineCorrectionTests(unittest.TestCase):
    def test_selection_can_change_while_awaiting_confirmation(self):
        self.assertEqual(OfflineIntent().interpret('2',{'state':'awaiting_confirmation','intent':'book','needed':[]}).fields,{'selection':'2'})
    def test_zip_only_followup_is_retained_in_identity_clarification(self):
        self.assertEqual(OfflineIntent().interpret('70115',{'state':'clarifying_identity','intent':'book','needed':['zip']}).fields,{'zip':'70115'})

class OfflineNaturalAnswerTests(unittest.TestCase):
    def test_explicit_date_of_birth_phrase(self):
        self.assertEqual(OfflineIntent().interpret('My date of birth is 1985-04-12',{'intent':'book','needed':['dob']}).fields,{'dob':'1985-04-12'})

class OfflineZipAnswerTests(unittest.TestCase):
    def test_zip_code_is_phrase(self):
        self.assertEqual(OfflineIntent().interpret('My ZIP code is 70115',{'state':'clarifying_identity','intent':'book','needed':['zip']}).fields,{'zip':'70115'})
