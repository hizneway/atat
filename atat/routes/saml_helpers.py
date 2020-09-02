from random import randint
import re
from urllib.parse import parse_qs, urlparse

from flask import current_app as app, g, session

from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.errors import OneLogin_Saml2_ValidationError
from onelogin.saml2.idp_metadata_parser import OneLogin_Saml2_IdPMetadataParser
from atat.domain.exceptions import NotFoundError, UnauthenticatedError
from atat.domain.users import Users
from atat.utils import first_or_none


SAM_ACCOUNT_FORMAT = re.compile("(1\d{9})\.(MIL|CIV|CTR)")


class EIFSAttributes:
    GIVEN_NAME = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname"
    LAST_NAME = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname"
    EMAIL = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
    # SAM Account Name provides both DoD ID and Short Designation (military/civlian/contractor)
    # Name is provided in format 1234567890.MIL
    SAM_ACCOUNT_NAME = "samAccountName"
    US_CITIZEN = "extensionAttribute4"
    AGENCY_CODE = "extensionAttribute1"
    MOBILE = "mobile"


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

    try:
        saml_auth.process_response(request_id=request_id)
    except OneLogin_Saml2_ValidationError as error_message:
        app.logger.error(f"OneLogin_Saml2_ValidationError detected: {error_message}")
        raise UnauthenticatedError("SAML Validation Failed")
    errors = saml_auth.get_errors()
    if len(errors) == 0:
        if "AuthNRequestID" in session:
            del session["AuthNRequestID"]
    else:
        app.logger.error(
            f"SAML response from IdP contained the following errors: {', '.join(errors)}"
        )
        app.logger.error(saml_auth.get_last_error_reason())
        raise UnauthenticatedError("SAML Authentication Failed")


def unique_dod_id():
    new_dod_id = f"{randint(0,99999999):09}"  # nosec
    try:
        Users.get_by_dod_id(new_dod_id)
    except NotFoundError:
        return new_dod_id
    return unique_dod_id()


def init_saml_auth(request):
    saml_request_config = _prepare_flask_request(request)
    saml_auth_config = _make_saml_config()
    auth = OneLogin_Saml2_Auth(saml_request_config, saml_auth_config)
    saml_settings = auth.get_settings()
    metadata = saml_settings.get_sp_metadata()
    errors = saml_settings.validate_metadata(metadata)
    if len(errors) != 0:
        app.logger.error("Error found on Metadata: %s" % (", ".join(errors)))
        raise UnauthenticatedError("SAML Metadata Validation Failed")
    else:
        return auth


def init_saml_auth_dev(request):
    saml_request_config = _prepare_flask_request(request)
    saml_auth_config = _make_dev_saml_config()
    auth = OneLogin_Saml2_Auth(saml_request_config, saml_auth_config)
    saml_settings = auth.get_settings()
    metadata = saml_settings.get_sp_metadata()
    errors = saml_settings.validate_metadata(metadata)
    if len(errors) != 0:
        app.logger.error("Error found on Metadata: %s" % (", ".join(errors)))
        raise UnauthenticatedError("SAML Metadata Validation Failed")
    else:
        return auth


def _prepare_flask_request(request):
    """
    Prepares a request object for use in building the SAML request.
    Since we use an AD FS SAML Identity Provider, we need to ensure
    that lowercase_urlencoding is enabled, per https://github.com/onelogin/python-saml/pull/144
    """
    url_data = urlparse(request.url)
    return {
        "https": "on" if request.scheme == "https" else "off",
        "http_host": request.host,
        "server_port": url_data.port,
        "script_name": request.path,
        "get_data": request.args.copy(),
        "lowercase_urlencoding": True,  # Required by ADFS
        "post_data": request.form.copy(),
    }


def _make_dev_saml_config():
    config = {
        "strict": True,
        "debug": True,
        "sp": {
            "entityId": app.config["SAML_DEV_ENTITY_ID"],
            "assertionConsumerService": {
                "url": app.config["SAML_DEV_ACS"],
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
            },
            "singleLogoutService": {
                "url": app.config["SAML_DEV_SLS"],
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
        },
    }

    idp_config = OneLogin_Saml2_IdPMetadataParser.parse_remote(
        app.config["SAML_DEV_IDP_URI"], validate_cert=False
    )
    config["idp"] = idp_config["idp"]
    return config


def _make_saml_config():
    config = {
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
            "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
        },
        "security": {
            "wantAssertionsSigned": True,  # Needed by EIFS
            "requestedAuthnContext": False,  # Needed by EIFS
        },
    }

    idp_config = OneLogin_Saml2_IdPMetadataParser.parse_remote(
        app.config["SAML_IDP_URI"], validate_cert=False
    )
    config["idp"] = idp_config["idp"]
    return config
