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
    help="Client ID (Also called AppId) of the service principle created in phase1",
    prompt="Service Principle used to provision infrastructure",
)
@click.option(
    "--sp_client_secret",
    help="Service Princeiple's password",
    prompt="Service Principle's password",
)
@click.option(
    "--subscription_id",
    help="The SubscriptionId (See subscriptions in Azure portal) that will house these resources",
    prompt="Subscription ID",
)
@click.option("--tenant_id", prompt="")
@click.option(
    "--ops_registry",
    help="Full URI of the container registry that after bootstrapping, should have rhel, rhel-py, and ops images",
    prompt="Domain of container registry eg:cloudzeroopsregistry${var.namespace}.azurecr.io",
)
@click.option("--ops_resource_group", help="Resource group created to hold all the resources for operations only", prompt="Name of operations resource group")
@click.option(
    "--ops_storage_account",
    help="Name of Storage Account that holds the terraform state and inputs for this process",
    prompt="Name of Ops Storage Account",
)
@click.option(
    "--ops_tf_bootstrap_container",
    default="tf-bootstrap",
    help="Name of the container (folder) in the ops_storage_account that holds the terraform state from bootstrap",
)
@click.option(
    "--ops_tf_application_container",
    default="tf-application",
    help="Name of the container (folder) in the ops_storage_account that holds the terraform state from application",
)
@click.option(
    "--ops_certs_container",
    default="certs",
    help="Name of the container (folder) in the ops_storage_account that holds the certs that will be needed by the application",
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
    ops_tf_application_container,
    ops_certs_container,
):

    ssl_process = diffie_helman(encryption=4096)
    download_file(
        ops_storage_account, ops_certs_container, "atatdev.pem", "atatdev.pem"
    )
    terraform_application_env(backend_resource_group_name=ops_resource_group, backend_storage_account_name=ops_storage_account, backend_container_name=ops_tf_application_container)

    pause_until_complete(ssl_process)


def diffie_helman(encryption: int = 4096) -> Optional[subprocess.Popen]:
    logger.info("diffie_helman")
    if path.exists("dhparams.pem"):
        return

    return subprocess.Popen(
        [
            "openssl",
            "dhparam",
            "-out",
            "dhparams.pem",
            "4096",
        ]
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


def terraform_application_env(sp_client_id, sp_client_secret, subscription_id, tenant_id, backend_resource_group_name, backend_storage_account_name, backend_container_name, backend_key="terraform.tfstate", bootrap_container_name="tf-bootstrap"):

    logger.info("terraform_application_env")
    cwd = path.join("../", "../", "terraform", "providers", "application_env")
    # bootstrap_output = load_bootstrap_output(workspace)

    default_args = {"cwd": cwd, "capture_output": True}

    backend_configs = [
        f"-backend-config=resource_group_name={backend_resource_group_name}",
        f"-backend-config=storage_account_name={backend_storage_account_name}",
        f"-backend-config=container_name={backend_container_name}",
        f"-backend-config=key={backend_key}",
    ]
    try:
        init_cmd = ["terraform", "init", *backend_configs, "."]

        subprocess.run(init_cmd, **default_args).check_returncode()
        if not path.exists(path.join(cwd, "plan.tf")):
            tfvars = [
                f"-var=operator_subscription_id={sp_client_id}",
                f"-var=operator_client_id={sp_client_secret}",
                f"-var=operator_client_secret={subscription_id}",
                f"-var=operator_tenant_id={tenant_id}",
                f"-var=ops_resource_group={backend_resource_group_name}",
                f"-var=ops_storage_account={backend_storage_account_name}",
                f"-var=tf_bootstrap_container={bootrap_container_name}",
                f"-var=dhparam4096=../../../CONFIGS_GO_HERE_OR_SUMMIN",
                f"-var=tls_cert_path=../../../CONFIGS_GO_HERE_OR_SUMMIN"
            ]
            subprocess.run(
                [
                    "terraform",
                    "plan",
                    "-input=false",
                    "-out=plan.tfplan",
                    "-var-file=app.tfvars.json",
                    *tfvars,
                    ".",
                ],
                **default_args,
            ).check_returncode()

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
