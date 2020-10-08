#!/bin/bash

# Required environment variables
# ------------------------------
# $az_environment
# $azure_subscription_id
# $azure_tenant
# $operator_sp_client_id
# $operator_sp_object_id
# $operator_sp_secret
# $operator_sp_url

env DOCKER_BUILDKIT=1 docker build  \
    --build-arg azure_subscription_id=$azure_subscription_id \
    --build-arg azure_tenant=$azure_tenant \
    --build-arg environment=$az_environment \
    --build-arg operator_sp_client_id=$operator_sp_client_id \
    --build-arg operator_sp_object_id=$operator_sp_object_id \
    --build-arg operator_sp_secret=$operator_sp_secret \
    --build-arg operator_sp_url=$operator_sp_url \
    . -f Dockerfile.ops -t ops:latest
