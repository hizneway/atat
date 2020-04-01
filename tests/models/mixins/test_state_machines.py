from enum import Enum

import pytest

from atat.models.portfolio_state_machine import FSMStates
from atat.models.mixins.state_machines import (
    AzureStages,
    StageStates,
    _build_csp_states,
    _build_transitions,
    compose_state,
)


class AzureStagesTest(Enum):
    TENANT = "tenant"


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
def test_compose_state():
    assert (
        compose_state(AzureStages.TENANT, StageStates.CREATED)
        == FSMStates.TENANT_CREATED
    )
