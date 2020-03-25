import pendulum
import pytest

from atat.domain.csp import HybridCSP
from atat.domain.csp.cloud.models import (
    KeyVaultCredentials,
    TenantCSPPayload,
    InitialMgmtGroupCSPPayload,
)
from atat.jobs import do_create_application
from atat.models import FSMStates, PortfolioStateMachine
from tests.factories import (
    ApplicationFactory,
    CLINFactory,
    PortfolioFactory,
    PortfolioStateMachineFactory,
    TaskOrderFactory,
    UserFactory,
)
from uuid import uuid4


@pytest.fixture(scope="function")
def portfolio():
    today = pendulum.today()
    yesterday = today.subtract(days=1)
    future = today.add(days=100)

    owner = UserFactory.create()
    portfolio = PortfolioFactory.create(owner=owner)
    ApplicationFactory.create(portfolio=portfolio, environments=[{"name": "dev"}])

    TaskOrderFactory.create(
        portfolio=portfolio,
        signed_at=yesterday,
        clins=[CLINFactory.create(start_date=yesterday, end_date=future)],
    )

    return portfolio


@pytest.fixture(scope="function")
def csp(app):
    return HybridCSP(app, test_mode=True).cloud


@pytest.fixture(scope="function")
def state_machine(app, csp, portfolio):
    return PortfolioStateMachineFactory.create(portfolio=portfolio, cloud=csp)


@pytest.mark.hybrid
def test_hybrid_cloud(pytestconfig, state_machine: PortfolioStateMachine):
    csp_data = {}
    config = {"billing_account_name": "billing_account_name"}

    # Starting
    state_machine.trigger_next_transition(csp_data=csp_data)
    # Started
    state_machine.trigger_next_transition(csp_data=csp_data)

    while state_machine.state != FSMStates.COMPLETED:
        collected_data = dict(
            list(csp_data.items())
            + list(state_machine.portfolio.to_dictionary().items())
            + list(config.items())
        )

        state_machine.trigger_next_transition(csp_data=collected_data)
        assert (
            "created" in state_machine.state.value
            or state_machine.state == FSMStates.COMPLETED
        )

        csp_data = state_machine.portfolio.csp_data


@pytest.mark.hybrid
def test_hybrid_create_application_job(session, csp):
    payload = TenantCSPPayload(
        **dict(
            user_id="admin",
            password="JediJan13$coot",  # pragma: allowlist secret
            domain_name="jediccpospawnedtenant2",
            first_name="Tedry",
            last_name="Tenet",
            country_code="US",
            password_recovery_email_address="thomas@promptworks.com",
        )
    )

    csp.tenant_id = csp.azure.tenant_id

    csp.azure.create_tenant_creds(
        csp.tenant_id,
        KeyVaultCredentials(
            root_tenant_id=csp.azure.tenant_id,
            root_sp_client_id=csp.azure.client_id,
            root_sp_key=csp.azure.secret_key,
            tenant_id=csp.azure.tenant_id,
            tenant_sp_key=csp.azure.secret_key,
            tenant_sp_client_id=csp.azure.client_id,
        ),
    )

    portfolio = PortfolioFactory.create(
        csp_data={
            "tenant_id": csp.azure.tenant_id,
            "root_management_group_id": csp.azure.config["AZURE_ROOT_MGMT_GROUP_ID"],
        }
    )

    application = ApplicationFactory.create(portfolio=portfolio, cloud_id=None)
    do_create_application(csp, application.id)
    session.refresh(application)

    assert application.cloud_id
