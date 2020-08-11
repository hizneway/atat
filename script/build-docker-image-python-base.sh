#! /bin/bash

env DOCKER_BUILDKIT=1 docker build \
    -t atst:rhel-py \
    -f python.Dockerfile \
    --build-arg IMAGE=cloudzerodryrunregistry.azurecr.io/rhelubi:8.2 \
    --secret id=redhat_username,src=redhat_username.secret \
    --secret id=redhat_password,src=redhat_password.secret \
    .
