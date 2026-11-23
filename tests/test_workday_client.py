
from unittest.mock import Mock

import pytest
import requests

from integration.workday_client import WorkdayClient


def test_workday_client_sends_get_request(monkeypatch):
    monkeypatch.setenv(
        "WORKDAY_BASE_URL",
        "https://example.workday.com"
    )

    client = WorkdayClient(access_token="test-token")

    mock_response = Mock()
    mock_response.json.return_value = {
        "data": [{"employee_id": "TEST001"}]
    }

    client.session.get = Mock(return_value=mock_response)

    result = client.get(
        "/workers",
        params={"limit": 10}
    )

    client.session.get.assert_called_once_with(
        "https://example.workday.com/workers",
        params={"limit": 10},
        timeout=30
    )

    assert result["data"][0]["employee_id"] == "TEST001"


def test_workday_client_raises_http_error(monkeypatch):
    monkeypatch.setenv(
        "WORKDAY_BASE_URL",
        "https://example.workday.com"
    )

    client = WorkdayClient(access_token="test-token")

    mock_response = Mock()
    mock_response.raise_for_status.side_effect = (
        requests.exceptions.HTTPError("Unauthorized")
    )

    client.session.get = Mock(return_value=mock_response)

    with pytest.raises(requests.exceptions.HTTPError):
        client.get("/workers")

def test_workday_client_rejects_empty_token(monkeypatch):
    monkeypatch.setenv(
        "WORKDAY_BASE_URL",
        "https://example.workday.com"
    )

    with pytest.raises(ValueError, match="access token is required"):
        WorkdayClient(access_token="")
        
def test_workday_client_sets_bearer_token_header(monkeypatch):
    monkeypatch.setenv(
        "WORKDAY_BASE_URL",
        "https://example.workday.com"
    )

    client = WorkdayClient(access_token="sample-test-token")

    assert (
        client.session.headers["Authorization"]
        == "Bearer sample-test-token"
    )

    assert (
        client.session.headers["Accept"]
        == "application/json"
    )