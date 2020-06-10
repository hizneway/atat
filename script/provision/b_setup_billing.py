import os
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(parent_dir)

from atat.domain.csp.cloud.models import (
    BillingProfileCreationCSPPayload,
    BillingProfileVerificationCSPPayload,
)
from script.provision.provision_base import handle
from atat.domain.csp.cloud.exceptions import GeneralCSPException
import time


def poll_billing(csp, inputs, csp_response):
    if csp_response.get("billing_profile_verify_url") is not None:
        get_billing_profile = BillingProfileVerificationCSPPayload(
            **{**inputs.get("initial_inputs"), **inputs.get("csp_data"), **csp_response}
        )
        try:
            return csp.create_billing_profile_verification(get_billing_profile)
        except GeneralCSPException:
            time.sleep(10)
            return poll_billing(csp, inputs, csp_response)
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
