
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

    def get_all_workers(self, page_size=2):
        if isinstance(page_size, bool) or not isinstance(page_size, int):
            raise ValueError("Page size must be a positive integer")

        if page_size <= 0:
            raise ValueError("Page size must be a positive integer")

        all_workers = []
        offset = 0

        while True:
            result = self.get(
                "/workers",
                params={
                    "limit": page_size,
                    "offset": offset
                }
            )

            workers = result.get("data")

            if not isinstance(workers, list):
                raise ValueError("Invalid worker response")

            all_workers.extend(workers)

            if not result.get("has_more", False):
                break

            if not workers:
                raise ValueError("Pagination returned no records but has_more is true")

            offset += len(workers)

        return all_workers
