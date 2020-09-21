# Intro

Circle ci config was parameterized to facilitate control over images and their destinations.

## Requirements

* Circle CI API key
* Azure tenant and subscription IDs for the target registries
* Azure Service Principal credentials
* a container registry URL for the app env and one for ops, they can be the same.


## Usage

You can use your method of choice to create POST request.  The request looks like:


URL: `https://circleci.com/api/v2/project/github/dod-ccpo/atst/pipeline`

Body:

```
{
    "branch": "build-ops-container",
    "parameters": {
         "subscription_id": "$target_deploy_env_subscription_id", //string the subscription id of the target environment of the application
         "tenant_id": "$tenant_id", //string  the tenant id of the target app environment
         "container_registry": "$target_deploy_env_registry", //string target registry of the app environment
         "atat_image_tag": "$target_deploy_env_registry/$atat_image_name:$atat_image_tag", //string  repo, image,tag of atat
         "nginx_image_tag": "$target_deploy_env_registry/$nginx_image_name:$nginx_image_tag", //string repo, image, tag of nginx
         "sp": "$target_deploy_service_principal_client_id",  //string service principal client id w/ appropriate credentials to build out an atat env (if a deployment image is built)
         "sp_object_id": "$target_deploy_service_principal_object_id", //string service principal object id relative to above 
         "operator_sp_url": "$target_deploy_service_principal_url", //string service principal URL relative to above
         "sp_password": "$target_deploy_service_principal_password", //string service principal secret relative to above
         "build_and_push_ops_image": false, //bool whether to trigger the ops image build and deploy (this will create an image that can deploy atat)
         "build_and_push_app_images": true, //bool  whether to trigger the app image build (this will build the nginx and atat images)
         "ops_registry": "$canonical_ops_registry", //string where to source the hardened base images for atat image builds
         "ops_subscription_id": "$canonical_ops_subscription_id" //string which subscription the ops registry above exists
    }
}

```

