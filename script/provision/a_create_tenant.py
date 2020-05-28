import os
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(parent_dir)

from script.provision.provision_base import handle

from atat.domain.csp.cloud.models import TenantCSPPayload


def create_tenant(csp, inputs):
    create_tenant_payload = TenantCSPPayload(
        **{**inputs.get("initial_inputs"), **inputs.get("csp_data")}
    )
    result = csp.create_tenant(create_tenant_payload)
    return dict(result)


if __name__ == "__main__":
    handle(create_tenant)
