#!/bin/bash
set -x
set -e

[ ! -f service_principal.json ] && ./create-service-principle.sh
sp=$(cat service_principal.json)

echo "exporting terraform creds"
export ARM_CLIENT_ID=$(echo $sp | jq -r '.appId')
export ARM_CLIENT_SECRET=$(echo $sp | jq -r '.password')
export ARM_SUBSCRIPTION_ID=$(az account show --query id --output tsv)
export ARM_TENANT_ID=$(echo $sp | jq -r '.tenant')
export TF_VAR_operator_subscription_id=$ARM_SUBSCRIPTION_ID
export TF_VAR_operator_client_id=$ARM_CLIENT_ID
export TF_VAR_operator_client_secret=$ARM_CLIENT_SECRET
export TF_VAR_operator_tenant_id=$ARM_TENANT_ID

echo "ARM_CLIENT_ID=$ARM_CLIENT_ID"
echo "ARM_CLIENT_SECRET=$ARM_CLIENT_SECRET"
echo "ARM_SUBSCRIPTION_ID=$ARM_SUBSCRIPTION_ID"
echo "ARM_TENANT_ID=$ARM_TENANT_ID"
echo "-----------"
echo $TF_VAR_operator_subscription_id
echo $TF_VAR_operator_client_id
echo $TF_VAR_operator_client_secret
echo $TF_VAR_operator_tenant_id

# If we previously ran this script and a storage account was created,
# temporarily allow connections from outside the subnet so that we can access
# terraform state
if [[ -z "${TF_VAR_resource_group_name}" ]] && [[ -z "${TF_VAR_storage_account_name}" ]]; then
  groups=$(az group list)
  deployment_group=$(echo $groups | jq -r -c '.[] | select(.name | endswith("$1"))'.name)
  accounts=$(az storage account list)
  deployment_storage_account=$(echo "$accounts" | jq -r -c '.[] | select(.name | endswith("$1"))'.name)
  if [[ ! -z "${deployment_group}" ]] && [[ ! -z "${deployment_storage_account}" ]]; then
    az storage account update --resource-group ${deployment_group} --name ${deployment_storage_account} --default-action Allow
  fi
else
  az storage account update --resource-group ${TF_VAR_resource_group_name} --name ${TF_VAR_storage_account_name} --default-action Allow
fi

echo "Terraform Bootstrap New Tenant"
cd ../../terraform/providers/bootstrap
terraform init
terraform plan -var "namespace=$1" -out out.plan .
terraform apply out.plan
echo "Now copying this state to the remote"
terraform init -force-copy

export REGISTRY_NAME=$(terraform output operations_container_registry_login_server)
export TF_VAR_resource_group_name=$(terraform output operations_resource_group_name)
export TF_VAR_storage_account_name=$(terraform output operations_storage_account_name)
export SUBNET_ID=$(terraform output operations_deployment_subnet_id)
export OPERATIONS_VIRTUAL_NETWORK=$(terraform output operations_virtual_network)

# Lock the storage account to just the subnet that was created. We can't do
# this in Terraform. Since we don't want to whitelist an IP addresses and we
# want to limit the access of the storage account to a private subnet, if we
# set these options in terraform, we wouldn't be able to provision storage
# containers under the storage account.
az storage account update --resource-group ${TF_VAR_resource_group_name} --name ${TF_VAR_storage_account_name} --default-action Deny
az storage account network-rule add --resource-group ${TF_VAR_resource_group_name} --account-name ${TF_VAR_storage_account_name} --subnet ${SUBNET_ID}

echo "Building RHEL"
cd ../../../ops/phase1

cd ../../../atat-rhel-image
make run-build-push-task

echo "Building Python Base"
cd ../atst
az acr build --registry ${REGISTRY_NAME} \
  --build-arg IMAGE=${REGISTRY_NAME}/rhelubi:8.3 \
  --build-arg "redhat_username=$2" \
  --build-arg "redhat_password=$3" \
  --image rhel-py \
  --file python.Dockerfile \
  .

echo "Build Ops Dockerfile"
export COMMIT_SHA=$(git rev-parse HEAD)
az acr build --registry ${REGISTRY_NAME} \
  --build-arg IMAGE=${REGISTRY_NAME}/rhel-py:latest \
  --image ops:${COMMIT_SHA} \
  --file ops.Dockerfile \
  .

az container create \
  --resource-group ${TF_VAR_resource_group_name} \
  --name "$1-provisioner" \
  --ip-address Private \
  --vnet ${OPERATIONS_VIRTUAL_NETWORK} \
  --subnet deployment-subnet \
  --image ${REGISTRY_NAME}/ops:${COMMIT_SHA} \
  --registry-password ${TF_VAR_operator_client_secret} \
  --registry-username ${TF_VAR_operator_client_id} \
  --memory 4 \
  --cpu 4 \
  --secure-environment-variables "TF_VAR_resource_group_name=$TF_VAR_resource_group_name" "TF_VAR_storage_account_name=$TF_VAR_storage_account_name" "TF_VAR_operator_subscription_id=$TF_VAR_operator_subscription_id" "TF_VAR_operator_client_id=$TF_VAR_operator_client_id" "TF_VAR_operator_client_secret=$TF_VAR_operator_client_secret" "TF_VAR_operator_tenant_id=$TF_VAR_operator_tenant_id" \
  --restart-policy Never
