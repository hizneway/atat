import re
import pytest
import tornado.web
import tornado.gen

MOCK_USER = {"id": "438567dd-25fa-4d83-a8cc-8aa8366cb24a"}
@tornado.gen.coroutine
def _fetch_user_info(c, t):
    return MOCK_USER

@pytest.mark.gen_test
def test_redirects_when_not_logged_in(http_client, base_url):
    response = yield http_client.fetch(
        base_url + "/home", raise_error=False, follow_redirects=False
    )
    location = response.headers["Location"]
    assert response.code == 302
    assert response.error
    assert re.match("/\??", location)


@pytest.mark.gen_test
def test_redirects_when_session_does_not_exist(monkeypatch, http_client, base_url):
    monkeypatch.setattr("atst.handlers.main.Main.get_secure_cookie", lambda s,c: 'stale cookie!')
    response = yield http_client.fetch(
        base_url + "/home", raise_error=False, follow_redirects=False
    )
    location = response.headers["Location"]
    cookie = response.headers._dict.get('Set-Cookie')
    # should clear session cookie
    assert 'atat=""' in cookie
    assert response.code == 302
    assert response.error
    assert re.match("/\??", location)


@pytest.mark.gen_test
def test_login_with_valid_bearer_token(app, monkeypatch, http_client, base_url):
    monkeypatch.setattr("atst.handlers.login_redirect.LoginRedirect._fetch_user_info", _fetch_user_info)
    response = yield http_client.fetch(
        base_url + "/login-redirect?bearer-token=abc-123",
        follow_redirects=False,
        raise_error=False,
    )
    assert response.headers["Set-Cookie"].startswith("atat")
    assert response.headers["Location"] == "/home"
    assert response.code == 302


@pytest.mark.gen_test
def test_login_via_dev_endpoint(app, http_client, base_url):
    response = yield http_client.fetch(
        base_url + "/login-dev", raise_error=False, follow_redirects=False
    )
    assert response.headers["Set-Cookie"].startswith("atat")
    assert response.code == 302
    assert response.headers["Location"] == "/home"


@pytest.mark.gen_test
@pytest.mark.skip(reason="need to work out auth error user paths")
def test_login_with_invalid_bearer_token(http_client, base_url):
    _response = yield http_client.fetch(
        base_url + "/home",
        raise_error=False,
        headers={"Cookie": "bearer-token=anything"},
    )

@pytest.mark.gen_test
def test_valid_login_creates_session(app, monkeypatch, http_client, base_url):
    monkeypatch.setattr("atst.handlers.login_redirect.LoginRedirect._fetch_user_info", _fetch_user_info)
    assert len(app.sessions.sessions) == 0
    yield http_client.fetch(
        base_url + "/login-redirect?bearer-token=abc-123",
        follow_redirects=False,
        raise_error=False,
    )
    assert len(app.sessions.sessions) == 1
    session = list(app.sessions.sessions.values())[0]
    assert "atat_permissions" in session["user"]
    assert isinstance(session["user"]["atat_permissions"], list)
