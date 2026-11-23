
import pytest

from integration.workday_config import get_workday_base_url


def test_missing_workday_url(monkeypatch):
    monkeypatch.delenv("WORKDAY_BASE_URL", raising=False)

    with pytest.raises(RuntimeError):
        get_workday_base_url()


def test_reject_http_url(monkeypatch):
    monkeypatch.setenv(
        "WORKDAY_BASE_URL",
        "http://example.workday.com"
    )

    with pytest.raises(ValueError):
        get_workday_base_url()


def test_accept_https_url(monkeypatch):
    monkeypatch.setenv(
        "WORKDAY_BASE_URL",
        "https://example.workday.com"
    )

    assert get_workday_base_url() == "https://example.workday.com"
