import os
import urllib.parse as url

from flask import Blueprint
from flask import current_app as app
from flask import g, make_response, redirect, render_template, request, session, url_for
from jinja2.exceptions import TemplateNotFound
from werkzeug.exceptions import MethodNotAllowed, NotFound
from werkzeug.routing import RequestRedirect

from atat.domain.auth import logout as _logout
from atat.domain.authnid import AuthenticationContext
from atat.domain.exceptions import UnauthenticatedError
from atat.domain.users import Users
from atat.routes.saml_helpers import init_saml_auth
from atat.utils.flash import formatted_flash as flash
from atat.routes.saml_helpers import saml_get, saml_post, init_saml_auth

bp = Blueprint("atat", __name__)


@bp.route("/")
def root():
    if g.current_user:
        return redirect(url_for(".home"))

    redirect_url = app.config.get("CAC_URL")
    if request.args.get("next"):
        redirect_url = url.urljoin(
            redirect_url,
            "?{}".format(url.urlencode({"next": request.args.get("next")})),
        )
        flash("login_next")

    return render_template("login.html", redirect_url=redirect_url)


@bp.route("/home")
def home():
    return render_template("home.html")


def _client_s_dn():
    return request.environ.get("HTTP_X_SSL_CLIENT_S_DN")


def _make_authentication_context():
    return AuthenticationContext(
        crl_cache=app.crl_cache,
        auth_status=request.environ.get("HTTP_X_SSL_CLIENT_VERIFY"),
        sdn=_client_s_dn(),
        cert=request.environ.get("HTTP_X_SSL_CLIENT_CERT"),
    )


def redirect_after_login_url(next_param=None):
    returl = next_param or request.args.get("next")
    if match_url_pattern(returl):
        param_name = request.args.get(app.form_cache.PARAM_NAME)
        if param_name:
            returl += "?" + url.urlencode({app.form_cache.PARAM_NAME: param_name})
        return returl
    else:
        return url_for("atat.home")


def match_url_pattern(url, method="GET"):
    """Ensure a url matches a url pattern in the flask app
    inspired by https://stackoverflow.com/questions/38488134/get-the-flask-view-function-that-matches-a-url/38488506#38488506
    """
    server_name = app.config.get("SERVER_NAME") or "localhost"
    adapter = app.url_map.bind(server_name=server_name)

    try:
        match = adapter.match(url, method=method)
    except RequestRedirect as e:
        # recursively match redirects
        return match_url_pattern(e.new_url, method)
    except (MethodNotAllowed, NotFound):
        # no match
        return None

    if match[0] in app.view_functions:
        return url


def current_user_setup(user):
    session["user_id"] = user.id
    session["last_login"] = user.last_login
    app.session_limiter.on_login(user)
    app.logger.info("authentication succeeded for user with EDIPI %s", user.dod_id)
    Users.update_last_login(user)


@bp.route("/login-redirect")
def login_redirect():
    try:
        auth_context = _make_authentication_context()
        auth_context.authenticate()

        user = auth_context.get_user()
        current_user_setup(user)
    except UnauthenticatedError as err:
        app.logger.info(
            "authentication failed for subject distinguished name %s", _client_s_dn()
        )
        raise err

    return redirect(redirect_after_login_url())


@bp.route("/logout")
def logout():
    login_method = session.pop("login_method", "main")
    _logout()
    logout_url = url_for(".root")

    if login_method == "dev":
        app.logger.info("preparing dev logout")
        saml_auth = init_saml_auth(request)
        logout_url = saml_auth.logout(return_to=logout_url)
        app.logger.info(f"update logout url to {logout_url}")

    response = make_response(redirect(logout_url))
    response.set_cookie("expandSidenav", "", expires=0, httponly=True)
    flash("logged_out")
    return response


@bp.route("/about")
def about():
    return render_template("about.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        saml_auth = init_saml_auth(request)
        return redirect(saml_get(saml_auth, request))

    if "acs" in request.args and request.method == "POST":
        saml_auth = init_saml_auth(request)
        saml_post(saml_auth)

        saml_user_details = {}
        saml_user_details["first_name"] = saml_auth.get_attribute(
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname"
        )[0]
        saml_user_details["last_name"] = saml_auth.get_attribute(
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname"
        )[0]
        saml_user_details["email"] = saml_auth.get_attribute(
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
        )[0]
        sam_account_name = saml_auth.get_attribute("samAccountName")[0]
        dod_id, short_designation = sam_account_name.split(".")
        if short_designation == "MIL":
            saml_user_details["designation"] = "miltary"
        elif short_designation == "CIV":
            saml_user_details["designation"] = "civilian"
        elif short_designation == "CTR":
            saml_user_details["designation"] = "contractor"
        # TODO: Do we need to add phone, agency
        user = Users.get_or_create_by_dod_id(dod_id, **saml_user_details)

    query_string_parameters = session.get("query_string_parameters", {})
    next_param = query_string_parameters.get("next_param", None)
    if "query_string_parameters" in session:
        del session["query_string_parameters"]
    current_user_setup(user)
    return redirect(redirect_after_login_url(next_param))
