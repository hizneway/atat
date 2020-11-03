import json
import logging
import os
import subprocess
from dataclasses import dataclass
from os import path
from subprocess import CalledProcessError, CompletedProcess
from typing import Dict, Optional

import click


@click.group()
def deploy():
    click.echo("deploy code")

@dataclass
class ServicePrinciple:
    app_id: str
    object_id: str
    secret: str
    url: str


@click.option('--subscription')
@click.option('--config_dir', default="./deploy_config")
@click.option('--storage_account', default="czopsstorageaccount2")
@click.option('--template_container', default="tf-configs")
@click.option('--certs_container', default="certs")
@deploy.command()
def init(config_dir:str, subscription:str, storage_account:str, template_container:str, certs_container:str) -> None:
    ensure_directory(config_dir)
    dl_config_templates(config_dir=config_dir, storage_account=storage_account, template_container=template_container)
    dl_keys(config_dir=config_dir, storage_account=storage_account, certs_container=certs_container)
    # service_principle = create_service_principle(config_dir, subscription)

# apply_template(config_dir, service_principle)

# make this something shared
def ensure_directory(dir_path):
    if path.exists(dir_path):
        return

    os.mkdir(dir_path)


def download_file(
    storage_account: str, container_name: str, file_name: str, dest_path: str
) -> None:
    if path.exists(dest_path):
        return

    subprocess.run(
        f"az storage blob download --account-name {storage_account} --container-name {container_name} --name {file_name} -f {dest_path} --no-progress".split(),
        text=True,
        capture_output=True,
        check=True
    )


def dl_config_templates(config_dir, storage_account, template_container):
    for file in ["bootstrap.tfvars", "app.tfvars.json"]:
        download_file(
            storage_account,
            template_container,
            file,
            path.join(config_dir, file),
        )


def dl_keys(config_dir, storage_account, certs_container):
    for file in ["atatdev.pem", "dhparams.pem"]:
        download_file(
            storage_account,
            certs_container,
            file,
            path.join(config_dir, file),
        )


def create_service_principle(config_dir:str, subscription:str=None) -> ServicePrinciple:
    sp = load_service_principle(config_dir)
    if sp is not None:
        return sp

    res1 = json.loads(subprocess.run("az ad sp create-for-rbac".split(), stdout=subprocess.PIPE, check=True).stdout.decode('utf-8'))
    res2 = json.loads(subprocess.run(f"az ad sp show --id {res1['appId']}".split(), stdout=subprocess.PIPE, check=True).stdout.decode('utf-8'))

    sp_dict = {**res1, **res2}
    sp_json_path = path.join(config_dir, 'service_principle.json')
    with open(sp_json_path, 'w') as output:
        output.write(json.dumps(sp_dict))
    return load_service_principle(config_dir)

def load_service_principle(config_dir:str) -> Optional[ServicePrinciple]:
    sp_json_path = path.join(config_dir, 'service_principle.json')
    if not path.exists(sp_json_path):
        return

    with open(sp_json_path, 'r') as output:
        sp_dict = json.load(output)

    return ServicePrinciple(
        app_id=sp_dict["appId"],
        object_id=sp_dict["objectId"],
        secret=sp_dict["password"],
        url=sp_dict["name"],
    )



def apply_template(config_dir, service_principle):
    pass

cli = click.CommandCollection(sources=[deploy])

if __name__ == 'main':
    cli()
