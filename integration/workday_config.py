import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def get_workday_base_url():
    base_url = os.getenv("WORKDAY_BASE_URL", "").strip()

    if not base_url:
        raise RuntimeError(
            "WORKDAY_BASE_URL is missing from the root .env file"
        )

    parsed_url = urlparse(base_url)

    is_local = parsed_url.hostname in ("localhost", "127.0.0.1")

    if parsed_url.scheme != "https" and not (
        parsed_url.scheme == "http" and is_local
    ):
        raise ValueError(
            "Use HTTPS, except for local development on localhost"
        )

    if not parsed_url.hostname:
        raise ValueError("Invalid Workday base URL")

    return base_url.rstrip("/")
