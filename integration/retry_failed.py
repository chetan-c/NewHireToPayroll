
import json
import os
import uuid
from pathlib import Path

import psycopg
from dotenv import load_dotenv

import send_employee as integration


# --------------------------------------------------
# 1. LOAD DATABASE CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing from .env")


# --------------------------------------------------
# 2. FIND EMPLOYEES WHOSE LATEST RESULT IS FAILED
# --------------------------------------------------


def get_failed_worker_codes():

    query = """
        SELECT worker_code
        FROM (
            SELECT DISTINCT ON (worker_code)
                worker_code,
                status
            FROM integration_logs
            ORDER BY worker_code, processed_at DESC, id DESC
        ) AS latest_results
        WHERE status = 'FAILED'
          AND worker_code IS NOT NULL
          AND BTRIM(worker_code) <> '';
    """

    with psycopg.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

    return {row[0] for row in rows}



# --------------------------------------------------
# 3. LOAD ORIGINAL EMPLOYEE DATA
# --------------------------------------------------

def load_failed_employees(failed_worker_codes):

    with open(
        integration.SOURCE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        employees = json.load(file)

    if not isinstance(employees, list):
        raise ValueError("Employee source must contain a JSON array")

    failed_employees = [
        employee
        for employee in employees
        if isinstance(employee, dict)
        and employee.get("employeeId") in failed_worker_codes
    ]

    return failed_employees


def get_existing_worker_codes(worker_codes):

    if not worker_codes:
        return set()

    query = """
        SELECT worker_code
        FROM employees
        WHERE worker_code = ANY(%s);
    """

    with psycopg.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (list(worker_codes),))
            rows = cursor.fetchall()

    return {row[0] for row in rows}


# --------------------------------------------------
# 4. RECOVERY EXECUTION
# --------------------------------------------------

def main():

    retry_execution_id = str(uuid.uuid4())

    print("========================================")
    print("FAILED EMPLOYEE RECOVERY STARTED")
    print("Recovery Execution ID:", retry_execution_id)
    print("========================================")

    failed_worker_codes = get_failed_worker_codes()

    if not failed_worker_codes:

        print("No failed employees found. Nothing to recover.")
        return

    failed_employees = load_failed_employees(
        failed_worker_codes
    )

    if not failed_employees:

        print(
            "Failed employee IDs were found, but no matching "
            "records exist in the source JSON file."
        )
        return

    # Give this recovery run its own execution ID.
    integration.EXECUTION_ID = retry_execution_id

    # Reset counters for this recovery execution.
    integration.TOTAL_RECORDS = len(failed_employees)
    integration.SUCCESS_COUNT = 0
    integration.FAILURE_COUNT = 0
    integration.DUPLICATE_COUNT = 0
    integration.RETRY_COUNT = 0

    integration.start_execution(retry_execution_id)

    final_status = "FAILED"
    message = "Recovery execution did not complete"

    try:

        for index, employee in enumerate(
            failed_employees,
            start=1
        ):

            
        # Check which employees already exist in payroll.
         worker_codes = {
            employee["employeeId"]
            for employee in failed_employees
            if employee.get("employeeId")
        }

        existing_worker_codes = get_existing_worker_codes(
            worker_codes
        )

        for index, employee in enumerate(
            failed_employees,
            start=1
        ):

            worker_code = employee.get("employeeId", "UNKNOWN")

            print(
                f"Recovery progress: {index}/"
                f"{len(failed_employees)} - {worker_code}"
            )

            # Do not POST employees already in payroll.
            if worker_code in existing_worker_codes:

                integration.DUPLICATE_COUNT += 1

                integration.write_audit(
                    worker_code,
                    "DUPLICATE",
                    "Employee already exists in payroll. "
                    "Skipped during recovery."
                )

                print("DUPLICATE - Employee already exists in payroll")
                continue

            try:

                status, result_message = (
                    integration.process_employee(employee)
                )

                print(status, "-", result_message)

            except Exception as error:

                integration.FAILURE_COUNT += 1

                integration.logger.exception(
                    "Recovery failed for employee %s",
                    worker_code
                )

                integration.write_audit(
                    worker_code,
                    "FAILED",
                    f"Unexpected recovery error: {error}"
                )


        # Determine recovery execution result.
        if integration.FAILURE_COUNT == 0:

            final_status = "SUCCESS"
            message = "All selected failed records were handled"

        elif (
            integration.SUCCESS_COUNT > 0
            or integration.DUPLICATE_COUNT > 0
        ):

            final_status = "PARTIAL_SUCCESS"
            message = "Recovery completed with some failures"

        else:

            final_status = "FAILED"
            message = "All recovery attempts failed"

    except Exception as error:

        message = str(error)

        integration.logger.exception(
            "Recovery execution failed"
        )

    finally:

        integration.finish_execution(
            execution_id=retry_execution_id,
            final_status=final_status,
            total_records=integration.TOTAL_RECORDS,
            success_count=integration.SUCCESS_COUNT,
            failure_count=integration.FAILURE_COUNT,
            duplicate_count=integration.DUPLICATE_COUNT,
            retry_count=integration.RETRY_COUNT,
            message=message
        )

        print("========================================")
        print("RECOVERY EXECUTION FINISHED")
        print("Execution ID:", retry_execution_id)
        print("Final status:", final_status)
        print("Total records:", integration.TOTAL_RECORDS)
        print("Successful:", integration.SUCCESS_COUNT)
        print("Failed:", integration.FAILURE_COUNT)
        print("Duplicates:", integration.DUPLICATE_COUNT)
        print("Retries:", integration.RETRY_COUNT)
        print("========================================")


# --------------------------------------------------
# 5. APPLICATION ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    main()
