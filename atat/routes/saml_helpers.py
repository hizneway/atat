from urllib.parse import urlparse, parse_qs
from random import randint
from flask import current_app as app, session, g
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from atat.domain.exceptions import UnauthenticatedError, NotFoundError
from atat.domain.users import Users


def saml_get(saml_auth, request):
    if "qs_dict" in session:
        del session["qs_dict"]
    sso_built_url = saml_auth.login()
    session["AuthNRequestID"] = saml_auth.get_last_request_id()
    parsed_url = urlparse(request.url)
    parsed_qs = parse_qs(parsed_url.query)
    next_param = next(iter(parsed_qs.get("next") or []), None)
    username_param = next(iter(parsed_qs.get("username") or []), None)
    dod_id_param = next(iter(parsed_qs.get("dod_id") or []), None)
    qs_dict = {}

    if next_param:
        qs_dict["next_param"] = next_param
    if username_param:
        qs_dict["username_param"] = username_param
    if dod_id_param:
        qs_dict["dod_id_param"] = dod_id_param
    if qs_dict:
        session["qs_dict"] = qs_dict

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

        qs_dict = session.get("qs_dict", {})
        if "username_param" in qs_dict or "dod_id_param" in qs_dict:
            return None
        else:
            # if username or dod_id param not passed in,
            # we get or create user from SAML information
            saml_user_details = {}
            saml_user_details["first_name"] = saml_auth.get_attribute(
                "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname"
            )[0]
            saml_user_details["last_name"] = saml_auth.get_attribute(
                "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname"
            )[0]
            try:
                user = Users.get_by_first_and_last_name(
                    saml_user_details["first_name"], saml_user_details["last_name"]
                )
            except NotFoundError:
                new_dod_id = unique_dod_id()

                created_user = Users.create(new_dod_id, **saml_user_details)
                return created_user
            return user

    else:
        app.logger.error(
            f"SAML response from IdP contained the following errors: {', '.join(errors)}"
        )
        raise UnauthenticatedError("SAML Authentication Failed")


def unique_dod_id():
    new_dod_id = f"{randint(0,99999999):09}"
    existing_dod_ids = Users.get_all_dod_ids()
    if new_dod_id in existing_dod_ids:
        unique_dod_id()
    else:
        return new_dod_id


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
