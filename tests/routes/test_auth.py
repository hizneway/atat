from urllib.parse import quote

from flask import url_for

from tests.factories import UserFactory
from atat.routes import get_user_from_saml_attributes
import pytest

# TODO:  update w/ new home url
PROTECTED_URL = "/home"


def test_home_page_with_complete_profile(client, user_session):
    user = UserFactory.create()
    user_session(user)
    response = client.get(PROTECTED_URL, follow_redirects=False)
    assert response.status_code == 200


def test_redirect_when_profile_missing_fields(client, user_session):
    user = UserFactory.create(email=None)
    user_session(user)
    response = client.get(PROTECTED_URL, follow_redirects=False)
    assert response.status_code == 302
    assert "/user?next={}".format(quote(PROTECTED_URL, safe="")) in response.location


def test_unprotected_route_with_incomplete_profile(client, user_session):
    user = UserFactory.create()
    user_session(user)
    response = client.get("/about", follow_redirects=False)
    assert response.status_code == 200


def test_completing_user_profile(client, user_session):
    user = UserFactory.create(phone_number=None)
    user_session(user)
    response = client.get(PROTECTED_URL, follow_redirects=True)
    assert b"You must complete your profile" in response.data

    updated_data = {**user.to_dictionary(), "phone_number": "5558675309"}
    response = client.post(url_for("users.update_user"), data=updated_data)
    assert response.status_code == 200

    response = client.get(PROTECTED_URL, follow_redirects=False)
    assert response.status_code == 200
    assert b"You must complete your profile" not in response.data


def test_get_user_from_saml_attributes():
    expected_dod_id = "1234567890"
    saml_attributes = {
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname": [""],
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname": [""],
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress": [""],
        "samAccountName": [f"{expected_dod_id}.MIL"],
        "extensionAttribute4": ["Y"],
        "extensionAttribute1": ["F"],
        "mobile": [""],
    }
    user = get_user_from_saml_attributes(saml_attributes)
    assert user.dod_id == expected_dod_id
    assert user.designation == "military"
    assert user.citizenship == "United States"
    assert user.service_branch == "air_force"


def test_get_user_from_saml_attributes_missing_dod_id():
    saml_attributes = {
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname": [""],
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname": [""],
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress": [""],
        "extensionAttribute4": [""],
        "extensionAttribute1": [""],
        "mobile": [""],
    }
    with pytest.raises(Exception):
        get_user_from_saml_attributes(saml_attributes)


def test_get_user_from_saml_existing_user():
    expected_dod_id = "1234567890"
    saml_attributes = {
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname": [""],
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname": [""],
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress": [""],
        "samAccountName": [f"{expected_dod_id}.MIL"],
        "extensionAttribute4": [""],
        "extensionAttribute1": [""],
        "mobile": [""],
    }
    expected_user = UserFactory.create(dod_id=expected_dod_id)

    assert expected_user == get_user_from_saml_attributes(saml_attributes)
