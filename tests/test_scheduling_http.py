import io
import json
import unittest
from urllib.parse import parse_qs, urlsplit
from urllib.error import URLError
from scheduling_assistant.adapters.http import HttpSchedulingAPI
from scheduling_assistant.ports import ApiError
from scheduling_test_support import supplied_server
PATIENT = {'patientId':'p','firstName':'SensitiveName','lastName':'Name','phone':'private-phone','dateOfBirth':'1985-04-12','zipCode':'70112','establishedPatient':True}
SLOT = {'slotId':'s','providerId':'pr','specialty':'primary_care','location':'downtown','startTime':'2026-10-15T09:00:00-05:00','available':True}
APPOINTMENT = {k:v for k,v in SLOT.items() if k not in ('slotId','available')}
APPOINTMENT.update(appointmentId='a',patientId='p',status='scheduled')
class Response(io.BytesIO):
    def __init__(self,status,payload):
        super().__init__(payload if isinstance(payload,bytes) else json.dumps(payload).encode())
        self.status = status
class HttpTests(unittest.TestCase):
    def test_real_search_is_exact_and_zip_stays_local(self):
        with supplied_server() as (base,requests):
            api = HttpSchedulingAPI(base)
            matches = api.patient_matches('555-0130','1978-09-22')
            self.assertEqual({m['zipCode'] for m in matches},{'70115','70005'})
            self.assertEqual(parse_qs(requests[-1]['query']),{'phone':['555-0130'],'dob':['1978-09-22']})
            self.assertEqual(api.patient_matches(' 555-0130','1978-09-22'),[])
    def test_real_provider_lookup_requires_no_identity(self):
        with supplied_server() as (base,requests):
            providers = HttpSchedulingAPI(base).providers({'specialty':'primary_care','location':'uptown'})
            self.assertTrue(providers)
            self.assertTrue(all('uptown' in p['locations'] for p in providers))
            self.assertEqual(parse_qs(requests[-1]['query']),{'specialty':['primary_care'],'location':['uptown']})
    def test_real_availability_and_booking_use_exact_contract(self):
        with supplied_server() as (base,requests):
            api = HttpSchedulingAPI(base,scenario='success')
            slots = api.availability('pat_1001',{'specialty':'primary_care','location':'downtown'})
            self.assertTrue(slots)
            self.assertTrue(all(s['available'] and 'conflictOnBooking' not in s for s in slots))
            self.assertEqual(parse_qs(requests[-1]['query']),{'patientId':['pat_1001'],'specialty':['primary_care'],'location':['downtown']})
            appointment = api.book('pat_1001',slots[0]['slotId'])
            self.assertEqual(appointment['patientId'],'pat_1001')
            self.assertEqual(appointment['startTime'],slots[0]['startTime'])
            self.assertEqual(requests[-1]['body'],{'patientId':'pat_1001','slotId':slots[0]['slotId'],'confirmed':True})
            self.assertTrue(all(r['scenario']=='success' for r in requests))
    def test_real_conflict_and_outage_are_known_rejections(self):
        with supplied_server() as (base,requests):
            for api,slot,code,status in [(HttpSchedulingAPI(base),'slot_conflict_001','slot_taken',409),(HttpSchedulingAPI(base,scenario='api_failure'),'slot_4001','downstream_unavailable',503)]:
                with self.assertRaises(ApiError) as caught: api.book('pat_1001',slot)
                self.assertEqual((caught.exception.code,caught.exception.status,caught.exception.unknown),(code,status,False))
            self.assertEqual(len(requests),2)
    def invoke(self,status=200,payload=None,failure=None,write=False):
        calls = []
        def transport(request,timeout):
            calls.append((request,timeout))
            if failure: raise failure
            return Response(status,payload)
        api = HttpSchedulingAPI('http://127.0.0.1:1',scenario='api_failure',transport=transport)
        try:
            result = api.book('p','s') if write else api.patient_matches('private-phone','1985-04-12')
            return result,calls
        except ApiError as exc:
            self.assertEqual(len(calls),1)
            for secret in ('private-phone','SensitiveName','127.0.0.1','1985-04-12'): self.assertNotIn(secret,str(exc))
            raise
    def test_encoded_search_and_timeout_scenario(self):
        _,calls = self.invoke(payload={'matches':[PATIENT]})
        request,timeout = calls[0]
        self.assertEqual(timeout,5)
        self.assertEqual(parse_qs(urlsplit(request.full_url).query),{'phone':['private-phone'],'dob':['1985-04-12']})
        self.assertEqual(request.get_header('X-mock-scenario'),'api_failure')
    def test_bad_reads_are_safe_and_not_retried(self):
        for payload in (b'not json',{}, {'matches':{}}, {'matches':[{}]}, {'matches':[dict(PATIENT,phone='other')]}):
            with self.subTest(payload=payload),self.assertRaises(ApiError) as caught: self.invoke(payload=payload)
            self.assertFalse(caught.exception.unknown)
        with self.assertRaises(ApiError) as caught: self.invoke(failure=URLError('private-phone URL'))
        self.assertFalse(caught.exception.unknown)
    def test_uncertain_posts_freeze_outcome_and_never_retry(self):
        for status,payload in [(500,{'code':'internal_error','message':'private-phone'}),(200,{'appointment':APPOINTMENT}),(201,b'broken'),(201,{'appointment':{}}),(201,{'appointment':dict(APPOINTMENT,patientId='other')}),(409,{'code':'invalid_parameter','message':'x'}),(503,{})]:
            with self.subTest(status=status,payload=payload),self.assertRaises(ApiError) as caught: self.invoke(status,payload,write=True)
            self.assertTrue(caught.exception.unknown)
        for failure in (TimeoutError('private-phone'),URLError('private-phone')):
            with self.assertRaises(ApiError) as caught: self.invoke(failure=failure,write=True)
            self.assertTrue(caught.exception.unknown)
    def test_only_validated_errors_are_known_rejections(self):
        for status,code in [(400,'unknown_patient'),(409,'slot_taken'),(503,'downstream_unavailable')]:
            with self.assertRaises(ApiError) as caught: self.invoke(status,{'code':code,'message':'safe'},write=True)
            self.assertFalse(caught.exception.unknown)
            self.assertEqual(caught.exception.code,code)
    def test_service_schema_and_filter_mismatches_are_not_usable_facts(self):
        cases = [
            ('providers', {'providers':[{}]}, {'specialty':'primary_care'}),
            ('providers', {'providers':[{'providerId':'pr','name':'Provider','specialty':'dermatology','locations':['downtown'],'modalities':['in_person']}]}, {'specialty':'primary_care'}),
            ('availability', {'slots':[dict(SLOT, conflictOnBooking=True)]}, {'specialty':'primary_care'}),
            ('availability', {'slots':[dict(SLOT, available='true')]}, {'specialty':'primary_care'}),
            ('availability', {'slots':[dict(SLOT, location='uptown')]}, {'specialty':'primary_care','location':'downtown'}),
            ('availability', {'slots':[SLOT]}, {'specialty':'primary_care','startDate':'2026-10-16'}),
        ]
        for operation,payload,criteria in cases:
            with self.subTest(operation=operation,payload=payload):
                api = HttpSchedulingAPI('http://127.0.0.1:1',transport=lambda request,timeout:Response(200,payload))
                with self.assertRaises(ApiError) as caught:
                    api.providers(criteria) if operation == 'providers' else api.availability('p',criteria)
                self.assertFalse(caught.exception.unknown)
                self.assertEqual(caught.exception.code,'malformed_response')
    def test_unavailable_slots_are_never_offered_and_date_filters_are_sent(self):
        calls = []
        def transport(request,timeout):
            calls.append(request)
            return Response(200,{'slots':[dict(SLOT,available=False),dict(SLOT,slotId='open')]})
        api = HttpSchedulingAPI('http://127.0.0.1:1',transport=transport)
        slots = api.availability('p',{'specialty':'primary_care','startDate':'2026-10-15','endDate':'2026-10-15'})
        self.assertEqual([s['slotId'] for s in slots],['open'])
        self.assertEqual(parse_qs(urlsplit(calls[0].full_url).query),{'patientId':['p'],'specialty':['primary_care'],'startDate':['2026-10-15'],'endDate':['2026-10-15']})
    def test_base_url_and_timeout_configuration_fail_safely(self):
        for base in ('https://example.org','http://patient:secret@127.0.0.1','http://127.0.0.1?phone=private-phone'):
            with self.assertRaises(ApiError) as caught: HttpSchedulingAPI(base)
            self.assertEqual(str(caught.exception),'bad_configuration')
        for timeout in (0,-1,float('inf'),float('nan'),'5'):
            with self.assertRaises(ApiError): HttpSchedulingAPI('http://127.0.0.1:1',timeout=timeout)
    def test_unsupported_wire_parameters_rejected_before_transport(self):
        def forbidden(*args,**kwargs): self.fail('invalid request reached network')
        api = HttpSchedulingAPI('http://127.0.0.1:1',transport=forbidden)
        for action in (lambda:api.providers({'zip':'70112'}),lambda:api.availability('p',{'providerId':'pr'})):
            with self.assertRaises((ValueError,ApiError)): action()
if __name__ == '__main__': unittest.main()
