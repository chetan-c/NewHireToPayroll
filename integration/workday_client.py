
import requests

from integration.workday_config import get_workday_base_url


class WorkdayClient:
    """Client for authorized Workday REST API requests."""

    def __init__(self, access_token):
        self.base_url = get_workday_base_url()
        if not access_token or not access_token.strip():
            raise ValueError("Workday access token is required")

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        })

    def get(self, endpoint, params=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        response = self.session.get(
            url,
            params=params,
            timeout=30
        )

        response.raise_for_status()
        return response.json()
