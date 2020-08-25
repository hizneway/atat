from random import randint
from urllib.parse import parse_qs, urlparse

from flask import current_app as app
from flask import g, session
from onelogin.saml2.auth import OneLogin_Saml2_Auth

from atat.domain.exceptions import NotFoundError, UnauthenticatedError
from atat.domain.users import Users
from atat.utils import first_or_none


def saml_get(saml_auth, request):
    if "query_string_parameters" in session:
        del session["query_string_parameters"]
    sso_built_url = saml_auth.login()
    session["AuthNRequestID"] = saml_auth.get_last_request_id()
    parsed_url = urlparse(request.url)
    parsed_query_string = parse_qs(parsed_url.query)
    next_param = first_or_none(lambda no_op: True, parsed_query_string.get("next", []))
    username_param = first_or_none(
        lambda no_op: True, parsed_query_string.get("username", [])
    )
    dod_id_param = first_or_none(
        lambda no_op: True, parsed_query_string.get("dod_id", [])
    )
    query_string_parameters = {}

    if next_param:
        query_string_parameters["next_param"] = next_param
    if username_param:
        query_string_parameters["username_param"] = username_param
    if dod_id_param:
        query_string_parameters["dod_id_param"] = dod_id_param
    if query_string_parameters:
        session["query_string_parameters"] = query_string_parameters

    return sso_built_url


def saml_post(saml_auth):
    request_id = None
    if "AuthNRequestID" in session:
        request_id = session["AuthNRequestID"]

    saml_auth.process_response(request_id=request_id)
    errors = saml_auth.get_errors()
    if len(errors) == 0:
        if "AuthNRequestID" in session:
            del session["AuthNRequestID"]
    else:
        app.logger.error(
            f"SAML response from IdP contained the following errors: {', '.join(errors)}"
        )
        raise UnauthenticatedError("SAML Authentication Failed")


def unique_dod_id():
    new_dod_id = f"{randint(0,99999999):09}"  # nosec
    try:
        Users.get_by_dod_id(new_dod_id)
    except NotFoundError:
        return new_dod_id
    return unique_dod_id()


def init_saml_auth(request):
    saml_request_config = prepare_flask_request(request)
    saml_auth_config = _make_saml_config()
    auth = OneLogin_Saml2_Auth(saml_request_config, saml_auth_config)
    return auth


def prepare_flask_request(request):
    # If server is behind proxys or balancers use the HTTP_X_FORWARDED fields
    url_data = urlparse(request.url)
    return {
        "https": "on" if request.scheme == "https" else "off",
        "http_host": request.host,
        "server_port": url_data.port,
        "script_name": request.path,
        "get_data": request.args.copy(),
        # Uncomment if using ADFS as IdP, https://github.com/onelogin/python-saml/pull/144
        # 'lowercase_urlencoding': True,
        "post_data": request.form.copy(),
    }


def _make_saml_config():
    return {
        "strict": True,
        "debug": g.dev,
        "sp": {
            "entityId": app.config["SAML_ENTITY_ID"],
            "assertionConsumerService": {
                "url": app.config["SAML_ACS"],
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
            },
            "singleLogoutService": {
                "url": app.config["SAML_SLS"],
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified",
            "x509cert": "",
            "privateKey": "",
        },
        "idp": {
            "entityId": app.config["SAML_IDP_ENTITY_ID"],
            "singleSignOnService": {
                "url": app.config["SAML_IDP_SSOS"],
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "singleLogoutService": {
                "url": app.config["SAML_IDP_SLS"],
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "x509cert": app.config["SAML_IDP_CERT"],
        },
    }
