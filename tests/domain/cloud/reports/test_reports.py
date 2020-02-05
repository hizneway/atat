from atst.domain.csp.reports import MockReportingProvider, prepare_azure_reporting_data
from tests.factories import PortfolioFactory
from decimal import Decimal
import pendulum


def test_get_environment_monthly_totals():
    environment = {
        "name": "Test Environment",
        "spending": {
            "this_month": {"JEDI_CLIN_1": 100, "JEDI_CLIN_2": 100},
            "last_month": {"JEDI_CLIN_1": 200, "JEDI_CLIN_2": 200},
            "total": {"JEDI_CLIN_1": 1000, "JEDI_CLIN_2": 1000},
        },
    }
    totals = MockReportingProvider._get_environment_monthly_totals(environment)
    assert totals == {
        "name": "Test Environment",
        "this_month": 200,
        "last_month": 400,
        "total": 2000,
    }


def test_get_application_monthly_totals():
    portfolio = PortfolioFactory.create(
        applications=[
            {"name": "Test Application", "environments": [{"name": "Z"}, {"name": "A"}]}
        ],
    )
    application = {
        "name": "Test Application",
        "environments": [
            {
                "name": "Z",
                "spending": {
                    "this_month": {"JEDI_CLIN_1": 50, "JEDI_CLIN_2": 50},
                    "last_month": {"JEDI_CLIN_1": 150, "JEDI_CLIN_2": 150},
                    "total": {"JEDI_CLIN_1": 250, "JEDI_CLIN_2": 250},
                },
            },
            {
                "name": "A",
                "spending": {
                    "this_month": {"JEDI_CLIN_1": 100, "JEDI_CLIN_2": 100},
                    "last_month": {"JEDI_CLIN_1": 200, "JEDI_CLIN_2": 200},
                    "total": {"JEDI_CLIN_1": 1000, "JEDI_CLIN_2": 1000},
                },
            },
        ],
    }

    totals = MockReportingProvider._get_application_monthly_totals(
        portfolio, application
    )
    assert totals["name"] == "Test Application"
    assert totals["this_month"] == 300
    assert totals["last_month"] == 700
    assert totals["total"] == 2500
    assert [env["name"] for env in totals["environments"]] == ["A", "Z"]


class TestPrepareAzureData:
    start_of_month = pendulum.today(tz="utc").start_of("month").replace(tzinfo=None)
    next_month = start_of_month.add(months=1).to_atom_string()
    this_month = start_of_month.to_atom_string()
    last_month = start_of_month.subtract(months=1).to_atom_string()
    two_months_ago = last_month = start_of_month.subtract(months=2).to_atom_string()

    def test_estimated_and_invoiced(self):
        rows = [
            [150.0, self.two_months_ago, "", "USD"],
            [100.0, self.last_month, "e0500a4qhw", "USD"],
            [50.0, self.this_month, "", "USD"],
            [50.0, self.next_month, "", "USD"],
        ]
        output = prepare_azure_reporting_data(rows)

        assert output.get("invoiced") == Decimal(250.0)
        assert output.get("estimated") == Decimal(100.0)

    def test_just_estimated(self):
        rows = [
            [100.0, self.this_month, "", "USD"],
        ]
        output = prepare_azure_reporting_data(rows)

        assert output.get("invoiced") == Decimal(0.0)
        assert output.get("estimated") == Decimal(100.0)

    def test_just_invoiced(self):
        rows = [
            [100.0, self.last_month, "", "USD"],
        ]
        output = prepare_azure_reporting_data(rows)

        assert output.get("invoiced") == Decimal(100.0)
        assert output.get("estimated") == Decimal(0.0)

    def test_no_rows(self):
        output = prepare_azure_reporting_data([])
        assert output.get("invoiced") == Decimal(0.0)
        assert output.get("estimated") == Decimal(0.0)
