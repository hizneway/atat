import os
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(parent_dir)

from atat.domain.csp.cloud.models import (
    ProductPurchaseCSPPayload,
    ProductPurchaseVerificationCSPPayload,
)
from script.provision.provision_base import handle


def poll_purchase(csp, inputs, csp_response):
    if csp_response.get("product_purchase_verify_url") is not None:
        purchase_premium = ProductPurchaseVerificationCSPPayload(
            **{**inputs.get("initial_inputs"), **inputs.get("csp_data"), **csp_response}
        )
        return csp.create_product_purchase_verification(purchase_premium)
    else:
        return csp_response


def purchase_aadp(csp, inputs):
    purchase_premium = ProductPurchaseCSPPayload(
        **{**inputs.get("initial_inputs"), **inputs.get("csp_data")}
    )

    result = csp.create_product_purchase(purchase_premium)
    poll_result = poll_purchase(csp, inputs, result.dict())
    return poll_result.dict()


if __name__ == "__main__":
    handle(purchase_aadp)
