from flask import render_template, g, Response
from flask import current_app as app

from . import requests_bp
from atst.domain.requests import Requests
from atst.domain.exceptions import NotFoundError


def task_order_dictionary(task_order):
    return {
        c.name: getattr(task_order, c.name)
        for c in task_order.__table__.columns
        if c.name not in ["id", "attachment_id"]
    }


@requests_bp.route("/requests/approval/<string:request_id>", methods=["GET"])
def approval(request_id):
    request = Requests.get(g.current_user, request_id)
    data = request.body
    if request.task_order:
        data["task_order"] = task_order_dictionary(request.task_order)

    return render_template("requests/approval.html", data=data, request_id=request.id, financial_review=True)


@requests_bp.route("/requests/task_order_download/<string:request_id>", methods=["GET"])
def task_order_pdf_download(request_id):
    request = Requests.get(g.current_user, request_id)
    if request.task_order and request.task_order.pdf:
        object_name = request.task_order.pdf.object_name
        generator = app.uploader.download_stream(object_name)
        return Response(generator, mimetype="application/pdf")
    else:
        raise NotFoundError("task_order pdf")
