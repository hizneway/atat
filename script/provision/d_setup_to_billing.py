import os
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(parent_dir)

from atat.domain.csp.cloud.models import (
    TaskOrderBillingCreationCSPPayload,
    TaskOrderBillingVerificationCSPPayload,
)
from script.provision.provision_base import handle
import time


def poll_billing(csp, inputs, csp_response):
    if csp_response.get("task_order_billing_verify_url") is not None:
        retries = 3
        for _ in range(retries):
            enable_to_billing = TaskOrderBillingVerificationCSPPayload(
                **{
                    **inputs.get("initial_inputs"),
                    **inputs.get("csp_data"),
                    **csp_response,
                }
            )
            response = csp.create_task_order_billing_verification(enable_to_billing)
            if response.reset_stage:
                time.sleep(10)
            else:
                return response
    else:
        return csp_response


def setup_to_billing(csp, inputs):
    enable_to_billing = TaskOrderBillingCreationCSPPayload(
        **{**inputs.get("initial_inputs"), **inputs.get("csp_data")}
    )
    result = csp.create_task_order_billing_creation(enable_to_billing)
    poll_result = poll_billing(csp, inputs, result.dict())
    return poll_result.dict()


if __name__ == "__main__":
    handle(setup_to_billing)
