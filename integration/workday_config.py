
import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")


def get_workday_base_url():
    base_url = os.getenv("WORKDAY_BASE_URL", "").strip()

    if not base_url:
        raise RuntimeError(
            "WORKDAY_BASE_URL is missing from the root .env file"
        )

    if not base_url.startswith("https://"):
        raise ValueError("Workday base URL must use HTTPS")

    return base_url.rstrip("/")
