import re
from enum import Enum
from unittest.mock import Mock, patch

import pendulum
import pydantic
import pytest
from tests.factories import (
    ApplicationFactory,
    CLINFactory,
    PortfolioFactory,
    PortfolioStateMachineFactory,
    TaskOrderFactory,
    UserFactory,
)

from atst.models import FSMStates, PortfolioStateMachine, TaskOrder
from atst.models.mixins.state_machines import (
    AzureStages,
    StageStates,
    _build_csp_states,
    _build_transitions,
    compose_state,
)
from atst.models.portfolio import Portfolio
from atst.models.portfolio_state_machine import (
    StateMachineMisconfiguredError,
    _stage_state_to_stage_name,
    _stage_to_classname,
    get_stage_csp_class,
)

# TODO: Write failure case tests


class AzureStagesTest(Enum):
    TENANT = "tenant"


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
def state_machine(portfolio):
    return PortfolioStateMachineFactory.create(portfolio=portfolio)


@pytest.mark.state_machine
def test_fsm_creation(portfolio):
    sm = PortfolioStateMachineFactory.create(portfolio=portfolio)
    assert sm.portfolio


@pytest.mark.state_machine
def test_state_machine_trigger_next_transition(portfolio):
    sm = PortfolioStateMachineFactory.create(portfolio=portfolio)

    sm.trigger_next_transition()
    assert sm.current_state == FSMStates.STARTING

    sm.trigger_next_transition()
    assert sm.current_state == FSMStates.STARTED


@pytest.mark.state_machine
def test_state_machine_compose_state():
    assert (
        compose_state(AzureStages.TENANT, StageStates.CREATED)
        == FSMStates.TENANT_CREATED
    )


@pytest.mark.state_machine
def test_stage_to_classname():
    assert (
        _stage_to_classname(AzureStages.BILLING_PROFILE_CREATION.name)
        == "BillingProfileCreation"
    )


@pytest.mark.state_machine
def test_get_stage_csp_class():
    csp_class = get_stage_csp_class(list(AzureStages)[0].name.lower(), "payload")
    assert isinstance(csp_class, pydantic.main.ModelMetaclass)


@pytest.mark.state_machine
def test_get_stage_csp_class_import_fail():
    with pytest.raises(StateMachineMisconfiguredError):
        csp_class = get_stage_csp_class("doesnotexist", "payload")


@pytest.mark.state_machine
def test_build_transitions():
    states, transitions = _build_transitions(AzureStagesTest)
    assert [s.get("name").name for s in states] == [
        "TENANT_CREATED",
        "TENANT_IN_PROGRESS",
        "TENANT_FAILED",
    ]
    assert [s.get("tags") for s in states] == [
        ["TENANT", "CREATED"],
        ["TENANT", "IN_PROGRESS"],
        ["TENANT", "FAILED"],
    ]
    assert [t.get("trigger") for t in transitions] == [
        "complete",
        "create_tenant",
        "finish_tenant",
        "fail_tenant",
        "resume_progress_tenant",
    ]


@pytest.mark.state_machine
def test_build_csp_states():
    states = _build_csp_states(AzureStagesTest)
    assert list(states) == [
        "UNSTARTED",
        "STARTING",
        "STARTED",
        "COMPLETED",
        "FAILED",
        "TENANT_CREATED",
        "TENANT_IN_PROGRESS",
        "TENANT_FAILED",
    ]


@pytest.mark.state_machine
def test_state_machine_valid_data_classes_for_stages():
    for stage in AzureStages:
        assert get_stage_csp_class(stage.name.lower(), "payload") is not None
        assert get_stage_csp_class(stage.name.lower(), "result") is not None


@pytest.mark.state_machine
def test_attach_machine(state_machine):
    state_machine.machine = None
    state_machine.attach_machine(stages=AzureStagesTest)
    assert list(state_machine.machine.events) == [
        "init",
        "start",
        "reset",
        "fail",
        "complete",
        "create_tenant",
        "finish_tenant",
        "fail_tenant",
        "resume_progress_tenant",
    ]


@pytest.mark.state_machine
def test_current_state_property(state_machine):
    assert state_machine.current_state == FSMStates.UNSTARTED
    state_machine.state = FSMStates.TENANT_IN_PROGRESS
    assert state_machine.current_state == FSMStates.TENANT_IN_PROGRESS


@pytest.mark.state_machine
def test_fail_stage(state_machine):
    state_machine.state = FSMStates.TENANT_IN_PROGRESS
    state_machine.portfolio.csp_data = {}
    state_machine.fail_stage("tenant")
    assert state_machine.state == FSMStates.TENANT_FAILED


@pytest.mark.state_machine
def test_fail_stage_invalid_triggers(state_machine):
    state_machine.state = FSMStates.TENANT_IN_PROGRESS
    state_machine.portfolio.csp_data = {}
    state_machine.machine.get_triggers = Mock(return_value=["some", "triggers", "here"])
    state_machine.fail_stage("tenant")
    assert state_machine.state == FSMStates.TENANT_IN_PROGRESS


@pytest.mark.state_machine
def test_fail_stage_invalid_stage(state_machine):
    state_machine.state = FSMStates.TENANT_IN_PROGRESS
    state_machine.portfolio.csp_data = {}
    portfolio.csp_data = {}
    state_machine.fail_stage("invalid stage")
    assert state_machine.state == FSMStates.TENANT_IN_PROGRESS


@pytest.mark.state_machine
def test_finish_stage(state_machine):
    state_machine.state = FSMStates.TENANT_IN_PROGRESS
    state_machine.portfolio.csp_data = {}
    state_machine.finish_stage("tenant")
    assert state_machine.state == FSMStates.TENANT_CREATED


@pytest.mark.state_machine
def test_finish_stage_invalid_triggers(state_machine):
    state_machine.state = FSMStates.TENANT_IN_PROGRESS
    state_machine.portfolio.csp_data = {}

    state_machine.machine.get_triggers = Mock(return_value=["some", "triggers", "here"])
    state_machine.finish_stage("tenant")
    assert state_machine.state == FSMStates.TENANT_IN_PROGRESS


@pytest.mark.state_machine
def test_finish_stage_invalid_stage(state_machine):
    state_machine.state = FSMStates.TENANT_IN_PROGRESS
    state_machine.portfolio.csp_data = {}
    portfolio.csp_data = {}
    state_machine.finish_stage("invalid stage")
    assert state_machine.state == FSMStates.TENANT_IN_PROGRESS


@pytest.mark.state_machine
def test_stage_state_to_stage_name():
    stage = _stage_state_to_stage_name(
        FSMStates.TENANT_IN_PROGRESS, StageStates.IN_PROGRESS
    )
    assert stage == "tenant"


@pytest.mark.state_machine
def test_state_machine_initialization(state_machine):
    for stage in AzureStages:

        # check that all stages have a 'create' and 'fail' triggers
        stage_name = stage.name.lower()
        for trigger_prefix in ["create", "fail"]:
            assert hasattr(state_machine, trigger_prefix + "_" + stage_name)

        # check that machine
        in_progress_triggers = state_machine.machine.get_triggers(
            stage.name + "_IN_PROGRESS"
        )
        assert [
            "reset",
            "fail",
            "finish_" + stage_name,
            "fail_" + stage_name,
        ] == in_progress_triggers

        started_triggers = state_machine.machine.get_triggers("STARTED")
        create_trigger = next(
            filter(
                lambda trigger: trigger.startswith("create_"),
                state_machine.machine.get_triggers(FSMStates.STARTED.name),
            ),
            None,
        )
        assert ["reset", "fail", create_trigger] == started_triggers


@pytest.mark.state_machine
@patch("atst.domain.csp.cloud.MockCloudProvider")
def test_fsm_transition_start(mock_cloud_provider, portfolio: Portfolio):
    mock_cloud_provider._authorize.return_value = None
    mock_cloud_provider._maybe_raise.return_value = None

    expected_states = [
        FSMStates.STARTING,
        FSMStates.STARTED,
        FSMStates.TENANT_CREATED,
        FSMStates.BILLING_PROFILE_CREATION_CREATED,
        FSMStates.BILLING_PROFILE_VERIFICATION_CREATED,
        FSMStates.BILLING_PROFILE_TENANT_ACCESS_CREATED,
        FSMStates.TASK_ORDER_BILLING_CREATION_CREATED,
        FSMStates.TASK_ORDER_BILLING_VERIFICATION_CREATED,
        FSMStates.BILLING_INSTRUCTION_CREATED,
        FSMStates.PRODUCT_PURCHASE_CREATED,
        FSMStates.PRODUCT_PURCHASE_VERIFICATION_CREATED,
        FSMStates.TENANT_PRINCIPAL_APP_CREATED,
        FSMStates.TENANT_PRINCIPAL_CREATED,
        FSMStates.TENANT_PRINCIPAL_CREDENTIAL_CREATED,
        FSMStates.ADMIN_ROLE_DEFINITION_CREATED,
        FSMStates.PRINCIPAL_ADMIN_ROLE_CREATED,
        FSMStates.INITIAL_MGMT_GROUP_CREATED,
        FSMStates.INITIAL_MGMT_GROUP_VERIFICATION_CREATED,
        FSMStates.TENANT_ADMIN_OWNERSHIP_CREATED,
        FSMStates.TENANT_PRINCIPAL_OWNERSHIP_CREATED,
        FSMStates.BILLING_OWNER_CREATED,
        FSMStates.COMPLETED,
    ]

    if portfolio.csp_data is not None:
        csp_data = portfolio.csp_data
    else:
        csp_data = {}

    ppoc = portfolio.owner

    user_id = f"{ppoc.first_name[0]}{ppoc.last_name}".lower()
    domain_name = re.sub("[^0-9a-zA-Z]+", "", portfolio.name).lower()

    initial_task_order: TaskOrder = portfolio.task_orders[0]
    initial_clin = initial_task_order.sorted_clins[0]

    portfolio_data = {
        "user_id": user_id,
        "password": "jklfsdNCVD83nklds2#202",  # pragma: allowlist secret
        "domain_name": domain_name,
        "display_name": "mgmt group display name",
        "management_group_name": "mgmt-group-uuid",
        "first_name": ppoc.first_name,
        "last_name": ppoc.last_name,
        "country_code": "US",
        "password_recovery_email_address": ppoc.email,
        "address": {  # TODO: TBD if we're sourcing this from data or config
            "company_name": "",
            "address_line_1": "",
            "city": "",
            "region": "",
            "country": "",
            "postal_code": "",
        },
        "billing_profile_display_name": "My Billing Profile",
        "initial_clin_amount": initial_clin.obligated_amount,
        "initial_clin_start_date": initial_clin.start_date.strftime("%Y/%m/%d"),
        "initial_clin_end_date": initial_clin.end_date.strftime("%Y/%m/%d"),
        "initial_clin_type": initial_clin.number,
        "initial_task_order_id": initial_task_order.number,
    }

    config = {"billing_account_name": "billing_account_name"}

    sm: PortfolioStateMachine = PortfolioStateMachineFactory.create(portfolio=portfolio)
    assert sm.portfolio
    assert sm.state == FSMStates.UNSTARTED

    for expected_state in expected_states:
        collected_data = dict(
            list(csp_data.items()) + list(portfolio_data.items()) + list(config.items())
        )
        sm.trigger_next_transition(csp_data=collected_data)
        assert sm.state == expected_state
        if portfolio.csp_data is not None:
            csp_data = portfolio.csp_data
        else:
            csp_data = {}
