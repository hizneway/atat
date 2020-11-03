import os
import shutil
import subprocess
from os import path

import pytest
from deployer import deploy


@pytest.fixture(autouse=True)
def clear_config():
    if path.exists("./deploy_config_test"):
        shutil.rmtree("./deploy_config_test")


@pytest.fixture()
def config_dir():
    deploy.ensure_directory("./deploy_config_test")
    return "./deploy_config_test"


def test_deploy_init(
    config_dir,
):
    # arrange
    storage_account = "czopsstorageaccount2"
    template_container = "tf-configs"
    certs_container = "certs"

    # act
    deploy.init(
        config_dir=config_dir,
        storage_account=storage_account,
        template_container=template_container,
        certs_container=certs_container,
    )

    # assert
    assert path.exists(config_dir)
    assert path.exists(path.join(config_dir, "bootstrap.tfvars"))
    assert path.exists(path.join(config_dir, "app.tfvars.json"))
    assert path.exists(path.join(config_dir, "atatdev.pem"))
    assert path.exists(path.join(config_dir, "dhparams.pem"))


def test_create_service_principle(config_dir):
    sp = deploy.create_service_principle(config_dir)
    assert sp.app_id is not None
    assert sp.object_id is not None
    assert sp.secret is not None
    assert sp.url is not None

    # test idempotence
    sp2 = deploy.create_service_principle(config_dir)
    assert sp.app_id == sp2.app_id
    assert sp.object_id == sp2.object_id
    assert sp.secret == sp2.secret
    assert sp.url == sp2.url
