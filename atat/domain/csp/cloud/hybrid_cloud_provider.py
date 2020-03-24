import contextlib
from uuid import uuid4

from atat.domain.csp.cloud.azure_cloud_provider import AzureCloudProvider
from atat.domain.csp.cloud.exceptions import UnknownServerException
from atat.domain.csp.cloud.mock_cloud_provider import MockCloudProvider
from atat.domain.csp.cloud.models import *


@contextlib.contextmanager
def monkeypatched(object_, name, patch):
    """ Temporarily monkeypatches an object. """

    pre_patched_value = getattr(object_, name)
    setattr(object_, name, patch)
    yield object_
    setattr(object_, name, pre_patched_value)


class HybridCloudProvider(object):
    def __init__(self, azure: AzureCloudProvider, mock: MockCloudProvider):
        self.azure = azure
        self.mock = mock
        self.tenant_id = None

    def create_tenant(self, payload):
        """In this step, we store a tenant ID with a username and password
        provided to the application ahead of time. Normally the tenant is
        created through API calls to Azure, however for the hybrid mock we
        will generate and store a tenant with a simple generated UUID string
        instead.
        """

        # This is the username and password for the primary point of contact
        # for a portfolio. These are normally generated for the tenant, but
        # but here we just inject existing and valid credentials.
        tenant_admin_username = self.azure.config["AZURE_TENANT_ADMIN_USERNAME"]
        tenant_admin_password = self.azure.config["AZURE_TENANT_ADMIN_PASSWORD"]
        user_object_id = self.azure.config["AZURE_USER_OBJECT_ID"]

        self.tenant_id = str(uuid4())

        # This is our mocked result of what would have been the API call to
        # create a tenant.
        result_dict = {
            "tenant_id": self.tenant_id,
            "user_id": "HybridCSPIntegrationTestUser",
            "user_object_id": user_object_id,
            "tenant_admin_username": tenant_admin_username,
            "tenant_admin_password": tenant_admin_password,
        }

        # Here we use the tenant id as a KeyVault key to store the primary
        # point of contact credentials.
        self.azure.create_tenant_creds(
            self.tenant_id,
            KeyVaultCredentials(
                root_tenant_id=self.azure.tenant_id,
                root_sp_client_id=self.azure.client_id,
                root_sp_key=self.azure.secret_key,
                tenant_id=self.azure.tenant_id,
                tenant_admin_username=tenant_admin_username,
                tenant_admin_password=tenant_admin_password,
            ),
        )

        return TenantCSPResult(domain_name="dancorriganpromptworks", **result_dict)

    def create_billing_profile_creation(self, payload):
        return self.mock.create_billing_profile_creation(payload)

    def create_billing_profile_verification(self, payload):
        return self.mock.create_billing_profile_verification(payload)

    def create_billing_profile_tenant_access(self, payload):
        return self.mock.create_billing_profile_tenant_access(payload)

    def create_task_order_billing_creation(self, payload):
        return self.mock.create_task_order_billing_creation(payload)

    def create_task_order_billing_verification(self, payload):
        return self.mock.create_task_order_billing_verification(payload)

    def create_billing_instruction(self, payload):
        return self.mock.create_billing_instruction(payload)

    def create_product_purchase(self, payload):
        return self.mock.create_product_purchase(payload)

    def create_product_purchase_verification(self, payload):
        return self.mock.create_product_purchase_verification(payload)

    def create_tenant_principal_app(self, payload):
        with monkeypatched(
            self.azure,
            "tenant_principal_app_display_name",
            f"Hybrid ATAT Remote Admin :: {payload.display_name}",
        ):
            return self.azure.create_tenant_principal_app(payload)

    def create_tenant_principal(self, payload):
        return self.azure.create_tenant_principal(payload)

    def create_tenant_principal_credential(self, payload):
        token = self.azure._get_tenant_admin_token(
            payload.tenant_id, self.azure.graph_resource
        )

        original_update_tenant_creds = self.azure.update_tenant_creds

        def mocked_update_tenant_creds(tenant_id, creds):
            """Necessary to ensure the root tenant id credentials are saved in
            KeyVault at the end of this stage.
            """
            creds.tenant_id = self.azure.tenant_id
            original_update_tenant_creds(tenant_id, creds)

        with monkeypatched(self.azure, "_get_tenant_admin_token", lambda *_a: token):
            with monkeypatched(
                self.azure, "update_tenant_creds", mocked_update_tenant_creds
            ):
                return self.azure.create_tenant_principal_credential(payload)

    def create_admin_role_definition(self, payload):
        return self.azure.create_admin_role_definition(payload)

    def create_principal_admin_role(self, payload):
        return self.azure.create_principal_admin_role(payload)

    def create_initial_mgmt_group(self, payload):
        return self.azure.create_initial_mgmt_group(payload)

    def create_initial_mgmt_group_verification(self, payload):
        return self.azure.create_initial_mgmt_group_verification(payload)

    def create_tenant_admin_ownership(self, payload):
        """For this step, we needed to be able to retrieve the elevated management 
        token from KeyVault with the original tenant id, but make the role assignment 
        request with the root credentials.
        """
        token = self.azure._get_elevated_management_token(payload.tenant_id)
        payload.tenant_id = self.azure.tenant_id
        with monkeypatched(
            self.azure, "_get_elevated_management_token", lambda _: token
        ):
            try:
                return self.azure.create_tenant_admin_ownership(payload)
            except UnknownServerException:
                return TenantAdminOwnershipCSPResult(
                    id=self.azure.config["AZURE_ADMIN_ROLE_ASSIGNMENT_ID"]
                )

    def create_tenant_principal_ownership(self, payload):
        token = self.azure._get_elevated_management_token(payload.tenant_id)
        payload.tenant_id = self.azure.tenant_id
        with monkeypatched(
            self.azure, "_get_elevated_management_token", lambda _: token
        ):
            return self.azure.create_tenant_principal_ownership(payload)

    def create_billing_owner(self, payload):
        token = self.azure._get_tenant_principal_token(
            payload.tenant_id, resource=self.azure.graph_resource
        )
        payload.tenant_id = self.azure.tenant_id
        with monkeypatched(
            self.azure, "_get_tenant_principal_token", lambda *a, **kw: token
        ):
            return self.azure.create_billing_owner(payload)

    def create_tenant_admin_credential_reset(self, payload):
        return self.azure.create_tenant_admin_credential_reset(payload)

    def create_policies(self, payload):
        return self.azure.create_policies(payload)
