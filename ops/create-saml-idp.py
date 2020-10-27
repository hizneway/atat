#! /usr/bin/python

import click
import time
import requests
import os

from typing import NoReturn


@click.command()
@click.argument("tenant-id", )
@click.argument("application-id")
@click.argument("object-id")
@click.argument("password")
def main(tenant_id: str, application_id: str, object_id: str, password: str) -> NoReturn:

    # Authenticate with the provided service principle.

    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    data = {
        "grant_type": "client_credentials",
        "client_id": application_id,
        "client_secret": password,
        "scope": "https://graph.microsoft.com/.default"
    }

    response = requests.post(url, data=data)
    response.raise_for_status()
    access_token = response.json()["access_token"]

    # Create a new app registration from a template.

    url = "https://graph.microsoft.com/beta/applicationTemplates/8adf8e6e-67b2-4cf2-a259-e3dc5476c621/instantiate"
    data = '{ "displayName": "ATAT SAML Auth (Jesse)" }'

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, data=data, headers=headers)
    response.raise_for_status()

    sp_object_id = response.json()["servicePrincipal"]["objectId"]

    # Poll for the existence of the newly created service princple

    sp_exists = False
    while not sp_exists:
        print(f"Polling for {sp_object_id}...")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        poll_response = requests.get(f"https://graph.microsoft.com/beta/servicePrincipals/{sp_object_id}", headers=headers)

        try:
            poll_response.raise_for_status()
            sp_exists = True
        except:
            print(poll_response.reason)
            time.sleep(2)
            continue
    
    # Configure the service principal to allow SAML sign-on.

    url = f"https://graph.microsoft.com/beta/servicePrincipals/{sp_object_id}"
    data = '{ "preferredSingleSignOnMode": "saml" }'

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    requests.patch(url, data=data, headers=headers).raise_for_status()
    
    # Set up redirect URIs.

    application_object_id = response.json()["application"]["objectId"]
    url = f"https://graph.microsoft.com/v1.0/applications/{application_object_id}"
    data = '''{
    "web": {
        "redirectUris": [
            "https://localhost:8000/login?acs"
        ],
        "logoutUrl": "https://localhost:8000/login?sls"
    },
    "identifierUris": [
        "https://localhost:8123"
    ]
    }'''
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.patch(url, data=data, headers=headers)
    response.raise_for_status()

    # Register login URL with the new service principal.

    url = f"https://graph.microsoft.com/beta/servicePrincipals/{sp_object_id}"
    data = '{ "loginUrl": "https://localhost:8000/login" }'
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.patch(url, data=data, headers=headers)
    response.raise_for_status()

    # Generate self signed certificate.

    os.system("openssl req -x509 -out saml.crt -keyout saml.key -newkey rsa:2048 -nodes -sha256 -subj '/CN=staging.atat.dev'")

    # Convert self-signed certificate to PKCS12.

    os.system("openssl pkcs12 -export -out saml.pfx -inkey saml.key -in saml.crt")

if __name__ == "__main__":
    main()


# curl --location --request GET 'https://graph.microsoft.com/v1.0/servicePrincipals/<servicePrincipal.objectId>' \
# --header 'Authorization: Bearer <access_token>'

# RESPONSE (truncated):
# "appRoles": [
#     {
#         "allowedMemberTypes": [
#             "User"
#         ],
#         "description": "User",
#         "displayName": "User",
#         "id": "servicePrincipal.userAppRoleId",
#         "isEnabled": true,
#         "origin": "Application",
#         "value": null
#     }
# ]


# curl --location --request POST 'https://graph.microsoft.com/v1.0/servicePrincipals/servicePrincipal.objectId/appRoleAssignments' \
# --header 'Authorization: Bearer <access_token>' \
# --header 'Content-Type: application/json' \
# --data-raw '{
# "principalId": "objectIdOfUser",
# "principalType": "User",
# "appRoleId":"servicePrincipal.userAppRoleId",
# "resourceId":"servicePrincipal.objectId"
# }'