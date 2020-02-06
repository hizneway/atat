import json
import os
import pprint
import sys

from atst.domain.csp.cloud import AzureCloudProvider
from atst.domain.csp.cloud.models import KeyVaultCredentials

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(parent_dir)


def get_provider_and_inputs(input_path):
    with open(input_path, "r") as input_file:
        details = json.loads(input_file.read())
        creds = details.get("creds")
        config = details.get("config")

        cloud = AzureCloudProvider(config)

        def fake_source_creds(tenant_id=None):
            return KeyVaultCredentials(**creds)

        cloud._source_creds = fake_source_creds

        return (cloud, details)


def update_and_write(inputs, result, output_path):
    inputs["csp_data"].update(result)
    print(f"Updated inputs {pprint.pformat(inputs, indent=2)}")
    with open(output_path, "w") as output_file:
        print(f"writing to {output_path}")
        output_file.write(json.dumps(inputs, indent=4))


def handle(f):
    input_path = sys.argv[1]
    output_path = sys.argv[2]

    (provider, inputs) = get_provider_and_inputs(input_path)
    try:
        result = f(provider, inputs)
        if result:
            print("Writing ")
            update_and_write(inputs, result, output_path)
        else:
            print("no result")
    except Exception as exc:
        print("Failed to create tenant")
        print(f"Inputs: {inputs}")
        print("Exception:")
        print(exc)
