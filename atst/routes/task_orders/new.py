from flask import g, redirect, render_template, request as http_request, url_for

from . import task_orders_bp
from atst.domain.authz.decorator import user_can_access_decorator as user_can
from atst.domain.task_orders import TaskOrders
from atst.forms.task_order import TaskOrderForm
from atst.models.permissions import Permissions
from atst.utils.flash import formatted_flash as flash


@task_orders_bp.route("/portfolios/<portfolio_id>/task_orders/new")
@task_orders_bp.route("/portfolios/<portfolio_id>/task_orders/<task_order_id>/edit")
@user_can(Permissions.CREATE_TASK_ORDER, message="view new task order form")
def edit(portfolio_id, task_order_id=None):
    form = None

    if task_order_id:
        task_order = TaskOrders.get(task_order_id)
        form = TaskOrderForm(number=task_order.number)
    else:
        form = TaskOrderForm()

    cancel_url = (
        http_request.referrer
        if http_request.referrer
        else url_for("task_orders.portfolio_funding", portfolio_id=portfolio_id)
    )

    return render_template("task_orders/edit.html", form=form, cancel_url=cancel_url)


@task_orders_bp.route("/portfolios/<portfolio_id>/task_orders/new", methods=["POST"])
@task_orders_bp.route(
    "/portfolios/<portfolio_id>/task_orders/<task_order_id>", methods=["POST"]
)
@user_can(Permissions.CREATE_TASK_ORDER, message="create new task order")
def update(portfolio_id, task_order_id=None):
    form_data = http_request.form
    form = TaskOrderForm(form_data)

    if form.validate():
        task_order = None
        if task_order_id:
            task_order = TaskOrders.update(task_order_id, **form.data)
        else:
            task_order = TaskOrders.create(g.current_user, portfolio_id, **form.data)

        flash("task_order_draft")

        return redirect(
            url_for(
                "task_orders.edit",
                portfolio_id=portfolio_id,
                task_order_id=task_order.id,
            )
        )
    else:
        flash("form_errors")
        return render_template("task_orders/edit.html", form=form)
