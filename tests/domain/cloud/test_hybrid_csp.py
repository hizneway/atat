import pendulum
import pytest

from atat.domain.csp import HybridCSP
from atat.models import FSMStates, PortfolioStateMachine
from tests.factories import (
    ApplicationFactory,
    CLINFactory,
    PortfolioFactory,
    PortfolioStateMachineFactory,
    TaskOrderFactory,
    UserFactory,
)


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
def state_machine(app, portfolio):
    return PortfolioStateMachineFactory.create(
        portfolio=portfolio, cloud=HybridCSP(app, test_mode=True).cloud
    )


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
