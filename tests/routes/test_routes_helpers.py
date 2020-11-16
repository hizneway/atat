from atat.routes.routes_helpers import match_url_pattern


def test_valid_url():
    assert match_url_pattern("/home")


def test_invalid_url():
    assert not match_url_pattern("http://not.a.real.url.gov/#")
