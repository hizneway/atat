import os
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(parent_dir)

from script.provision.provision_base import handle

from atst.domain.csp.cloud.models import TenantCSPPayload


def create_tenant(csp, inputs):
    create_tenant_payload = TenantCSPPayload(
        **{**inputs.get("initial_inputs"), **inputs.get("csp_data")}
    )

    csp.update_tenant_creds = lambda a, b: None
    result = csp.create_tenant(create_tenant_payload)
    if result.get("status") == "ok":
        return result.get("body").dict()
    else:
        print("there was an error during the request:")
        print(result.get("body"))


if __name__ == "__main__":
    handle(create_tenant)

