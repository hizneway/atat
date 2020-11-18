import json
import os
import subprocess
import logging
from os import path
from subprocess import CalledProcessError, CompletedProcess
from typing import Optional, Dict, NoReturn

import click
from click.utils import echo
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--sp_client_id",
    help="Client ID (Also called AppId) of the service principle created in phase1 - envvar: SP_CLIENT_ID",
    prompt="Service Principle used to provision infrastructure",
    envvar="SP_CLIENT_ID",
)
@click.option(
    "--sp_client_secret",
    help="Service Principle's password - envvar: SP_CLIENT_SECRET",
    prompt="Service Principle's password",
    envvar="SP_CLIENT_SECRET",
)
@click.option(
    "--subscription_id",
    help="The SubscriptionId (See subscriptions in Azure portal) that will house these resources - envvar: SUBSCRIPTION_ID",
    prompt="Subscription ID",
    envvar="SUBSCRIPTION_ID",
)
@click.option("--tenant_id", help="tenant id - envvar: TENANT_ID", envvar="TENANT_ID")
@click.option(
    "--ops_registry",
    help="Full URI of the container registry that after bootstrapping, should have rhel, rhel-py, and ops images - envvar: OPS_REGISTRY",
    prompt="Domain of container registry eg:cloudzeroopsregistry${var.namespace}.azurecr.io",
    envvar="OPS_REGISTRY",
)
@click.option(
    "--ops_resource_group",
    help="Resource group created to hold all the resources for operations only - envvar: OPS_RESOURCE_GROUP",
    prompt="Name of operations resource group",
    envvar="OPS_RESOURCE_GROUP",
)
@click.option(
    "--ops_storage_account",
    help="Name of Storage Account that holds the terraform state and inputs for this process - envvar: OPS_STORAGE_ACCOUNT",
    prompt="Name of Ops Storage Account",
    envvar="OPS_STORAGE_ACCOUNT",
)
@click.option(
    "--ops_tf_bootstrap_container",
    default="tf-bootstrap",
    help="Name of the container (folder) in the ops_storage_account that holds the terraform state from bootstrap - envvar: OPS_TF_BOOTSTRAP_CONTAINER",
    envvar="OPS_TF_BOOTSTRAP_CONTAINER",
)
@click.option(
    "--namespace",
    help="Namespacing of your environment - envvar: NAMESPACE",
    envvar="NAMESPACE",
)
@click.option(
    "--ops_tf_application_container",
    default="tf-application",
    help="Name of the container (folder) in the ops_storage_account that holds the terraform state from application - envvar: OPS_TF_APPLICATION_CONTAINER",
    envvar="OPS_TF_APPLICATION_CONTAINER",
)
@click.option(
    "--ops_config_container",
    default="config",
    help="Name of the container (folder) in the ops_storage_account that holds the config that will be needed by the application - envvar: OPS_CONFIG_CONTAINER",
    envvar="OPS_CERTS_CONTAINER",
)
@click.option(
    "--config-azcli/--no-config-azcli",
    default=True,
    help="Whether to try and run the az login w/ the service principle so we can install the aks plugins"
)
def provision(
    sp_client_id,
    sp_client_secret,
    subscription_id,
    tenant_id,
    ops_registry,
    ops_resource_group,
    ops_storage_account,
    ops_tf_bootstrap_container,
    namespace,
    ops_tf_application_container,
    ops_config_container,
    config_azcli,
):
    if config_azcli:
        configure_azcli(
            sp_client_id=sp_client_id,
            sp_client_secret=sp_client_secret,
            tenant_id=tenant_id,
        )
    # ssl_process = diffie_helman(encryption=4096)
    # download_file(
    #     ops_storage_account, ops_config_container, "atatdev.pem", "/tmp/atatdev.pem"
    # )

    # download_file(
    #     ops_storage_account,
    #     ops_config_container,
    #     "app.tfvars.json",
    #     "/tmp/app.tfvars.json",
    # )
    # pause_until_complete(ssl_process)

    # terraform_application(
    #     sp_client_id=sp_client_id,
    #     sp_client_secret=sp_client_secret,
    #     subscription_id=subscription_id,
    #     tenant_id=tenant_id,
    #     backend_resource_group_name=ops_resource_group,
    #     backend_storage_account_name=ops_storage_account,
    #     backend_container_name=ops_tf_application_container,
    #     namespace=namespace,
    # )

    # pause_until_complete(ssl_process)


def configure_azcli(sp_client_id, sp_client_secret, tenant_id):
    cmd = [
        "az",
        "login",
        "--service-principal",
        "--username", sp_client_id,
        "--password", sp_client_secret,
        "--tenant", tenant_id,
    ]
    print(cmd)
    subprocess.run(cmd).check_returncode()
    subprocess.run("az extension add --name aks-preview".split()).check_returncode()
    subprocess.run("az extension update --name aks-preview".split()).check_returncode()
    subprocess.run(
        "az feature register --name AKS-AzurePolicyAutoApprove --namespace Microsoft.ContainerService".split()
    ).check_returncode()
    subprocess.run(
        "az provider register --namespace Microsoft.ContainerService".split()
    ).check_returncode()


def terraform_application(
    sp_client_id,
    sp_client_secret,
    subscription_id,
    tenant_id,
    backend_resource_group_name,
    backend_storage_account_name,
    backend_container_name,
    namespace,
    backend_key="terraform.tfstate",
    bootrap_container_name="tf-bootstrap",
):

    logger.info("terraform_application")

    cwd = path.join("../", "../", "terraform", "providers", "application_env")

    default_args = {"cwd": cwd}

    backend_configs = [
        f"-backend-config=resource_group_name={backend_resource_group_name}",
        f"-backend-config=storage_account_name={backend_storage_account_name}",
        f"-backend-config=container_name={backend_container_name}",
        f"-backend-config=key={backend_key}",
    ]
    try:
        init_cmd = ["terraform", "init", *backend_configs, "."]
        print(init_cmd)
        subprocess.run(init_cmd, **default_args).check_returncode()

        tfvars = [
            f"-var=operator_subscription_id={subscription_id}",
            f"-var=operator_client_id={sp_client_id}",
            f"-var=operator_client_secret={sp_client_secret}",
            f"-var=operator_tenant_id={tenant_id}",
            f"-var=ops_resource_group={backend_resource_group_name}",
            f"-var=ops_storage_account={backend_storage_account_name}",
            f"-var=tf_bootstrap_container={bootrap_container_name}",
            f"-var=deployment_namespace={namespace}",
        ]
        cmd = [
            "terraform",
            "plan",
            "-input=false",
            "-out=plan.tfplan",
            "-var-file=/tmp/app.tfvars.json",
            *tfvars,
            ".",
        ]
        print(cmd)
        subprocess.run(cmd, **default_args).check_returncode()
        print("terraform apply plan.tfplan")
        subprocess.run(
            "terraform apply plan.tfplan".split(), **default_args
        ).check_returncode()

    except CalledProcessError as err:
        echo("=" * 50)
        echo(f"Failed running {err.cmd}")
        echo("=" * 50)
        echo(err.stdout)
        echo("=" * 50)
        echo(err.stderr)
        import pdb

        pdb.set_trace()
        raise


def diffie_helman(encryption: int = 4096) -> Optional[subprocess.Popen]:
    logger.info("diffie_helman")
    if path.exists("/tmp/dhparams.pem"):
        return

    return subprocess.Popen(
        [
            "openssl",
            "dhparam",
            "-out",
            "/tmp/dhparams.pem",
            "4096",
        ],
        stdout=subprocess.DEVNULL,
    )


def download_file(
    storage_account: str, container_name: str, file_name: str, dest_path: str
) -> int:
    if path.exists(dest_path):
        return 0

    result = subprocess.run(
        f"az storage blob download --account-name {storage_account} --container-name {container_name} --name {file_name} -f {dest_path} --no-progress".split(),
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        echo(result.stdout)
        echo(result.stderr)

    return result.returncode


def pause_until_complete(open_process: Optional[subprocess.Popen]):
    logger.info("pause_until_complete")
    if open_process is None:
        return

    while True:
        return_code = open_process.poll()
        if return_code is not None:
            click.echo(f"Return Code {return_code}")
            click.echo(open_process.stdout.read())
            return return_code == 0


if __name__ == "__main__":
    provision()