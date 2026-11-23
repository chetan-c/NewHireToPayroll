
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


# Load project configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing from .env")


def record_audit(
    worker_code,
    status,
    message,
    retry_count=0,
    execution_id=None
):
    """
    Save integration execution details in PostgreSQL.
    """

    with psycopg.connect(DATABASE_URL) as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO integration_logs (
                    worker_code,
                    integration_name,
                    status,
                    message,
                    retry_count,
                    execution_id
                )
                VALUES (%s, %s, %s, %s, %s, %s);
                """,
                (
                    worker_code,
                    "NewHireToPayroll",
                    status,
                    message,
                    retry_count,
                    execution_id
                )
            )
