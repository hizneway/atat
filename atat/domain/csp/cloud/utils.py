import re
import string

import requests
from flask import current_app as app
from msrestazure.azure_cloud import AZURE_PUBLIC_CLOUD as cloud


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
