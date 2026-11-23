
from unittest.mock import Mock

import pytest

from integration.workday_client import WorkdayClient


def test_get_all_workers_handles_multiple_pages(monkeypatch):
    monkeypatch.setenv(
        "WORKDAY_BASE_URL",
        "http://127.0.0.1:8001"
    )

    client = WorkdayClient(access_token="test-token")

    client.get = Mock(side_effect=[
        {
            "data": [
                {"employeeId": "100245"},
                {"employeeId": "100246"}
            ],
            "has_more": True
        },
        {
            "data": [
                {"employeeId": "100247"}
            ],
            "has_more": False
        }
    ])

    workers = client.get_all_workers(page_size=2)

    assert len(workers) == 3
    assert workers[0]["employeeId"] == "100245"
    assert workers[2]["employeeId"] == "100247"

    assert client.get.call_count == 2


def test_get_all_workers_rejects_invalid_page_size(monkeypatch):
    monkeypatch.setenv(
        "WORKDAY_BASE_URL",
        "http://127.0.0.1:8001"
    )

    client = WorkdayClient(access_token="test-token")

    with pytest.raises(ValueError):
        client.get_all_workers(page_size=0)
