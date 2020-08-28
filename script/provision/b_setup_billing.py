import os
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(parent_dir)

from atat.domain.csp.cloud.models import (
    BillingProfileCreationCSPPayload,
    BillingProfileVerificationCSPPayload,
)
from script.provision.provision_base import handle
import time


def poll_billing(csp, inputs, csp_response):
    """Polls billing endpoint for async response three times.  If verify url is not 
    available, the csp_response payload will be returned. 

    Args:
        csp: CSP Class object
        inputs: Json string
        csp_response: Result from billing profile creation

    Returns:
        Response from billing profile verification or csp_response payload
    """
    if csp_response.get("billing_profile_verify_url") is not None:
        retries = 3
        for _ in range(retries):
            get_billing_profile = BillingProfileVerificationCSPPayload(
                **{
                    **inputs.get("initial_inputs"),
                    **inputs.get("csp_data"),
                    **csp_response,
                }
            )
            response = csp.create_billing_profile_verification(get_billing_profile)
            if response.reset_stage:
                time.sleep(10)
            else:
                return response
    else:
        return csp_response


def setup_billing(csp, inputs):
    create_billing_profile = BillingProfileCreationCSPPayload(
        **{**inputs.get("initial_inputs"), **inputs.get("csp_data")}
    )

    result = csp.create_billing_profile_creation(create_billing_profile)
    polling_result = poll_billing(csp, inputs, result.dict())
    return polling_result.dict()


if __name__ == "__main__":
    handle(setup_billing)
