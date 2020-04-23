from enum import Enum

import pytest
from pytest import raises

from atat.models.mixins.state_machines import (
    AzureStages,
    StageStates,
    PortfolioStates,
    StateMachineMisconfiguredError,
    _build_csp_states,
    _build_transitions,
    compose_state,
)
from tests.factories import PortfolioFactory


class AzureStagesTest(Enum):
    TENANT = "tenant"
    POLICIES = "policies"


def test_find_and_call_stage_trigger():
    portfolio = PortfolioFactory.create(state="TENANT_IN_PROGRESS")
    portfolio.state_machine._find_and_call_stage_trigger("fail_")
    assert portfolio.state_machine.state == PortfolioStates.TENANT_FAILED


def test_find_and_call_stage_trigger_fails():
    portfolio = PortfolioFactory.create(state="UNSTARTED")
    with raises(StateMachineMisconfiguredError):
        portfolio.state_machine._find_and_call_stage_trigger(
            "wont_find_a_trigger_with_this_prefix"
        )
    assert portfolio.state_machine.state == PortfolioStates.CONFIGURATION_ERROR


@pytest.mark.state_machine
def test_build_transitions():
    states, transitions = _build_transitions(AzureStagesTest)
    assert [s.get("name").name for s in states] == [
        "TENANT_CREATED",
        "TENANT_IN_PROGRESS",
        "TENANT_FAILED",
        "POLICIES_CREATED",
        "POLICIES_IN_PROGRESS",
        "POLICIES_FAILED",
    ]
    assert [s.get("tags") for s in states] == [
        ["TENANT", "CREATED"],
        ["TENANT", "IN_PROGRESS"],
        ["TENANT", "FAILED"],
        ["POLICIES", "CREATED"],
        ["POLICIES", "IN_PROGRESS"],
        ["POLICIES", "FAILED"],
    ]
    assert [t.get("trigger") for t in transitions] == [
        "create_tenant",
        "finish_tenant",
        "fail_tenant",
        "resume_progress_tenant",
        "create_policies",
        "finish_policies",
        "fail_policies",
        "resume_progress_policies",
        "complete",
    ]

    created_to_in_progress_trigger = next(
        (t for t in transitions if t.get("trigger") == "create_policies")
    )
    assert created_to_in_progress_trigger["source"] == PortfolioStates.TENANT_CREATED
    assert (
        created_to_in_progress_trigger["dest"] == PortfolioStates.POLICIES_IN_PROGRESS
    )


@pytest.mark.state_machine
def test_build_csp_states():
    states = _build_csp_states(AzureStagesTest)
    assert list(states) == [
        "UNSTARTED",
        "COMPLETED",
        "CONFIGURATION_ERROR",
        "TENANT_CREATED",
        "TENANT_IN_PROGRESS",
        "TENANT_FAILED",
        "POLICIES_CREATED",
        "POLICIES_IN_PROGRESS",
        "POLICIES_FAILED",
    ]


@pytest.mark.state_machine
def test_compose_state():
    assert (
        compose_state(AzureStages.TENANT, StageStates.CREATED)
        == PortfolioStates.TENANT_CREATED
    )
