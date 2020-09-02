import pytest

from tests.factories import UserFactory
from atat.routes import get_user_from_saml_attributes
from atat.routes.saml_helpers import EIFSAttributes


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
