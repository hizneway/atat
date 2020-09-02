from urllib.parse import quote

from flask import url_for

from tests.factories import UserFactory

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
