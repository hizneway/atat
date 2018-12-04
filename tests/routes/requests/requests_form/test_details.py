import re
from flask import url_for

from atst.models.request_status_event import RequestStatus

from tests.factories import RequestFactory, TaskOrderFactory, UserFactory


def test_can_show_financial_data(client, user_session):
    user = UserFactory.create()
    user_session(user)

    task_order = TaskOrderFactory.create()
    request = RequestFactory.create_with_status(
        status=RequestStatus.PENDING_CCPO_APPROVAL, task_order=task_order, creator=user
    )
    response = client.get(
        url_for("requests.view_request_details", request_id=request.id)
    )

    body = response.data.decode()
    assert re.search(r">\s+Financial Verification\s+<", body)


def test_can_not_show_financial_data(client, user_session):
    user = UserFactory.create()
    user_session(user)

    request = RequestFactory.create_with_status(
        status=RequestStatus.PENDING_CCPO_ACCEPTANCE, creator=user
    )
    response = client.get(
        url_for("requests.view_request_details", request_id=request.id)
    )

    body = response.data.decode()
    assert not re.search(r">\s+Financial Verification\s+<", body)