"""Boundary tests: reject unusable service facts before they reach a workflow."""
import unittest
from scheduling_assistant.models import (Conversation, validate_patient, validate_provider,
    validate_slot, validate_appointment, validate_criteria)
from scheduling_assistant.ports import ApiError

PATIENT=dict(patientId='pat_x',firstName='Synthetic',lastName='Person',phone='555-0101',dateOfBirth='1985-04-12',zipCode='70112',establishedPatient=True)
PROVIDER=dict(providerId='prov_x',name='Synthetic Doctor',specialty='primary_care',locations=['downtown'],modalities=['in_person'])
SLOT=dict(slotId='slot_x',providerId='prov_x',specialty='primary_care',location='downtown',startTime='2026-10-10T09:00:00-05:00',available=True)
APPOINTMENT=dict(appointmentId='apt_x',patientId='pat_x',providerId='prov_x',specialty='primary_care',location='downtown',startTime='2026-10-10T09:00:00-05:00',status='scheduled')

class BoundaryTests(unittest.TestCase):
    def test_missing_or_wrong_typed_service_facts_never_become_usable(self):
        for validate,value,key in [(validate_patient,PATIENT,'patientId'),(validate_provider,PROVIDER,'providerId'),(validate_slot,SLOT,'slotId'),(validate_appointment,APPOINTMENT,'appointmentId')]:
            with self.subTest(key=key):
                bad=dict(value);bad.pop(key)
                with self.assertRaises(ValueError):validate(bad)
                bad=dict(value);bad[key]=True
                with self.assertRaises(ValueError):validate(bad)
    def test_returned_time_is_preserved_and_naive_or_invalid_time_rejected(self):
        self.assertEqual(validate_slot(SLOT)['startTime'],'2026-10-10T09:00:00-05:00')
        for t in ['2026-10-10T09:00:00','not-a-time']:
            with self.assertRaises(ValueError):validate_slot(dict(SLOT,startTime=t))
    def test_fixture_only_values_are_not_application_facts(self):
        with self.assertRaises(ValueError):validate_slot(dict(SLOT,conflictOnBooking=True))
    def test_unavailable_slot_stays_unavailable(self):
        self.assertIs(validate_slot(dict(SLOT,available=False))['available'],False)
        with self.assertRaises(ValueError):validate_slot(dict(SLOT,available='true'))
    def test_criteria_reject_unknown_filters_dates_and_unsupported_values(self):
        for bad in [{'specialty':'cardiology'},{'location':'moon'},{'providerId':'prov_x'},{'startDate':'2026-02-30'},{'startDate':'2026-10-12','endDate':'2026-10-10'}]:
            with self.assertRaises(ValueError):validate_criteria(bad)
        self.assertEqual(validate_criteria({'specialty':'primary_care','location':'downtown'}),{'specialty':'primary_care','location':'downtown'})
    def test_conversation_state_is_isolated(self):
        a,b=Conversation(),Conversation();a.fields['phone']='sentinel';a.slots.append(dict(SLOT))
        self.assertNotEqual(a.session_id,b.session_id)
        self.assertEqual(b.fields,{});self.assertEqual(b.slots,[])
        self.assertNotIn('sentinel',repr(a))
    def test_errors_do_not_render_arbitrary_downstream_text(self):
        self.assertNotIn('PRIVATE_SENTINEL',str(ApiError('PRIVATE_SENTINEL',status=500,unknown=True)))
