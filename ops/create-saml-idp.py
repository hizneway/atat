#! /usr/bin/python

import base64
import click
import datetime
import json
import requests
import time
import uuid

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import BestAvailableEncryption
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509.oid import NameOID
from typing import NoReturn


@click.command()
@click.argument("tenant-id",)
@click.argument("application-id")
@click.argument("object-id")
@click.argument("password")
def main(
    tenant_id: str, application_id: str, object_id: str, password: str
) -> NoReturn:

    # Authenticate with the provided service principle.

    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    data = {
        "grant_type": "client_credentials",
        "client_id": application_id,
        "client_secret": password,
        "scope": "https://graph.microsoft.com/.default",
    }

    response = requests.post(url, data=data)
    response.raise_for_status()
    access_token = response.json()["access_token"]

    # Create a new app registration from a template.

    url = "https://graph.microsoft.com/beta/applicationTemplates/8adf8e6e-67b2-4cf2-a259-e3dc5476c621/instantiate"
    data = '{ "displayName": "ATAT SAML Auth" }'

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
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
            "Content-Type": "application/json",
        }
        poll_response = requests.get(
            f"https://graph.microsoft.com/beta/servicePrincipals/{sp_object_id}",
            headers=headers,
        )

        try:
            poll_response.raise_for_status()
            sp_exists = True
        except requests.HTTPError:
            print(poll_response.reason)
            time.sleep(2)
            continue

    # Configure the service principal to allow SAML sign-on.

    url = f"https://graph.microsoft.com/beta/servicePrincipals/{sp_object_id}"
    data = '{ "preferredSingleSignOnMode": "saml" }'

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    requests.patch(url, data=data, headers=headers).raise_for_status()

    # Set up redirect URIs.

    application_object_id = response.json()["application"]["objectId"]
    url = f"https://graph.microsoft.com/v1.0/applications/{application_object_id}"
    data = """{
    "web": {
        "redirectUris": [
            "https://localhost:8000/login?acs"
        ],
        "logoutUrl": "https://localhost:8000/login?sls"
    },
    "identifierUris": [
        "https://localhost:8123"
    ]
    }"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    response = requests.patch(url, data=data, headers=headers)
    response.raise_for_status()

    # Register login URL with the new service principal.

    url = f"https://graph.microsoft.com/beta/servicePrincipals/{sp_object_id}"
    data = '{ "loginUrl": "https://localhost:8000/login" }'
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    response = requests.patch(url, data=data, headers=headers)
    response.raise_for_status()

    # https://docs.microsoft.com/en-us/graph/application-saml-sso-configure-api?tabs=http#step-4-configure-signing-certificate
    # https://cryptography.io/en/latest/x509/tutorial.html#creating-a-self-signed-certificate

    # Generate uuid to use as a password
    saml_signing_password = str(uuid.uuid4())

    # Generate self signed certificate.
    key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    # Various details about who we are. For a self-signed certificate the
    # subject and issuer are always the same.
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Pennsylvania"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Philadelphia"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "PromptWorks"),
            x509.NameAttribute(NameOID.COMMON_NAME, "PromptWorks"),
        ]
    )

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(
            # Our certificate will be valid for 1 year
            datetime.datetime.utcnow()
            + datetime.timedelta(days=365)
        )
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost")]),
            critical=False,
            # Sign our certificate with our private key
        )
        .sign(key, hashes.SHA256(), backend=default_backend())
    )

    from cryptography.hazmat.primitives.serialization.pkcs12 import (
        serialize_key_and_certificates,
    )

    pem_pkcs12 = serialize_key_and_certificates(
        name=b"saml_cert",
        key=key,
        cert=cert,
        cas=None,
        encryption_algorithm=BestAvailableEncryption(saml_signing_password.encode()),
    )

    url = f"https://graph.microsoft.com/beta/servicePrincipals/{sp_object_id}"

    sign_and_password_guid = str(uuid.uuid4())
    verify_guid = str(uuid.uuid4())

    private_key = base64.encodebytes(pem_pkcs12).decode().strip("\n")
    public_key = (
        base64.encodebytes(cert.public_bytes(Encoding.PEM)).decode().strip("\n")
    )
    thumbprint = (
        base64.encodebytes(cert.fingerprint(hashes.SHA256())).decode().strip("\n")
    )

    data = {
        "keyCredentials": [
            {
                "customKeyIdentifier": thumbprint,
                "endDateTime": cert.not_valid_after.isoformat(),
                "keyId": sign_and_password_guid,
                "startDateTime": cert.not_valid_before.isoformat(),
                "type": "X509CertAndPassword",
                "usage": "Sign",
                "key": private_key,
                "displayName": "CN=ATAT SAML Signing Certificate",
            },
            {
                "customKeyIdentifier": thumbprint,
                "endDateTime": cert.not_valid_after.isoformat(),
                "keyId": verify_guid,
                "startDateTime": cert.not_valid_before.isoformat(),
                "type": "AsymmetricX509Cert",
                "usage": "Verify",
                "key": public_key,
                "displayName": "CN=ATAT SAML Verification Certificate",
            },
        ],
        "passwordCredentials": [
            {
                "customKeyIdentifier": thumbprint,
                "keyId": sign_and_password_guid,
                "endDateTime": cert.not_valid_after.isoformat(),
                "startDateTime": cert.not_valid_before.isoformat(),
                "secretText": saml_signing_password,
            }
        ],
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    response = requests.patch(url, data=json.dumps(data), headers=headers)
    response.raise_for_status()

    user_service_principals = open("user_service_principals.txt")

    for line in user_service_principals.readlines():
        user_object_id = line.strip()
        url = f"https://graph.microsoft.com/v1.0/servicePrincipals/{sp_object_id}/appRoleAssignments"
        data = {
            "principalId": user_object_id,
            "principalType": "User",
            "resourceId": sp_object_id,
            "appRoleId": "18d14569-c3bd-439b-9a66-3a2aee01d14f",
        }
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        response = requests.post(url, data=json.dumps(data), headers=headers)

        if response.status_code != 201:
            print(f"Failed to assign user {user_object_id}")
            print(response.json())


if __name__ == "__main__":
    main()
