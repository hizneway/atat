import os
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(parent_dir)


from atst.domain.csp.cloud.models import BillingInstructionCSPPayload
from script.provision.provision_base import handle


def report_clin(csp, inputs):
    billing_instruction = BillingInstructionCSPPayload(
        **{**inputs.get("initial_inputs"), **inputs.get("csp_data")}
    )
    result = csp.create_billing_instruction(billing_instruction)
    if result.get("status") == "ok":
        return result.get("body").dict()
    else:
        print("there was an error during the request:")
        print(result.get("body"))


if __name__ == "__main__":
    handle(report_clin)
