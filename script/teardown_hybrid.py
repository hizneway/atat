import requests
from msrestazure.azure_cloud import AZURE_PUBLIC_CLOUD
import os
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)

from atat.app import make_config
from atat.domain.csp.cloud.hybrid_cloud_provider import HYBRID_PREFIX


GRAPH_API = "https://graph.microsoft.com"


def delete_tenant_principal_app(token, app_id):
    auth_header = {
        "Authorization": f"Bearer {token}",
    }

    url = f"{GRAPH_API}/v1.0/applications/{app_id}"

    response = requests.delete(url, headers=auth_header)
    response.raise_for_status()


def list_app_registrations(token):
    auth_header = {
        "Authorization": f"Bearer {token}",
    }

    url = f"{GRAPH_API}/v1.0/applications"
    response = requests.get(url, headers=auth_header)
    response.raise_for_status()

    apps = response.json()["value"]

    return [
        (app["displayName"], app["id"])
        for app in apps
        if app["displayName"].startswith(HYBRID_PREFIX)
    ]


def get_user_token(cloud, tenant_id, username, password, ps_client_id):
    url = f"{cloud.endpoints.active_directory}/{tenant_id}/oauth2/token"
    resource = GRAPH_API
    payload = {
        "client_id": ps_client_id,
        "grant_type": "password",
        "username": username,
        "password": password,
        "resource": resource,
    }
    token_response = requests.get(url, data=payload, timeout=30)
    token_response.raise_for_status()
    token = token_response.json().get("access_token")
    if token is None:
        message = f"Failed to get user principal token for resource '{resource}' in tenant '{tenant_id}'"
        raise RuntimeError(message)
    else:
        return token


if __name__ == "__main__":
    """
    This script deletes applications created by the HybridCloudProvider
    interface. It expects that the ATAT hybrid configuration settings
    referenced below in this function have been set.
    """
    config = make_config()

    required_config = [
        "AZURE_TENANT_ID",
        "AZURE_TENANT_ADMIN_USERNAME",
        "AZURE_TENANT_ADMIN_PASSWORD",
        "AZURE_POWERSHELL_CLIENT_ID",
    ]
    missing_config = [s for s in required_config if config[s] is None]

    if missing_config:
        raise ValueError(
            f"The following config settings must have values: {', '.join(missing_config)}"
        )

    tenant_id, username, password, ps_client_id = [config[s] for s in required_config]

    token = get_user_token(
        AZURE_PUBLIC_CLOUD, tenant_id, username, password, ps_client_id,
    )
    apps = list_app_registrations(token)
    if len(apps) > 0:
        print("Deleting Hybrid-managed applications...")
        for app_name, app_id in apps:
            delete_tenant_principal_app(token, app_id)
            print(f"  deleted {app_name}")
    else:
        print("No matching applications found in tenant.")
