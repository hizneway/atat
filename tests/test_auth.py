import os
from datetime import datetime
from urllib.parse import urlparse

import pendulum
import pytest
from flask import session, url_for

from atat.domain.auth import UNPROTECTED_ROUTES
from atat.domain.exceptions import NotFoundError
from atat.domain.users import Users

from .factories import UserFactory
from .utils import FakeLogger

MOCK_USER = {"id": "438567dd-25fa-4d83-a8cc-8aa8366cb24a"}


def _fetch_user_info(c, t):
    return MOCK_USER


def _login(*args, **kwargs):
    raise NotImplementedError("needs to be reimplemented")


# checks that all of the routes in the app are protected by auth
def is_unprotected(rule):
    return rule.endpoint in UNPROTECTED_ROUTES


def protected_routes(app):
    for rule in app.url_map.iter_rules():
        args = [1] * len(rule.arguments)
        mock_args = dict(zip(rule.arguments, args))
        _n, route = rule.build(mock_args)
        if is_unprotected(rule) or "/static" in route:
            continue
        yield rule, route


def test_protected_routes_redirect_to_login(client, app):
    server_name = app.config.get("SERVER_NAME") or "localhost"
    for rule, protected_route in protected_routes(app):
        if "GET" in rule.methods:
            resp = client.get(protected_route)
            assert resp.status_code == 302
            assert server_name in resp.headers["Location"]

        if "POST" in rule.methods:
            resp = client.post(protected_route)
            assert resp.status_code == 302
            assert server_name in resp.headers["Location"]


def test_unprotected_routes_set_user_if_logged_in(client, app, user_session):
    user = UserFactory.create()

    resp = client.get(url_for("atat.about"))
    assert resp.status_code == 200
    assert user.full_name not in resp.data.decode()

    user_session(user)
    resp = client.get(url_for("atat.about"))
    assert resp.status_code == 200
    assert user.full_name in resp.data.decode()


@pytest.mark.skip("re-implement after fed auth")
def test_logout(app, client, monkeypatch, mock_logger):
    user = UserFactory.create()
    # create a real session
    resp = _login(client)
    resp_success = client.get(url_for("users.user"))
    # verify session is valid
    assert resp_success.status_code == 200
    client.get(url_for("atat.logout"))
    resp_failure = client.get(url_for("users.user"))
    # verify that logging out has cleared the session
    assert resp_failure.status_code == 302
    destination = urlparse(resp_failure.headers["Location"]).path
    assert destination == url_for("atat.root")
    # verify that logout is noted in the logs
    logout_msg = mock_logger.messages[-1]
    assert user.dod_id in logout_msg
    assert "logged out" in logout_msg


@pytest.mark.skip("re-implement after fed auth")
def test_logging_out_creates_a_flash_message(app, client, monkeypatch):
    _login(client)
    logout_response = client.get(url_for("atat.logout"), follow_redirects=True)

    assert "Logged out" in logout_response.data.decode()


@pytest.mark.skip("re-implement after fed auth")
def test_redirected_on_login(client, monkeypatch):
    target_route = url_for("users.user")
    response = _login(client, next=target_route)
    assert target_route in response.headers.get("Location")


@pytest.mark.skip("re-implement after fed auth")
def test_last_login_set_when_user_logs_in(client, monkeypatch):
    last_login = pendulum.now(tz="UTC")
    user = UserFactory.create(last_login=last_login)
    _login(client)
    assert session["last_login"]
    assert user.last_login > session["last_login"]
    assert isinstance(session["last_login"], datetime)
