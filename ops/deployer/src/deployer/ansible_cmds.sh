#! /bin/bash
set -x
mkdir tmp

# If we start with the entrypoint, we can just pass
# Required environment variables
# ------------------------------
# export az_environment=


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

cd ../terraform/providers/bootstrap
mkdir tmp

az storage blob download --account-name czopsstorageaccount --container-name tf-configs --name bootstrap.tfvars -f tmp/bootstrap.tfvars
az storage blob download --account-name czopsstorageaccount --container-name certs --name atatdev.pem -f tmp/atatdev.pem --no-progress

terraform init .
terraform plan -input=false -out=tmp/plan.tfplan -var-file=tmp/bootstrap.tfvars
terraform apply -auto-approve tmp/plan.tfplan
terraform output -no-color > ../application_env/bootstrap_output.tfvars
export ops_container_registry_name="$(terraform output ops_container_registry_name)"

# Need to build docker images
# TODO: I do not need that bastion image
# TODO: Will this work w/ my new service principal doing the running?
# Piping to dev null to hide the login details
docker run -v $(pwd):/root/.azure mcr.microsoft.com/azure-cli az login --service-principal -u http://azure-cli-2020-10-14-11-09-42 -p t0Nh_.B_kLBm6NQscPX8cw_yKH3DrPNCzU --tenant b5ab0e1e-09f8-4258-afb7-fb17654bc5b3 > /dev/null

az acr import --name $ops_container_registry_name --source cloudzeroopsregistry.azurecr.io/rhel-py --image rhel-py
az acr build \
  --image nginx:poc-crt \
  --registry $ops_container_registry_name \
  --build-arg IMAGE=$ops_container_registry_name/rhel-py \
  --file nginx.Dockerfile \
  ../../
az acr build \
  --image atat:poc-crt \
  --registry $ops_container_registry_name \
  --build-arg IMAGE=$ops_container_registry_name/rhel-py \
  --file Dockerfile \
  ../../




cd ../application_env
mkdir tmp
az storage blob download --account-name czopsstorageaccount --container-name certs --name atatdev.pem -f tmp/atatdev.pem --no-progress

# this ought to be able to be threaded out early in the deployment process
openssl dhparam -out tmp/dhparams.pem 4096
export dhparam4096="tmp/dhparams.pem"

az storage blob download --account-name czopsstorageaccount --container-name tf-configs --name app.tfvars.json -f tmp/app.tfvars.json
# cd terraform/providers/application_env
terraform init -backend-config="container_name=tfstate" -backend-config="key=rattler.tfstate" -backend-config="resource_group_name=cloudzero-cloudzerorattlertfstate-rattler" -backend-config="storage_account_name=cloudzerorattlertfstate" .

# terraform init .
# missing mailgun api key and djparam4096
# Breaking because:
# expected "object_id" to be a valid UUID, got for admin_users
# This suggests the problem may actually have to do with the way the provider is configured.  Dunno.
#  https://github.com/hashicorp/vault-guides/issues/222
# terraform apply -var-file=tmp/app.tfvars.json -auto-approve .
# terraform plan -var-file=tmp/app.tfvars.json -var 'dhparam4096=tmp/dhparams.pem' -var 'mailgun_api_key=123' -var 'tls_cert_path=tmp/atatdev.pem' .



terraform apply -auto-approve -var-file=tmp/app.tfvars.json -var 'dhparam4096=tmp/dhparams.pem' -var 'mailgun_api_key=123' -var 'tls_cert_path=tmp/atatdev.pem' .
# # circleci
# az acr build --image atat:poc-crt --registry cloudzeroopsregistry.azurecr.io --build-arg IMAGE=cloudzeroopsregistry.azurecr.io/rhel-py --file nginx.Dockerfile .
# az acr build --image atat:poc-crt --registry cloudzeroopsregistry.azurecr.io --build-arg IMAGE=cloudzeroopsregistry.azurecr.io/rhel-py --file atat.Dockerfile .

# role azure_keyvault - wha?

# postgres - actually, can we just leave this in ansible?
