import re
import pytest
import tornado
import urllib
from tests.mocks import MOCK_REQUEST, MOCK_USER
from tests.factories import PENumberFactory


class TestPENumberInForm:

    required_data = {
        "pe_id": "123",
        "task_order_id": "1234567899C0001",
        "fname_co": "Contracting",
        "lname_co": "Officer",
        "email_co": "jane@mail.mil",
        "office_co": "WHS",
        "fname_cor": "Officer",
        "lname_cor": "Representative",
        "email_cor": "jane@mail.mil",
        "office_cor": "WHS",
        "funding_type": "RDTE",
        "funding_type_other": "other",
        "clin_0001": "50,000",
        "clin_0003": "13,000",
        "clin_1001": "30,000",
        "clin_1003": "7,000",
        "clin_2001": "30,000",
        "clin_2003": "7,000",
    }

    def _set_monkeypatches(self, monkeypatch):
        monkeypatch.setattr("atst.forms.financial.FinancialForm.validate", lambda s: True)
        monkeypatch.setattr("atst.domain.requests.Requests.get", lambda i: MOCK_REQUEST)
        monkeypatch.setattr("atst.domain.auth.get_current_user", lambda *args: MOCK_USER)

    def submit_data(self, client, data):
        response = client.post(
            "/requests/verify/{}".format(MOCK_REQUEST.id),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=urllib.parse.urlencode(data),
            follow_redirects=False,
        )
        return response

    def test_submit_request_form_with_invalid_pe_id(self, monkeypatch, client):
        self._set_monkeypatches(monkeypatch)

        response = self.submit_data(client, self.required_data)

        assert "We couldn\'t find that PE number" in response.data.decode()
        assert response.status_code == 200

    def test_submit_request_form_with_unchanged_pe_id(self, monkeypatch, client):
        self._set_monkeypatches(monkeypatch)

        data = dict(self.required_data)
        data['pe_id'] = MOCK_REQUEST.body['financial_verification']['pe_id']

        response = self.submit_data(client, data)

        assert response.status_code == 302
        assert "/requests/financial_verification_submitted" in response.headers.get("Location")

    def test_submit_request_form_with_new_valid_pe_id(self, session, monkeypatch, client):
        self._set_monkeypatches(monkeypatch)
        pe = PENumberFactory.create(number="8675309U", description="sample PE number")
        session.add(pe)
        session.commit()

        data = dict(self.required_data)
        data['pe_id'] = pe.number

        response = self.submit_data(client, data)

        assert response.status_code == 302
        assert "/requests/financial_verification_submitted" in response.headers.get("Location")
