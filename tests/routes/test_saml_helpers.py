from unittest.mock import Mock

import pytest
from flask import current_app, session
from tests.factories import UserFactory

from atat.domain.exceptions import UnauthenticatedError
from atat.routes import get_user_from_saml_attributes
from atat.routes.saml_helpers import (
    EIFSAttributes,
    _cache_params_in_session,
    saml_get,
)


def test_saml_get_success():
    request = Mock(args={})
    saml_auth = Mock(
        login=lambda: "https://idp.saml", get_last_request_id=lambda: "ABC123"
    )

    login_url = saml_get(saml_auth, request)

    assert login_url == "https://idp.saml"
    assert session["AuthNRequestID"] == "ABC123"


def test_qp_cache_success():
    request = Mock(
        args={
            "next": "https://sp.com/deep/link",
            "username": "Amanda",
            "dod_id": "1234567890",
        }
    )

    _cache_params_in_session(request)

    qsp = session["query_string_parameters"]
    assert qsp["next_param"] == "https://sp.com/deep/link"
    assert qsp["username_param"] == "Amanda"
    assert qsp["dod_id_param"] == "1234567890"


def test_qp_cache_cleared():
    request = Mock(args={})

    session["query_string_parameters"] = {"next_param": "https://gone.com"}
    _cache_params_in_session(request)

    assert "query_string_parameters" not in session



def test_get_user_from_saml_attributes():
    expected_dod_id = "1234567890"
    saml_attributes = {
        EIFSAttributes.GIVEN_NAME: [""],
        EIFSAttributes.LAST_NAME: [""],
        EIFSAttributes.EMAIL: [""],
        EIFSAttributes.SAM_ACCOUNT_NAME: [f"{expected_dod_id}.MIL"],
        EIFSAttributes.US_CITIZEN: ["Y"],
        EIFSAttributes.AGENCY_CODE: ["F"],
        EIFSAttributes.MOBILE: [""],
    }
    user = get_user_from_saml_attributes(saml_attributes)
    assert user.dod_id == expected_dod_id
    assert user.designation == "military"
    assert user.citizenship == "United States"
    assert user.service_branch == "air_force"


def test_get_user_from_saml_attributes_missing_dod_id():
    saml_attributes = {
        EIFSAttributes.GIVEN_NAME: [""],
        EIFSAttributes.LAST_NAME: [""],
        EIFSAttributes.EMAIL: [""],
        EIFSAttributes.US_CITIZEN: [""],
        EIFSAttributes.AGENCY_CODE: [""],
        EIFSAttributes.MOBILE: [""],
    }
    with pytest.raises(Exception):
        get_user_from_saml_attributes(saml_attributes)


def test_get_user_from_saml_invalid_sam_format():
    saml_attributes = {
        EIFSAttributes.GIVEN_NAME: [""],
        EIFSAttributes.LAST_NAME: [""],
        EIFSAttributes.SAM_ACCOUNT_NAME: ["sam account name format changed"],
        EIFSAttributes.EMAIL: [""],
        EIFSAttributes.US_CITIZEN: [""],
        EIFSAttributes.AGENCY_CODE: [""],
        EIFSAttributes.MOBILE: [""],
    }
    with pytest.raises(Exception):
        get_user_from_saml_attributes(saml_attributes)


def test_get_user_from_saml_existing_user():
    expected_dod_id = "1234567890"
    saml_attributes = {
        EIFSAttributes.GIVEN_NAME: [""],
        EIFSAttributes.LAST_NAME: [""],
        EIFSAttributes.EMAIL: [""],
        EIFSAttributes.SAM_ACCOUNT_NAME: [f"{expected_dod_id}.MIL"],
        EIFSAttributes.US_CITIZEN: [""],
        EIFSAttributes.AGENCY_CODE: [""],
        EIFSAttributes.MOBILE: [""],
    }
    expected_user = UserFactory.create(dod_id=expected_dod_id)

    assert expected_user == get_user_from_saml_attributes(saml_attributes)
