import json
import os
import subprocess
from os import path
from subprocess import CalledProcessError, CompletedProcess
from typing import Optional

import click
from azure.identity import DefaultAzureCredential
from click.utils import echo


@click.command()
def cli():
    workspace = "./workspace"
    create_workspace(workspace)

    clone_repo(workspace=workspace)
    checkout_branch(workspace=workspace, branch="staging")

    ssl_process = diffie_helman(encryption=256)

    download_pem(workspace=workspace)
    download_bootstrap_config(workspace=workspace)
    terraform_bootstrap(workspace=workspace)

    download_application_env_config(workspace=workspace)
    login_registry("cloudzeroopsregistry.azurecr.io")
    import_rhel(
        src_registry="cloudzeroopsregistry.azurecr.io",
        dest_registry="cloudzeroopscontainerregistryrattler.azurecr.io",
    )
    nginx_proc = build_nginx()
    atat_proc = build_atat()

    download_application_env_config(workspace=workspace)
    # terraform_application()

    click.echo("Time to wait on ssl")
    pause_until_complete(ssl_process)


def create_workspace(workspace="./workspace") -> int:
    if path.exists(workspace):
        return 0

    os.mkdir(workspace)
    return 0


def clone_repo(workspace: str, repo: str = "https://github.com/dod-ccpo/atst") -> int:
    if path.exists(path.join(workspace, ".git")):
        return 0

    result = subprocess.run(f"git clone {repo} {workspace}".split())
    return result.returncode


def checkout_branch(workspace: str, branch: str) -> int:
    result = subprocess.run(f"git checkout {branch}".split(), cwd=workspace)
    return result.returncode


def diffie_helman(workspace: str, encryption: int = 4096) -> subprocess.Popen:
    if path.exists(path.join(workspace, "dhparams.pem")):
        return

    return subprocess.Popen(
        [
            "diffie_helman",
            "dhparam",
            "-out",
            os.path.join(workspace, "dhparams.pem"),
            "4096",
        ]
    )


def login_registry(registry) -> int:
    result = subprocess.run(
        f"az acr login --name {registry}".split(), stdout=subprocess.PIPE
    )
    return result.returncode


def import_rhel(src_registry, dest_registry, image="rhel-py") -> int:
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
    return subprocess.Popen(
        f"az acr build --image nginx:{tag} --registry {registry} --build-arg IMAGE={registry}/rhel-py --file nginx.Dockerfile .".split(),
        stdout=subprocess.PIPE,
        cwd=workspace,
    )


def build_atat(workspace: str, registry: str, tag: str = "test") -> subprocess.Popen:
    return subprocess.Popen(
        f"az acr build --image atat:{tag} --registry {registry} --build-arg IMAGE={registry}/rhel-py --file Dockerfile .".split(),
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
    return download_file(
        "czopsstorageaccount",
        "tf-configs",
        "bootstrap.tfvars",
        path.join(workspace, "terraform", "providers", "bootstrap", "bootstrap.tfvars"),
    )


def download_application_env_config(workspace: str):
    return download_file(
        "czopsstorageaccount",
        "tf-configs",
        "app.tfvars.json",
        path.join(
            workspace, "terraform", "providers", "application_env", "app.tfvars.json"
        ),
    )


def download_pem(workspace: str):
    return download_file(
        "czopsstorageaccount",
        "certs",
        "atatdev.pem",
        path.join(workspace, "atatdev.pem"),
    )


def terraform_bootstrap(workspace: str):
    cwd = path.join(workspace, "terraform", "providers", "bootstrap")
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
        raise


def terraform_application_env(workspace: str):
    cwd = path.join(workspace, "terraform", "providers", "application_env")
    bootstrap_output_config = path.join(cwd, "bootstrap_output.tfvars.json")
    if not path.exists(bootstrap_output_config):
        raise RuntimeError(
            f"Missing output from the bootstrap step. Either bootstrap has not been run, or the output json was not created here: {bootstrap_output_config}"
        )
    with open(bootstrap_output_config, "r") as bootstrap_output_config_file:
        bootstrap_output = json.load(bootstrap_output_config_file)

    default_args = {"cwd": cwd, "capture_output": True}

    # cmd = f"terraform init -backend-config='container_name=tfstate' "
    #     + f"-backend-config='key={bootstrap_output['environment']['value']}.tfstate' "

    # terraform init -backend-config='container_name=tfstate' -backend-config='key=coral.tfstate' -backend-config='resource_group_name=cloudzero-cloudzerocoraltfstate-coral' -backend-config='storage_account_name=cloudzerocoraltfstate' .
    try:
        comp_proc = subprocess.run(
            f"terraform init -backend-config='container_name=tfstate' -backend-config='key={bootstrap_output['environment']['value']}.tfstate' -backend-config='resource_group_name=cloudzero-cloudzero{bootstrap_output['environment']['value']}tfstate-{bootstrap_output['environment']['value']}' -backend-config='storage_account_name=cloudzero{bootstrap_output['environment']['value']}tfstate' .".split(),
            **default_args,
        )  # .check_returncode()

        subprocess.run(
            "terraform apply -auto-approve -var-file=app.tfvars.json -var 'dhparam4096=dhparams.pem' -var 'mailgun_api_key=123' -var 'tls_cert_path=atatdev.pem' .".split(),
            **default_args,
        ).check_returncode()

        # subprocess.run(
        #     "terraform apply -auto-approve plan.tfplan".split(), **default_args
        # ).check_returncode()

    except CalledProcessError as err:
        echo("=" * 50)
        echo(f"Failed running {err.cmd}")
        echo("=" * 50)
        echo(err.output)
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
