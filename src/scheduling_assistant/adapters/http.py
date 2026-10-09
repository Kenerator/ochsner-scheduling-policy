"""Thin supplied-API adapter. Consequential requests are attempted exactly once."""
import json
import math
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from ..models import (validate_appointment, validate_criteria, validate_patient,
                      validate_provider, validate_slot)
from ..ports import ApiError


class _NoRedirect(HTTPRedirectHandler):
    # A redirect cannot silently move patient data or replay a booking request.
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class HttpSchedulingAPI:
    def __init__(self, base_url, scenario=None, timeout=5, transport=None):
        try:
            parsed = urlsplit(base_url)
            valid = (parsed.scheme == 'http' and parsed.hostname in {'localhost','127.0.0.1','::1'}
                     and not parsed.username and not parsed.password and not parsed.query
                     and not parsed.fragment and parsed.path in ('','/'))
            parsed.port
            valid = valid and isinstance(timeout,(int,float)) and math.isfinite(timeout) and timeout > 0
            valid = valid and (scenario is None or isinstance(scenario,str) and '\n' not in scenario and '\r' not in scenario)
        except (TypeError, ValueError):
            valid = False
        if not valid:
            raise ApiError('bad_configuration') from None
        self.base_url = base_url.rstrip('/')
        self.scenario = scenario
        self.timeout = timeout
        self.transport = transport or build_opener(_NoRedirect()).open

    @staticmethod
    def _identifier(value):
        if not isinstance(value,str) or not value.strip():
            raise ApiError('invalid_request')
        return value

    def _request(self, path, query=None, body=None):
        write = body is not None
        url = self.base_url + path
        if query:
            url += '?' + urlencode(query)
        headers = {'Accept':'application/json'}
        if self.scenario is not None:
            headers['X-Mock-Scenario'] = self.scenario
        raw = None
        if write:
            headers['Content-Type'] = 'application/json'
            raw = json.dumps(body).encode('utf-8')
        request = Request(url, data=raw, headers=headers, method='POST' if write else 'GET')
        status = None
        try:
            try:
                response = self.transport(request, timeout=self.timeout)
            except HTTPError as error:
                response = error
            with response:
                status = response.status
                payload = json.loads(response.read())
        except (URLError, OSError, HTTPException, ValueError, UnicodeError):
            raise ApiError('unknown_write' if write else 'read_failure', status, unknown=write) from None
        if status != (201 if write else 200):
            allowed = {
                400: {'missing_parameter','invalid_parameter','unknown_patient','unknown_slot','confirmation_required','invalid_json'},
                409: {'slot_taken'},
                503: {'downstream_unavailable'},
            }
            if (isinstance(payload,dict) and isinstance(payload.get('code'),str)
                    and payload['code'] in allowed.get(status,set()) and isinstance(payload.get('message'),str)):
                raise ApiError(payload['code'],status) from None
            raise ApiError('unknown_write' if write else 'api_failure',status,unknown=write) from None
        if not isinstance(payload,dict):
            raise ApiError('malformed_response',status,unknown=write)
        return payload

    @staticmethod
    def _facts(payload, key, validator):
        try:
            values = payload[key]
            if not isinstance(values,list):
                raise ValueError()
            return [validator(value) for value in values]
        except (KeyError, TypeError, ValueError):
            raise ApiError('malformed_response',200) from None

    def providers(self, criteria):
        criteria = validate_criteria(criteria)
        query = {k:v for k,v in criteria.items() if k in ('specialty','location')}
        providers = self._facts(self._request('/providers',query), 'providers',validate_provider)
        if any((query.get('specialty') and p['specialty'] != query['specialty']) or
               (query.get('location') and query['location'] not in p['locations']) for p in providers):
            raise ApiError('malformed_response',200)
        return providers

    def patient_matches(self, phone, dob):
        self._identifier(phone)
        self._identifier(dob)
        matches = self._facts(self._request('/patients/search',{'phone':phone,'dob':dob}), 'matches',validate_patient)
        if any(p['phone'] != phone or p['dateOfBirth'] != dob for p in matches):
            raise ApiError('malformed_response',200)
        return matches

    def availability(self, patient_id, criteria):
        self._identifier(patient_id)
        criteria = validate_criteria(criteria,require_specialty=True)
        slots = self._facts(self._request('/availability',{'patientId':patient_id,**criteria}), 'slots',validate_slot)
        if any(s['specialty'] != criteria['specialty'] or
               (criteria.get('location') and s['location'] != criteria['location']) or
               (criteria.get('startDate') and s['startTime'][:10] < criteria['startDate']) or
               (criteria.get('endDate') and s['startTime'][:10] > criteria['endDate']) for s in slots):
            raise ApiError('malformed_response',200)
        return [s for s in slots if s['available']]

    def book(self, patient_id, slot_id):
        self._identifier(patient_id)
        self._identifier(slot_id)
        # Only the guarded core calls this operation after binding explicit consent.
        payload = self._request('/appointments',body={'patientId':patient_id,'slotId':slot_id,'confirmed':True})
        try:
            appointment = validate_appointment(payload['appointment'])
            if appointment['patientId'] != patient_id:
                raise ValueError()
        except (KeyError, TypeError, ValueError):
            raise ApiError('malformed_response',201,unknown=True) from None
        return appointment
