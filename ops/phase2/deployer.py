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
    prompt="Full URI of container registry eg: cloudzeroopsregistry${var.namespace}.azurecr.io",
    envvar="OPS_REGISTRY",
)
@click.option(
    "--namespace",
    help="Namespacing of your environment - envvar: NAMESPACE",
    envvar="NAMESPACE",
)
@click.option(
    "--atat_registry",
    help="Full URI of the container registry that k8s will have access to - envvar: ATAT_REGISTRY",
    prompt="Domain of atat container registry eg:cloudzeroregistry${var.namespace}.azurecr.io",
    envvar="ATAT_REGISTRY",
)
@click.option(
    "--atat-image-tag",
    default="latest",
    help="Set the tag applied to the atat image that will be build",
)
@click.option("--atat-commit-sha", help="")
@click.option(
    "--nginx-image-tag",
    default="latest",
    help="Set the tag applied to the nginx image that will be build",
)
@click.option(
    "--git-sha",
    help="The git sha of the current commit"
)
@click.option(
    "--config-azcli/--no-config-azcli",
    default=True,
    help="Whether to try and run the az login w/ the service principle so we can install the aks plugins"
)
def deploy(
    sp_client_id,
    sp_client_secret,
    subscription_id,
    tenant_id,
    namespace,
    ops_registry,
    atat_registry,
    atat_image_tag,
    atat_commit_sha,
    nginx_image_tag,
    config_azcli,
    git_sha,
):
    setup(sp_client_id, sp_client_secret, subscription_id, tenant_id, namespace, config_azcli)
    build_atat(ops_registry, atat_registry, git_sha, atat_image_tag)
    build_nginx(ops_registry, atat_registry, nginx_image_tag)

    tf_output_dict = collect_terraform_outputs()

    ansible(
        tf_output_dict=tf_output_dict,
        addl_args={
            "sp_client_id": sp_client_id,
            "sp_client_secret": sp_client_secret,
            "subscription_id": subscription_id,
            "tenant_id": tenant_id,
            "atat_image_tag": atat_image_tag,
            "nginx_image_tag": nginx_image_tag
        },
    )


def setup(sp_client_id, sp_client_secret, subscription_id, tenant_id, namespace, config_azcli):
    if config_azcli:
        configure_azcli(
            sp_client_id=sp_client_id,
            sp_client_secret=sp_client_secret,
            tenant_id=tenant_id,
            namespace=namespace
        )


def configure_azcli(sp_client_id, sp_client_secret, tenant_id, namespace):
    cmd = [
        "az",
        "login",
        "--service-principal",
        "--username",
        sp_client_id,
        "--password",
        sp_client_secret,
        "--tenant",
        tenant_id,
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
    subprocess.run(f"az aks get-credentials -g cloudzero-vpc-{namespace} -n cloudzero-private-k8s-{namespace}".split()).check_returncode()

def build_atat(ops_registry, atat_registry, git_sha, atat_image_tag):
    cmd = [
        "az",
        "acr",
        "build",
        "--registry",
        ops_registry,
        "--build-arg",
        f"IMAGE={ops_registry}/rhel-py:latest",
        "--image",
        f"atat:{atat_image_tag}",
        "--file",
        "Dockerfile",
        ".",
    ]
    # TODO: Make this async
    subprocess.run(cmd).check_returncode()


def build_nginx(ops_registry, atat_registry, nginx_image_tag):
    cmd = [
        "az",
        "acr",
        "build",
        "--registry",
        ops_registry,
        "--build-arg",
        f"IMAGE={ops_registry}/rhel-py:latest",
        "--image",
        f"atat:{nginx_image_tag}",
        ".",
    ]
    # TODO: Make this async
    subprocess.run(cmd).check_returncode()


def ansible(tf_output_dict, addl_args):
    extra_vars = {**tf_output_dict, **addl_args}
    extra_vars["postgres_root_cert"] = "../deploy/azure/pgsslrootcert.yml"
    extra_vars["src_dir"] = os.path.abspath(os.path.join(os.getcwd(), "../", "../"))
    cwd = path.join("../", "../", "ansible")
    print(extra_vars)
    cmd = [
        "ansible-playbook",
        "k8s.yml",
        "-vvv",
        "--extra-vars",
        json.dumps(extra_vars),
    ]
    subprocess.run(cmd, cwd=cwd).check_returncode()


if __name__ == "__main__":
    deploy()
