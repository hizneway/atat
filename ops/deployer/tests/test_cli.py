import shutil
import time
import subprocess
import uuid
import logging
from os import path
import os
import pytest
from click.testing import CliRunner
from deployer.cli import (
    build_atat,
    build_nginx,
    checkout_branch,
    cli,
    clone_repo,
    create_workspace,
    diffie_helman,
    download_application_env_config,
    download_bootstrap_config,
    download_file,
    download_pem,
    import_rhel,
    load_bootstrap_output,
    login_registry,
    pause_until_complete,
    terraform_application_env,
    terraform_bootstrap,
)

@pytest.fixture(autouse=True)
def clear_workspace():
    if path.exists("./workspace_test"):
        shutil.rmtree("./workspace_test")

logger = logging.getLogger(__name__)

@pytest.fixture()
def workspace():
    create_workspace("./workspace_test")
    return "./workspace_test"


@pytest.fixture()
def registry():
    return "cloudzeroopscontainerregistryrattler.azurecr.io"


# def test_deployer_cli():
#     runner = CliRunner()
#     result = runner.invoke(cli)
#     assert result.exit_code == 0

# def test_create_workspace():
#     create_workspace("./workspace_test")
#     assert path.exists("./workspace_test")
#     create_workspace("./workspace_test")

# def test_git(workspace):
#     clone_repo(workspace)
#     assert path.exists(path.join(workspace, ".git"))
#     clone_repo(workspace)
#     assert path.exists(path.join(workspace, ".git"))

#     checkout_branch(workspace, "master")
#     output = subprocess.run(["git", "branch"], capture_output=True, text=True)
#     assert "master" in output.stdout

# def test_diffie_helman(workspace):
#     resp = diffie_helman(workspace, 8)
#     pause_until_complete(resp)
#     assert path.exists(path.join(workspace, 'dhparams.pem'))
#     resp = diffie_helman(workspace, 8)
#     pause_until_complete(resp)
#     assert path.exists(path.join(workspace, 'dhparams.pem'))

# def test_import(registry):
#     subprocess.run(f"az acr repository delete --image rhel-py --name {registry} --yes".split())

#     assert import_rhel('cloudzeroopsregistry.azurecr.io', registry) == 0

#     output = subprocess.run(f"az acr repository list --name {registry} --output table".split(), capture_output=True, text=True)
#     assert "rhel-py" in output.stdout

#     assert import_rhel('cloudzeroopsregistry.azurecr.io', registry) == 0
#     output = subprocess.run(f"az acr repository list --name {registry} --output table".split(), capture_output=True, text=True)
#     assert "rhel-py" in output.stdout


# def test_build_images(workspace, registry):
#     clone_repo(workspace)
#     checkout_branch(workspace, "staging")
#     import_rhel("cloudzeroopsregistry.azurecr.io", registry)
#     proc_nginx = build_nginx(workspace, registry, tag="test")
#     proc_atat = build_atat(workspace, registry, tag="test")
#     pause_until_complete(proc_atat)
#     pause_until_complete(proc_nginx)


# def test_download_files(workspace):
#     clone_repo(workspace=workspace)

#     assert download_pem(workspace) == 0
#     assert path.exists(path.join(workspace, "atatdev.pem"))

#     assert download_bootstrap_config(workspace) == 0
#     assert path.exists(
#         path.join(workspace, "terraform", "providers", "bootstrap", "bootstrap.tfvars")
#     )

#     assert download_application_env_config(workspace) == 0
#     assert path.exists(
#         path.join(
#             workspace, "terraform", "providers", "application_env", "app.tfvars.json"
#         )
#     )


# def test_terraform_bootstrap(workspace):
#     clone_repo(workspace)
#     download_pem(workspace)
#     download_bootstrap_config(workspace)
#     terraform_bootstrap(workspace)
#     assert path.exists(
#         path.join(
#             workspace,
#             "terraform",
#             "providers",
#             "application_env",
#             "bootstrap_output.tfvars.json",
#         )
#     )
#     assert path.exists(
#         path.join(
#             workspace,
#             "terraform",
#             "providers",
#             "application_env",
#             "bootstrap_output.tfvars",
#         )
#     )


def test_terraform_bootstrap(workspace):
    clone_repo(workspace)
    # workspace = path.abspath( path.join(os.getcwd(), "../../"))
    workspace = "./workspace_test"

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
    time.sleep(5)
    # login_registry(bootstrap_outputs["ops_container_registry_name"])

    # nginx_proc = build_nginx(workspace=workspace, registry=bootstrap_outputs["ops_container_registry_name"])
    # atat_proc = build_atat(workspace=workspace, registry=bootstrap_outputs["ops_container_registry_name"])

    # pause_until_complete(nginx_proc)
    # pause_until_complete(atat_proc)
    terraform_application_env(workspace)
    assert path.exists(
        path.join(
            workspace,
            "terraform",
            "providers",
            "application_env",
            "bootstrap_output.tfvars",
        )
    )
