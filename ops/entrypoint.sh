#! /bin/bash

# Required environment variables
# ------------------------------
# $az_environment
# $azure_subscription_id
# $azure_tenant
# $build_branch
# $circle_api_token
# $operator_sp_client_id
# $operator_sp_object_id
# $operator_sp_secret
# $operator_sp_url

export ARM_CLIENT_ID_BUILD="$operator_sp_client_id"
export ARM_CLIENT_ID="$operator_sp_client_id"
export ARM_CLIENT_SECRET_BUILD="$operator_sp_secret"
export ARM_CLIENT_SECRET="$operator_sp_secret"
export ARM_SUBSCRIPTION_ID_BUILD="$azure_subscription_id"
export ARM_SUBSCRIPTION_ID="$azure_subscription_id"
export ARM_TENANT_ID_BUILD="$azure_tenant"
export ARM_TENANT_ID="$azure_tenant"
export AZ_CLI_SP="$operator_sp_url"
export AZ_ENVIRONMENT="$az_environment"
export AZURE_CLIENT_ID="$operator_sp_client_id"
export AZURE_CLIENT_SECRET="$operator_sp_secret"
export AZURE_TENANT_ID="$azure_tenant"
export BUILD_BRANCH="$build_branch"
export CIRCLE_CI_API_KEY="$circle_api_token"
export SUBSCRIPTION_CID="$operator_sp_client_id"
export SUBSCRIPTION_ID="$azure_subscription_id"
export SUBSCRIPTION_SECRET="$operator_sp_secret"
export SUBSCRIPTION_TENANT="$azure_tenant"
export TF_VAR_azure_subscription_id="$azure_subscription_id"
export TF_VAR_OPS_CID="$operator_sp_client_id"
export TF_VAR_OPS_OID="$operator_sp_object_id"
export TF_VAR_OPS_SEC="$operator_sp_secret"
export TF_VAR_OPS_SP_URL="$operator_sp_url"

az login \
    --service-principal \
    --username "$operator_sp_client_id" \
    --password "$operator_sp_secret" \
    --tenant "$azure_tenant"
az extension add --name aks-preview
az extension update --name aks-preview
az feature register --name AKS-AzurePolicyAutoApprove --namespace Microsoft.ContainerService
az provider register --namespace Microsoft.ContainerService

ansible-playbook site.yml \
    -vvv \
    --extra-vars \
        app_name=atat \
        scripts_dir=/src/script \
        az_environment=dryrun3 \
        show_bs_env=yes \
        show_app_env_outputs=yes \
        tfvars_file_path=/src/terraform/providers/bootstrap/dryrun.tfvars \
        tf_base_dir=/src/terraform/providers \
        show_app_env_outputs=true \
        bootstrap_subscription_id=$SUBSCRIPTION_ID \
        application_subscription_id=$SUBSCRIPTION_ID
        