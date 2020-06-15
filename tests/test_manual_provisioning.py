from script.provision.provision_base import get_provider_and_inputs, update_and_write
from script.provision import (
    a_create_tenant,
    b_setup_billing,
    c_billing_profile_tenant_access,
    d_setup_to_billing,
    e_report_clin,
    f_purchase_aadp,
)
import json
import pytest


class TestManualProvisioning:
    def _helper(self, prov_func, input_path, output_path):
        csp, inputs = get_provider_and_inputs(input_path, "mock-test")
        result = prov_func(csp, inputs)
        update_and_write(inputs, result, output_path, verbose=False)
        with open(output_path) as json_file:
            assert json.load(json_file)

    @pytest.fixture(scope="session")
    def output_dir(self, tmp_path_factory):
        return tmp_path_factory.getbasetemp()

    def test_create_tenant(self, output_dir):
        self._helper(
            a_create_tenant.create_tenant,
            "script/provision/sample.json",
            output_dir / "create_tenant.json",
        )

    def test_setup_billing(self, output_dir):
        self._helper(
            b_setup_billing.setup_billing,
            output_dir / "create_tenant.json",
            output_dir / "setup_billing.json",
        )

    def test_grant_access(self, output_dir):
        self._helper(
            c_billing_profile_tenant_access.grant_access,
            output_dir / "setup_billing.json",
            output_dir / "grant_access.json",
        )

    def test_setup_to_billing(self, output_dir):
        self._helper(
            d_setup_to_billing.setup_to_billing,
            output_dir / "grant_access.json",
            output_dir / "setup_to_billing.json",
        )

    def test_report_clin(self, output_dir):
        self._helper(
            e_report_clin.report_clin,
            output_dir / "setup_to_billing.json",
            output_dir / "report_clin.json",
        )

    def test_purchase_aadp(self, output_dir):
        self._helper(
            f_purchase_aadp.purchase_aadp,
            output_dir / "report_clin.json",
            output_dir / "purchase_aadp.json",
        )
