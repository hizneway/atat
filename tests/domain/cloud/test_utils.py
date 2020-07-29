from unittest.mock import MagicMock, patch

import pytest
import requests

from atat.domain.csp.cloud.utils import get_principal_auth_token
from tests.domain.cloud.test_azure_csp import mock_requests_response
from tests.mock_azure import mock_requests


@patch("atat.domain.csp.cloud.utils.requests", new_callable=mock_requests)
def test_get_principal_auth_token(mock_requests):
    mock_requests.post.side_effect = [
        mock_requests_response(
            status=500,
            raise_for_status=requests.exceptions.HTTPError("500 Server Error"),
        ),
        mock_requests_response(json_data={"access_token": "token"}),
        mock_requests_response(json_data={}),
    ]
    payload = MagicMock(return_value={})

    with pytest.raises(requests.HTTPError):
        get_principal_auth_token("a_tenant_id", payload)

    assert get_principal_auth_token("a_tenant_id", payload) == "token"
    assert get_principal_auth_token("a_tenant_id", payload) is None
