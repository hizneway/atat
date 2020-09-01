import os
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(parent_dir)

from atat.domain.csp.cloud.models import (
    TaskOrderBillingCreationCSPPayload,
    TaskOrderBillingVerificationCSPPayload,
)
from script.provision.provision_base import handle


def poll_billing(csp, inputs, csp_response):
    """Polls billing endpoint for async response three times.  If verify url is not 
    available, the csp_response payload will be returned. 

    Args:
        csp: CSP Class object
        inputs: Json string
        csp_response: Result from billing profile creation

    Returns:
        Response from billing verification or csp_response payload
    """
    verify_url = csp_response.get("task_order_billing_verify_url")
    csp_method = csp.create_task_order_billing_verification
    payload = TaskOrderBillingVerificationCSPPayload(
        **{**inputs.get("initial_inputs"), **inputs.get("csp_data"), **csp_response,}
    )
    return verify_async(verify_url, csp_method, payload, csp_response)


def setup_to_billing(csp, inputs):
    enable_to_billing = TaskOrderBillingCreationCSPPayload(
        **{**inputs.get("initial_inputs"), **inputs.get("csp_data")}
    )
    result = csp.create_task_order_billing_creation(enable_to_billing)
    poll_result = poll_billing(csp, inputs, result.dict())
    return poll_result.dict()


if __name__ == "__main__":
    handle(setup_to_billing)
