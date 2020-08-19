import re
import string

import requests
from flask import current_app as app
from msrestazure.azure_cloud import AZURE_PUBLIC_CLOUD as cloud


def make_auth_header(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def generate_user_principal_name(name, domain_name):
    mail_name = generate_mail_nickname(name)
    return f"{mail_name}@{domain_name}.{app.config.get('OFFICE_365_DOMAIN')}"


ESCAPED_PUNCTUATION = re.escape(string.punctuation)


def generate_mail_nickname(name):
    return re.sub(f"[{ESCAPED_PUNCTUATION} ]+", ".", name).lower()


def get_principal_auth_token(tenant_id, payload):
    """Returns an OAuth Access token for a User or Service Principal

    args:
        tenant_id (str)
        payload (UserPrincipalTokenPayload or ServicePrincipalTokenPayload)
    returns:
        str: token
        or
        None
    """

    url = f"{cloud.endpoints.active_directory}/{tenant_id}/oauth2/v2.0/token"
    response = requests.post(url, data=payload.dict(), timeout=30)
    response.raise_for_status()
    token = response.json().get("access_token")
    return token


def create_active_directory_user(graph_token, graph_resource, payload):
    request_body = {
        "accountEnabled": True,
        "displayName": payload.display_name,
        "mailNickname": payload.mail_nickname,
        "userPrincipalName": payload.user_principal_name,
        "passwordProfile": {
            "forceChangePasswordNextSignIn": True,
            "password": payload.password,
        },
    }

    url = f"{graph_resource}/v1.0/users"

    return requests.post(
        url, headers=make_auth_header(graph_token), json=request_body, timeout=30,
    )
