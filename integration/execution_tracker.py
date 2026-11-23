
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing from .env")


def start_execution(execution_id):
    """Create a record when an integration execution begins."""

    with psycopg.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO integration_executions (
                    execution_id,
                    integration_name,
                    final_status,
                    message
                )
                VALUES (%s, %s, %s, %s);
                """,
                (
                    execution_id,
                    "NewHireToPayroll",
                    "RUNNING",
                    "Integration execution started"
                )
            )


def finish_execution(
    execution_id,
    final_status,
    total_records,
    success_count,
    failure_count,
    duplicate_count,
    retry_count,
    message
):
    """Update the execution record when processing finishes."""

    allowed_statuses = [
        "SUCCESS",
        "PARTIAL_SUCCESS",
        "FAILED"
    ]

    if final_status not in allowed_statuses:
        raise ValueError("Invalid final execution status")

    with psycopg.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE integration_executions
                SET
                    end_time = CURRENT_TIMESTAMP,
                    final_status = %s,
                    total_records = %s,
                    success_count = %s,
                    failure_count = %s,
                    duplicate_count = %s,
                    retry_count = %s,
                    message = %s
                WHERE execution_id = %s;
                """,
                (
                    final_status,
                    total_records,
                    success_count,
                    failure_count,
                    duplicate_count,
                    retry_count,
                    message,
                    execution_id
                )
            )

            if cursor.rowcount == 0:
                raise ValueError(
                    f"Execution ID not found: {execution_id}"
                )
