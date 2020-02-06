from flask import current_app
from itertools import groupby
from atst.domain.csp.cloud.models import (
    ReportingCSPPayload,
    CostManagementQueryCSPResult,
)
from atst.domain.csp.reports import prepare_azure_reporting_data
import pendulum


class Reports:
    @classmethod
    def monthly_spending(cls, portfolio):
        return current_app.csp.reports.get_portfolio_monthly_spending(portfolio)

    @classmethod
    def expired_task_orders(cls, portfolio):
        return [
            task_order for task_order in portfolio.task_orders if task_order.is_expired
        ]

    @classmethod
    def obligated_funds_by_JEDI_clin(cls, portfolio):
        clin_spending = current_app.csp.reports.get_spending_by_JEDI_clin(portfolio)
        active_clins = portfolio.active_clins
        for jedi_clin, clins in groupby(
            active_clins, key=lambda clin: clin.jedi_clin_type
        ):
            if not clin_spending.get(jedi_clin.name):
                clin_spending[jedi_clin.name] = {}
            clin_spending[jedi_clin.name]["obligated"] = sum(
                clin.obligated_amount for clin in clins
            )

        output = []
        for clin in clin_spending.keys():
            invoiced = clin_spending[clin].get("invoiced", 0)
            estimated = clin_spending[clin].get("estimated", 0)
            obligated = clin_spending[clin].get("obligated", 0)
            remaining = obligated - (invoiced + estimated)
            output.append(
                {
                    "name": clin,
                    "invoiced": invoiced,
                    "estimated": estimated,
                    "obligated": obligated,
                    "remaining": remaining,
                }
            )
        return output

    @classmethod
    def get_portfolio_spending(cls, portfolio):
        # TODO: Extend this function to make from_date and to_date configurable
        from_date = pendulum.now().subtract(years=1).add(days=1).format("YYYY-MM-DD")
        to_date = pendulum.now().format("YYYY-MM-DD")
        rows = []

        if portfolio.csp_data:
            payload = ReportingCSPPayload(
                from_date=from_date, to_date=to_date, **portfolio.csp_data
            )
            response: CostManagementQueryCSPResult = current_app.csp.cloud.get_reporting_data(
                payload
            )
            rows = response.properties.rows

        return prepare_azure_reporting_data(rows)
