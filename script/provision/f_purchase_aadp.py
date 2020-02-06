import os
import sys

from atst.domain.csp.cloud.models import (
    ProductPurchaseCSPPayload,
    ProductPurchaseVerificationCSPPayload,
)
from script.provision.provision_base import handle

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(parent_dir)


def poll_purchase(csp, inputs, csp_response):
    if csp_response.get("product_purchase_verify_url") is not None:
        time.sleep(csp_response.get("product_purchase_retry_after"))
        purchase_premium = ProductPurchaseVerificationCSPPayload(
            **{**inputs.get("initial_inputs"), **inputs.get("csp_data"), **csp_response}
        )
        result = csp.create_product_purchase_verification(purchase_premium)
        if result.get("status") == "ok":
            csp_response = result.get("body").dict()
            poll_purchase(csp, inputs, csp_response)
        else:
            return result.get("body").dict()
    else:
        return csp_response


def purchase_aadp(csp, inputs):
    purchase_premium = ProductPurchaseCSPPayload(
        **{**inputs.get("initial_inputs"), **inputs.get("csp_data")}
    )

    result = csp.create_product_purchase_creation(purchase_premium)
    if result.get("status") == "ok":
        csp_response = result.get("body").dict()
        poll_purchase(csp, inputs, csp_response)
    else:
        print("there was an error during the request:")
        print(result.get("body"))


if __name__ == "__main__":
    handle(purchase_aadp)
