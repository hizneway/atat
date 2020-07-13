import pendulum
import pytest
from time import sleep
from uuid import uuid4

from atat.domain.csp import CSP
from atat.domain.csp.cloud.exceptions import UserProvisioningException
from atat.domain.csp.cloud.models import (
    EnvironmentCSPPayload,
    KeyVaultCredentials,
    UserCSPPayload,
    UserRoleCSPPayload,
    CostManagementQueryCSPPayload,
    SubscriptionCreationCSPPayload,
    SubscriptionVerificationCSPPayload,
)
from atat.jobs import (
    do_create_application,
    do_create_environment,
    do_create_environment_role,
    do_create_user,
)
from atat.models import PortfolioStates, PortfolioStateMachine
import tests.factories as factories
from tests.factories import (
    ApplicationFactory,
    ApplicationRoleFactory,
    ApplicationRoleStatus,
    CLINFactory,
    EnvironmentFactory,
    EnvironmentRoleFactory,
    PortfolioFactory,
    PortfolioStateMachineFactory,
    TaskOrderFactory,
    UserFactory,
)


def _create_active_taskorder(factory: TaskOrderFactory, portfolio):
    """
    Since some of the fixtures in this module are scoped to the test session
    and others to the function, they cannot easily share fixtures in common.
    In order to DRY up some of the code, this method takes the
    TaskOrderFactory as an argument. That way pytest does not object about
    whether the SQLAlchemy session fixture underlying the factory is session
    or function-scoped.
    """
    today = pendulum.today()
    yesterday = today.subtract(days=1)
    future = today.add(days=100)

    return factory.create(
        portfolio=portfolio,
        signed_at=yesterday,
        clins=[CLINFactory.create(start_date=yesterday, end_date=future)],
    )


@pytest.fixture(scope="function")
def portfolio(csp, app):
    owner = UserFactory.create()
    portfolio = PortfolioFactory.create(
        owner=owner,
        csp_data={
            "tenant_id": csp.mock_tenant_id,
            "domain_name": app.config["AZURE_HYBRID_TENANT_DOMAIN"],
            "root_management_group_name": csp.hybrid_tenant_id,
        },
    )

    _create_active_taskorder(TaskOrderFactory, portfolio)

    return portfolio


@pytest.fixture(scope="function")
def csp(app):
    csp = CSP(
        "hybrid",
        app.config,
        with_delay=False,
        with_failure=False,
        with_authorization=False,
    ).cloud
    csp.mock_tenant_id = str(uuid4())

    csp.azure.create_tenant_creds(
        csp.mock_tenant_id,
        KeyVaultCredentials(
            root_tenant_id=csp.azure.root_tenant_id,
            root_sp_client_id=csp.azure.client_id,
            root_sp_key=csp.azure.secret_key,
            tenant_id=csp.hybrid_tenant_id,
            tenant_sp_client_id=app.config["AZURE_HYBRID_CLIENT_ID"],
            tenant_sp_key=app.config["AZURE_HYBRID_SECRET_KEY"],
        ),
    )

    return csp


@pytest.mark.hybrid
class TestIntegration:
    @pytest.fixture(scope="session")
    def portfolio(self, csp, app):
        owner = UserFactory.create()
        portfolio = PortfolioFactory.create(owner=owner,)

        _create_active_taskorder(TaskOrderFactory, portfolio)

        return portfolio

    @pytest.fixture(scope="function")
    def tenant_id(self, portfolio):
        return portfolio.csp_data["tenant_id"]

    @pytest.fixture(scope="session")
    def user(self):
        first_name = f"test-user-{uuid4()}"
        return UserFactory.create(
            first_name=first_name, last_name="Solo", email=f"{first_name}@example.com"
        )

    @pytest.fixture(scope="session")
    def application(self, portfolio):
        return ApplicationFactory.create(portfolio=portfolio, cloud_id=None)

    @pytest.fixture(scope="session")
    def app_role(self, application, user):
        return ApplicationRoleFactory.create(
            application=application,
            user=user,
            status=ApplicationRoleStatus.ACTIVE,
            cloud_id=None,
        )

    @pytest.fixture(scope="session")
    def environment(self, application):
        return EnvironmentFactory.create(application=application, cloud_id=None)

    @pytest.fixture(scope="session")
    def csp(self, app):
        csp = CSP(
            "hybrid",
            app.config,
            with_delay=False,
            with_failure=False,
            with_authorization=False,
        ).cloud

        return csp

    @pytest.fixture(scope="session")
    def state_machine(self, app, csp, portfolio):
        return PortfolioStateMachineFactory.create(portfolio=portfolio, cloud=csp)

    @pytest.mark.depends(name="portfolio")
    def test_hybrid_provision_portfolio(self, state_machine: PortfolioStateMachine):
        csp_data = {}
        config = {"billing_account_name": "billing_account_name"}

        self.portfolio = state_machine.portfolio
        self.csp = state_machine.cloud

        while state_machine.state != PortfolioStates.COMPLETED:
            collected_data = dict(
                list(csp_data.items())
                + list(state_machine.portfolio.to_dictionary().items())
                + list(config.items())
            )

            state_machine.trigger_next_transition(csp_data=collected_data)
            # TODO: The _get_service_principal_token method call within
            # create_initial_mgmt_group fails periodically. There must be some kind
            # of race condition on the Azure side we're not accounting for. This
            # sleep is temporary and we should solve the race condition.
            sleep(1)
            assert (
                "created" in state_machine.state.value
                or state_machine.state == PortfolioStates.COMPLETED
            )

            csp_data = state_machine.portfolio.csp_data

    def _get_management_group(self, csp, tenant_id, management_group_id):
        sp_token = csp.azure._get_tenant_principal_token(tenant_id)
        headers = {
            "Authorization": f"Bearer {sp_token}",
        }
        response = csp.azure.sdk.requests.get(
            f"{csp.azure.sdk.cloud.endpoints.resource_manager}{management_group_id}?api-version=2020-02-01",
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    @pytest.mark.depends(name="application", on=["portfolio"])
    def test_hybrid_create_application_job(self, csp, application, tenant_id, session):
        do_create_application(csp, application.id)
        session.refresh(application)

        assert application.cloud_id

        mgmt_grp_resp = self._get_management_group(csp, tenant_id, application.cloud_id)

        # the portfolio management group should be the parent of the management
        # group we just created for the application
        assert (
            application.portfolio.csp_data["root_management_group_name"]
            in mgmt_grp_resp["properties"]["details"]["parent"]["id"]
        )

    @pytest.mark.depends(on=["application"])
    def test_hybrid_create_environment_job(self, csp, environment, tenant_id, session):
        do_create_environment(csp, environment.id)
        session.refresh(environment)

        assert environment.cloud_id

        mgmt_grp_resp = self._get_management_group(csp, tenant_id, environment.cloud_id)

        # the application management group should be the parent of the management
        # group we just created for the environment
        assert (
            environment.application.cloud_id
            in mgmt_grp_resp["properties"]["details"]["parent"]["id"]
        )

    @pytest.mark.depends(on=["application"])
    def test_hybrid_create_user_job(self, session, csp, app_role, portfolio):
        assert not app_role.cloud_id

        session.begin_nested()
        do_create_user(csp, [app_role.id])
        session.rollback()

        assert app_role.cloud_id


@pytest.mark.hybrid
def test_get_reporting_data(csp, app):
    """This test requires credentials for an app registration that has the
    "Invoice Section Reader" role for the invoice section scope being queried.
    """

    from_date = pendulum.now().subtract(years=1).add(days=1).format("YYYY-MM-DD")
    to_date = pendulum.now().format("YYYY-MM-DD")

    payload = CostManagementQueryCSPPayload(
        tenant_id=csp.azure.root_tenant_id,
        from_date=from_date,
        to_date=to_date,
        billing_profile_properties={"invoice_sections": [{"invoice_section_id": "",}],},
    )

    result = csp.get_reporting_data(payload)
    assert result.name


@pytest.mark.hybrid
@pytest.mark.skip(
    reason="We are using the mock cloud provider's subscription method right now"
)
def test_create_subscription(csp):
    environment = EnvironmentFactory.create()

    payload = SubscriptionCreationCSPPayload(
        display_name=environment.name,
        tenant_id=csp.mock_tenant_id,
        parent_group_id=csp.hybrid_tenant_id,
        billing_account_name=csp.azure.config["AZURE_BILLING_ACCOUNT_NAME"],
        billing_profile_name=csp.azure.config["AZURE_BILLING_PROFILE_ID"],
        invoice_section_name=csp.azure.config["AZURE_INVOICE_SECTION_ID"],
    )

    csp.create_subscription_creation(payload)


@pytest.mark.hybrid
def test_create_subscription_mocked(csp):
    # TODO: When we finally move over to azure, this mocked test should
    # probably be removed in favor of the above "test_create_subscription"
    # test.
    payload = SubscriptionCreationCSPPayload(
        tenant_id="tenant id",
        displayName="display name",
        parentGroupId="parent group id",
        billingAccountName="billing account name",
        billingProfileName="billing profile name",
        invoiceSectionName="invoice section name",
    )

    sub = csp.create_subscription(payload)
    sub_creation = csp.create_subscription_creation(payload)

    assert (
        sub.subscription_verify_url
        == sub_creation.subscription_verify_url
        == "https://zombo.com"
    )
    assert sub.subscription_retry_after == sub_creation.subscription_retry_after == 10


@pytest.mark.hybrid
def test_create_subscription_verification(csp):
    payload = SubscriptionVerificationCSPPayload(
        tenantId="tenant id", subscriptionVerifyUrl="subscription verify url"
    )
    assert csp.create_subscription_verification(payload).subscription_id


@pytest.mark.hybrid
class TestHybridUserManagement:
    @pytest.fixture
    def app_1(self, portfolio):
        return ApplicationFactory.create(portfolio=portfolio, cloud_id="321")

    @pytest.fixture
    def app_2(self, portfolio):
        return ApplicationFactory.create(portfolio=portfolio, cloud_id="123")

    @pytest.fixture
    def user(self):
        return UserFactory.create(
            first_name=f"test-user-{uuid4()}", last_name="Solo", email="han@example.com"
        )

    @pytest.fixture
    def app_role_1(self, app_1, user):
        return ApplicationRoleFactory.create(
            application=app_1,
            user=user,
            status=ApplicationRoleStatus.ACTIVE,
            cloud_id=None,
        )

    @pytest.fixture
    def app_role_2(self, app_2, user):
        return ApplicationRoleFactory.create(
            application=app_2,
            user=user,
            status=ApplicationRoleStatus.ACTIVE,
            cloud_id=None,
        )

    def test_hybrid_create_user_job(self, session, csp, app_role_1, portfolio):
        assert not app_role_1.cloud_id

        session.begin_nested()
        do_create_user(csp, [app_role_1.id])
        session.rollback()

        assert app_role_1.cloud_id

    def test_hybrid_user_has_tenant(self, session, csp, app_role_1, app_1, user):
        cloud_id = "123456"
        ApplicationRoleFactory.create(
            user=user,
            status=ApplicationRoleStatus.ACTIVE,
            cloud_id=cloud_id,
            application=ApplicationFactory.create(portfolio=app_1.portfolio),
        )

        session.begin_nested()
        do_create_user(csp, [app_role_1.id])
        session.rollback()

        assert app_role_1.cloud_id == cloud_id

    def test_hybrid_disable_user(self, session, csp, portfolio, app, app_role_1):
        session.begin_nested()
        do_create_user(csp, [app_role_1.id])
        session.rollback()

        payload = UserRoleCSPPayload(
            tenant_id=csp.mock_tenant_id,
            role="owner",
            management_group_id=csp.hybrid_tenant_id,
            user_object_id=app_role_1.cloud_id,
        )

        create_user_role_result = csp.azure.create_user_role(payload)
        disable_user_result = csp.azure.disable_user(
            csp.mock_tenant_id, create_user_role_result.id
        )
        assert disable_user_result["id"] == create_user_role_result.id

    def test_hybrid_do_create_environment_role_job(self, session, csp, app):
        environment_role = EnvironmentRoleFactory.create()
        environment_role.environment.cloud_id = csp.hybrid_tenant_id
        environment_role.application_role.cloud_id = app.config["AZURE_USER_OBJECT_ID"]
        environment_role.environment.portfolio.csp_data = {
            "tenant_id": csp.mock_tenant_id,
            "domain_name": app.config["AZURE_HYBRID_TENANT_DOMAIN"],
        }

        session.commit()

        try:
            do_create_environment_role(csp, environment_role.id)
        except UserProvisioningException as e:
            if "RoleAssignmentExists" not in str(e):
                raise e


@pytest.mark.hybrid
def test_create_user(csp):
    payload = UserCSPPayload(
        tenant_id=csp.mock_tenant_id,
        display_name="Test Testerson",
        tenant_host_name="testtenant",
        email="test@testerson.test",
        password="asdfghjkl",  # pragma: allowlist secret
    )

    result = csp.azure.create_user(payload)
    assert result.id
