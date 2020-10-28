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
@click.argument("workspace", default="./workspace")
@click.argument("subscription_id",envvar='AZURE_SUBSCRIPTION_ID')
@click.argument("tenant_id",envvar='AZURE_TENANT_ID')
@click.argument("client_id",envvar='AZURE_CLIENT_ID')
@click.argument("client_secret",envvar='AZURE_CLIENT_SECRET')
@click.argyment("config_directory" default=None)
def cli(subscription_id, tenant_id, client_id, client_secret, config_directory) -> NoReturn:
    os.environ["AZURE_SUBSCRIPTION_ID"=subscription_id
    os.environ["AZURE_TENANT_ID"=tenant_id
    os.environ["AZURE_CLIENT_ID"=client_id
    os.environ["AZURE_CLIENT_SECRET"=client_secret
    set_environment_variables()
    # workspace = path.abspath( path.join(os.getcwd(), "../../"))
    # workspace = "./workspace"
    create_workspace(workspace)

    clone_repo(workspace=workspace)
    checkout_branch(workspace=workspace, branch="staging")


    # create service principal





    ssl_process = diffie_helman(workspace=workspace, encryption=4096)

    download_pem(workspace=workspace)
    download_bootstrap_config(workspace=workspace)
    terraform_bootstrap(workspace=workspace)
    bootstrap_outputs = load_bootstrap_output(workspace)

    download_application_env_config(workspace=workspace)
    login_registry("cloudzeroopsregistry.azurecr.io")
    import_rhel(
        src_registry="cloudzeroopsregistry.azurecr.io",
        dest_registry=bootstrap_outputs["ops_container_registry_name"],
    )

    nginx_proc = build_nginx(workspace=workspace, registry=bootstrap_outputs["ops_container_registry_name"])
    atat_proc = build_atat(workspace=workspace, registry=bootstrap_outputs["ops_container_registry_name"])
    ops_proc = build_ops(workspace=workspace, registry=bootstrap_outputs["ops_container_registry_name"])

    download_application_env_config(workspace=workspace)

    click.echo("Time to wait on slow jobs")
    pause_until_complete(ssl_process)
    pause_until_complete(nginx_proc)
    pause_until_complete(atat_proc)
    pause_until_complete(ops_proc)
    terraform_application_env(workspace)


def create_workspace(workspace="./workspace") -> int:
    logger.info("create_workspace")
    if path.exists(workspace):
        return 0

    os.mkdir(workspace)
    return 0


def clone_repo(workspace: str, repo: str = "https://github.com/dod-ccpo/atst") -> int:
    logger.info("clone_repo")
    if path.exists(path.join(workspace, ".git")):
        return 0

    result = subprocess.run(f"git clone {repo} {workspace}".split())
    return result.returncode


def checkout_branch(workspace: str, branch: str) -> int:
    logger.info("checkout_branch")
    result = subprocess.run(f"git checkout {branch}".split(), cwd=workspace)
    return result.returncode


def diffie_helman(workspace: str, encryption: int = 4096) -> subprocess.Popen:
    logger.info("diffie_helman")
    dhparams_path =path.join(workspace, "terraform", "providers", "application_env", "dhparams.pem")
    if path.exists(dhparams_path):
        return

    return subprocess.Popen(
        [
            "openssl",
            "dhparam",
            "-out",
            dhparams_path,
            "4096",
        ]
    )


def login_registry(registry) -> int:
    logger.info("login_registry")
    result = subprocess.run(
        f"az acr login --name {registry}".split(), stdout=subprocess.PIPE
    )
    return result.returncode


def import_rhel(src_registry, dest_registry, image="rhel-py") -> int:
    logger.info("import_rhel")
    output = subprocess.run(
        f"az acr repository list --name {dest_registry} --output table".split(),
        capture_output=True,
        text=True,
    )
    if image in output.stdout:
        return 0
    result = subprocess.run(
        f"az acr import --name {dest_registry} --source {src_registry}/{image} --image {image}".split(),
        stdout=subprocess.PIPE,
    )

    return result.returncode


def build_nginx(workspace: str, registry: str, tag: str = "test") -> subprocess.Popen:
    logger.info("build_nginx")
    return subprocess.Popen(
        f"az acr build --image nginx:{tag} --registry {registry} --build-arg IMAGE={registry}/rhel-py --file nginx.Dockerfile .".split(),
        stdout=subprocess.PIPE,
        cwd=workspace,
    )


def build_atat(workspace: str, registry: str, tag: str = "test") -> subprocess.Popen:
    logger.info("build_atat")
    return subprocess.Popen(
        f"az acr build --image atat:{tag} --registry {registry} --build-arg IMAGE={registry}/rhel-py --file Dockerfile .".split(),
        stdout=subprocess.PIPE,
        cwd=workspace,
    )

def build_ops(workspace: str, registry: str, tag: str = "test") -> subprocess.Popen:
    logger.info("build_ops")
    return subprocess.Popen(
        f"az acr build --image ops:{tag} --registry {registry} --build-arg IMAGE={registry}/rhel-py --file ops.Dockerfile .".split(),
        stdout=subprocess.PIPE,
        cwd=workspace,
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


def download_bootstrap_config(workspace: str):
    logger.info("download_bootstrap_config")
    return download_file(
        "czopsstorageaccount",
        "tf-configs",
        "bootstrap.tfvars",
        path.join(workspace, "terraform", "providers", "bootstrap", "bootstrap.tfvars"),
    )


def download_application_env_config(workspace: str):
    logger.info("download_application_env_config")
    return download_file(
        "czopsstorageaccount",
        "tf-configs",
        "app.tfvars.json",
        path.join(
            workspace, "terraform", "providers", "application_env", "app.tfvars.json"
        ),
    )


def download_pem(workspace: str):
    logger.info("download_pem")
    return download_file(
        "czopsstorageaccount",
        "certs",
        "atatdev.pem",
        path.join(workspace, "terraform", "providers", "application_env", "atatdev.pem"),
    )

def delete_file(path_to_file):
    if path.exists(path_to_file):
        os.remove(path_to_file)

def delete_application_env_plan(workspace: str):
    delete_file(path.join(path_to_application_env, "plan.tfplan"))

def path_to_application_env(workspace: str):
    return path.join(workspace, "terraform", "providers", "application_env")

def path_to_bootstrap(workspace: str):
    return path.join(workspace, "terraform", "providers", "bootstrap")


def terraform_bootstrap(workspace: str):
    logger.info("terraform_bootstrap")
    logger.info("If we're re-bootstrapping, we need to delete the plan in application_env")
    delete_application_env_plan(workspace)
    cwd = path_to_bootstrap(workspace)
    default_args = {"cwd": cwd, "capture_output": True}
    try:
        subprocess.run("terraform init .".split(), **default_args).check_returncode()
        if not path.exists(path.join(cwd, "plan.tfplan")):
            subprocess.run(
                "terraform plan -input=false -out=plan.tfplan -var-file=bootstrap.tfvars".split(),
                **default_args,
            ).check_returncode()
        subprocess.run(
            "terraform apply plan.tfplan".split(), **default_args
        ).check_returncode()

        bootstrap_output_path = path.join(
            workspace,
            "terraform",
            "providers",
            "application_env",
            "bootstrap_output.tfvars",
        )
        with open(bootstrap_output_path, "w") as bootstrap_output:
            subprocess.run(
                "terraform output -no-color".split(),
                stdout=bootstrap_output,
                cwd=cwd,
            )
        bootstrap_output_path = path.join(
            workspace,
            "terraform",
            "providers",
            "application_env",
            "bootstrap_output.tfvars.json",
        )
        with open(bootstrap_output_path, "w") as bootstrap_output:
            subprocess.run(
                "terraform output -json".split(),
                stdout=bootstrap_output,
                cwd=cwd,
            )
    except CalledProcessError as err:
        echo("=" * 50)
        echo(f"Failed running {err.cmd}")
        echo("=" * 50)
        echo(err.output)
        echo(err.stderr)
        echo(err.stdout)
        raise

def load_bootstrap_output(workspace: str):
    logger.info("load_bootstrap_output")
    output_path = path.join(workspace, "terraform", "providers", "application_env", "bootstrap_output.tfvars.json")
    if not path.exists(output_path):
        raise RuntimeError(
            f"Missing output from the bootstrap step. Either bootstrap has not been run, or the output json was not created here: {output_path}"
        )

    with open(output_path, 'r') as file:
        output = json.load(file)

    return { k : v["value"] for k, v in output.items()}

def terraform_application_env(workspace: str):
    logger.info("terraform_application_env")
    cwd = path.join(workspace, "terraform", "providers", "application_env")
    bootstrap_output = load_bootstrap_output(workspace)

    default_args = {"cwd": cwd, "capture_output": True}

    backend_configs = [f"-backend-config={key}={bootstrap_output[key]}" for key in ['key', 'container_name', 'resource_group_name', 'storage_account_name']]
    try:
        init_cmd = [
            "terraform",
            "init",
            *backend_configs,
            "."
        ]
        # import pdb; pdb.set_trace()
        subprocess.run( init_cmd, **default_args).check_returncode()
        if not path.exists(path.join(cwd, "plan.tf")):
            subprocess.run([
                "terraform",
                "plan",
                "-input=false",
                "-out=plan.tfplan",
                "-var-file=app.tfvars.json",
                "-var",
                "dhparam4096=dhparams.pem",
                "-var",
                "tls_cert_path=atatdev.pem",
                "."
            ], **default_args).check_returncode()

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

    # export ops_container_registry_name="$(terraform output ops_container_registry_name)"


def assert_ok(comp_process: CompletedProcess) -> None:
    if comp_process.returncode != 0:
        pass
    return


def stop_on_error(methods, context):
    for method in methods:
        comp_process = method(build_args(context))
        comp_process.check_returncode()


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
    cli()
