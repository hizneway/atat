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


class TestManualProvisioning:
    init_input_file = "script/provision/sample.json"

    def _helper(self, prov_func, input_path, output_path):
        csp, inputs = get_provider_and_inputs(input_path, "mock-test")
        result = prov_func(csp, inputs)
        update_and_write(inputs, result, output_path, verbose=False)
        with open(output_path) as json_file:
            assert json.load(json_file)

    def test_create_tenant(self, tmp_path_factory):
        tmp_path = tmp_path_factory.getbasetemp()
        self._helper(
            a_create_tenant.create_tenant,
            self.init_input_file,
            tmp_path / "create_tenant.json",
        )

    def test_setup_billing(self, tmp_path_factory):
        tmp_path = tmp_path_factory.getbasetemp()
        self._helper(
            b_setup_billing.setup_billing,
            tmp_path / "create_tenant.json",
            tmp_path / "setup_billing.json",
        )

    def test_grant_access(self, tmp_path_factory):
        tmp_path = tmp_path_factory.getbasetemp()
        self._helper(
            c_billing_profile_tenant_access.grant_access,
            tmp_path / "setup_billing.json",
            tmp_path / "grant_access.json",
        )

    def test_setup_to_billing(self, tmp_path_factory):
        tmp_path = tmp_path_factory.getbasetemp()
        self._helper(
            d_setup_to_billing.setup_to_billing,
            tmp_path / "grant_access.json",
            tmp_path / "setup_to_billing.json",
        )

    def test_report_clin(self, tmp_path_factory):
        tmp_path = tmp_path_factory.getbasetemp()
        self._helper(
            e_report_clin.report_clin,
            tmp_path / "setup_to_billing.json",
            tmp_path / "report_clin.json",
        )

    def test_purchase_aadp(self, tmp_path_factory):
        tmp_path = tmp_path_factory.getbasetemp()
        self._helper(
            f_purchase_aadp.purchase_aadp,
            tmp_path / "report_clin.json",
            tmp_path / "purchase_aadp.json",
        )
