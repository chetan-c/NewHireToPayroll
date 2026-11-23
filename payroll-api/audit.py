
from database import get_connection


def save_integration_log(
    worker_code,
    status,
    message,
    retry_count=0
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO integration_logs (
                    worker_code,
                    integration_name,
                    status,
                    message,
                    retry_count
                )
                VALUES (%s, %s, %s, %s, %s);
                """,
                (
                    worker_code,
                    "NewHireToPayroll",
                    status,
                    message,
                    retry_count
                )
            )
