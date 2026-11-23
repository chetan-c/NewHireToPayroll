
import json
import os
import uuid
import time
from pathlib import Path

import requests
from dotenv import load_dotenv


# --------------------------------------------------
# 1. LOAD PROJECT CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

PAYROLL_API_URL = os.getenv("PAYROLL_API_URL")
PAYROLL_API_KEY = os.getenv("PAYROLL_API_KEY")

if not PAYROLL_API_URL or not PAYROLL_API_KEY:
    raise RuntimeError("Payroll API configuration is missing")


# Import project modules
from validator import validate_employee
from logger_config import logger
from notification import notify_support
from audit_client import record_audit
from execution_tracker import start_execution, finish_execution


# --------------------------------------------------
# 2. CONFIGURATION
# --------------------------------------------------

SOURCE_FILE = PROJECT_ROOT / "sample-data" / "employee.json"

MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", "3"))
RETRY_BASE_DELAY = int(os.getenv("RETRY_BASE_DELAY", "2"))

if MAX_ATTEMPTS < 1:
    raise ValueError("MAX_ATTEMPTS must be at least 1")

if RETRY_BASE_DELAY < 0:
    raise ValueError("RETRY_BASE_DELAY cannot be negative")

REQUEST_HEADERS = {
    "X-API-Key": PAYROLL_API_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json"
}


# --------------------------------------------------
# 3. EXECUTION TRACKING
# --------------------------------------------------

EXECUTION_ID = str(uuid.uuid4())

TOTAL_RECORDS = 0
SUCCESS_COUNT = 0
FAILURE_COUNT = 0
DUPLICATE_COUNT = 0
RETRY_COUNT = 0


# --------------------------------------------------
# 4. AUDIT LOGGING
# --------------------------------------------------

def write_audit(worker_code, status, message, retry_count=0):

    try:
        record_audit(
            worker_code,
            status,
            message,
            retry_count,
            EXECUTION_ID
        )

        logger.info(
            "Audit record saved for employee %s",
            worker_code
        )

    except Exception:
        logger.exception(
            "Could not save audit record for employee %s",
            worker_code
        )

    if status == "FAILED":
        try:
            notify_support(worker_code, message)
        except Exception:
            logger.exception("Could not send support notification")


# --------------------------------------------------
# 5. PROCESS ONE EMPLOYEE
# --------------------------------------------------

def process_employee(employee):

    global SUCCESS_COUNT
    global FAILURE_COUNT
    global DUPLICATE_COUNT
    global RETRY_COUNT

    worker_code = (
        employee.get("employeeId", "UNKNOWN")
        if isinstance(employee, dict)
        else "UNKNOWN"
    )

    employee_retry_count = 0

    logger.info("----------------------------------------")
    logger.info("Processing employee: %s", worker_code)

    # ----------------------------------------------
    # VALIDATE EMPLOYEE
    # ----------------------------------------------

    if not isinstance(employee, dict):

        FAILURE_COUNT += 1

        message = "Employee record must be a JSON object"

        logger.error(message)
        write_audit(worker_code, "FAILED", message)

        return "FAILED", message

    errors = validate_employee(employee)

    if errors:

        for error in errors:
            logger.error(
                "Employee %s validation error: %s",
                worker_code,
                error
            )

        message = "Validation failed: " + "; ".join(errors)

        FAILURE_COUNT += 1
        write_audit(worker_code, "FAILED", message)

        return "FAILED", message

    logger.info(
        "Employee %s validation successful",
        worker_code
    )

    # ----------------------------------------------
    # TRANSFORM EMPLOYEE DATA
    # ----------------------------------------------

    payroll_employee = {
        "worker_code": employee["employeeId"],
        "first_name": employee["firstName"],
        "last_name": employee["lastName"],
        "department_name": employee["department"],
        "job_title": employee["jobTitle"],
        "annual_salary": employee["annualSalary"],
        "joining_date": employee["hireDate"],
        "pay_group": employee["payGroup"]
    }

    logger.info(
        "Employee %s transformation completed",
        worker_code
    )

    # ----------------------------------------------
    # SEND EMPLOYEE TO PAYROLL API
    # ----------------------------------------------

    for attempt in range(1, MAX_ATTEMPTS + 1):

        try:

            logger.info(
                "Sending employee %s. Attempt %s of %s",
                worker_code,
                attempt,
                MAX_ATTEMPTS
            )

            response = requests.post(
                PAYROLL_API_URL,
                json=payroll_employee,
                headers=REQUEST_HEADERS,
                timeout=10
            )

            # --------------------------------------
            # DUPLICATE EMPLOYEE
            # --------------------------------------

            if response.status_code == 409:

                message = "Employee already exists in payroll"

                logger.warning(
                    "%s: %s",
                    worker_code,
                    message
                )

                DUPLICATE_COUNT += 1

                write_audit(
                    worker_code,
                    "DUPLICATE",
                    message,
                    employee_retry_count
                )

                return "DUPLICATE", message

            # --------------------------------------
            # TEMPORARY SERVER ERRORS
            # --------------------------------------

            if response.status_code in (500, 503):

                logger.warning(
                    "Temporary server error for %s: HTTP %s",
                    worker_code,
                    response.status_code
                )

                if attempt < MAX_ATTEMPTS:

                    RETRY_COUNT += 1
                    employee_retry_count += 1

                    wait_seconds = RETRY_BASE_DELAY * (2 ** (attempt - 1))

                    logger.info(
                        "Retrying employee %s in %s seconds",
                        worker_code,
                        wait_seconds
                    )

                    time.sleep(wait_seconds)
                    continue

                message = (
                    "Payroll server failed after maximum attempts"
                )

                FAILURE_COUNT += 1

                write_audit(
                    worker_code,
                    "FAILED",
                    message,
                    employee_retry_count
                )

                return "FAILED", message

            # --------------------------------------
            # OTHER HTTP ERRORS
            # --------------------------------------

            response.raise_for_status()

            # --------------------------------------
            # SUCCESSFUL RESPONSE
            # --------------------------------------

            logger.info(
                "Payroll API successful for %s. HTTP status: %s",
                worker_code,
                response.status_code
            )

            try:
                logger.info(
                    "Payroll API response: %s",
                    response.json()
                )
            except ValueError:
                logger.info(
                    "Payroll API returned a non-JSON success response"
                )

            SUCCESS_COUNT += 1

            message = "Employee successfully created in payroll"

            write_audit(
                worker_code,
                "SUCCESS",
                message,
                employee_retry_count
            )

            return "SUCCESS", message

        # ------------------------------------------
        # REQUEST TIMEOUT
        # ------------------------------------------

        except requests.exceptions.Timeout:

            message = (
                "Payroll request timed out; outcome is unknown"
            )

            logger.error(
                "Employee %s: %s",
                worker_code,
                message
            )

            FAILURE_COUNT += 1

            write_audit(
                worker_code,
                "FAILED",
                message,
                employee_retry_count
            )

            # Do not retry automatically because the server
            # may have processed the request already.
            return "FAILED", message

        # ------------------------------------------
        # CONNECTION ERROR
        # ------------------------------------------

        except requests.exceptions.ConnectionError:

            logger.error(
                "Could not connect to payroll API for %s. Attempt %s",
                worker_code,
                attempt
            )

            if attempt < MAX_ATTEMPTS:

                RETRY_COUNT += 1
                employee_retry_count += 1

                wait_seconds = RETRY_BASE_DELAY * (2 ** (attempt - 1))

                logger.info(
                    "Retrying connection in %s seconds",
                    wait_seconds
                )

                time.sleep(wait_seconds)

            else:

                message = (
                    "Payroll connection failed after maximum attempts"
                )

                FAILURE_COUNT += 1

                write_audit(
                    worker_code,
                    "FAILED",
                    message,
                    employee_retry_count
                )

                return "FAILED", message

        # ------------------------------------------
        # HTTP ERROR
        # ------------------------------------------

        except requests.exceptions.HTTPError as error:

            status_code = (
                error.response.status_code
                if error.response is not None
                else "Unknown"
            )

            message = f"Payroll API returned HTTP {status_code}"

            logger.error(
                "Employee %s: %s",
                worker_code,
                message
            )

            FAILURE_COUNT += 1

            write_audit(
                worker_code,
                "FAILED",
                message,
                employee_retry_count
            )

            return "FAILED", message

        # ------------------------------------------
        # OTHER REQUEST ERRORS
        # ------------------------------------------

        except requests.exceptions.RequestException:

            message = "Unexpected payroll API request failure"

            logger.exception(
                "Employee %s: %s",
                worker_code,
                message
            )

            FAILURE_COUNT += 1

            write_audit(
                worker_code,
                "FAILED",
                message,
                employee_retry_count
            )

            return "FAILED", message

    return "FAILED", "Integration attempts exhausted"


# --------------------------------------------------
# 6. BATCH INTEGRATION PROCESS
# --------------------------------------------------

def run_integration():

    global TOTAL_RECORDS
    global FAILURE_COUNT

    logger.info("========================================")
    logger.info("NewHireToPayroll batch execution started")
    logger.info("Execution ID: %s", EXECUTION_ID)
    logger.info("========================================")

    # ----------------------------------------------
    # LOAD EMPLOYEE SOURCE DATA
    # ----------------------------------------------

    try:

        with open(SOURCE_FILE, "r", encoding="utf-8") as file:
            employees = json.load(file)

    except (OSError, json.JSONDecodeError):

        logger.exception("Could not load employee source data")
        raise

    if not isinstance(employees, list):

        raise ValueError(
            "Employee source file must contain a JSON array"
        )

    if not employees:

        raise ValueError(
            "Employee source file contains no employee records"
        )

    TOTAL_RECORDS = len(employees)

    logger.info(
        "Loaded %s employee records",
        TOTAL_RECORDS
    )

    # ----------------------------------------------
    # PROCESS EACH EMPLOYEE
    # ----------------------------------------------

    for index, employee in enumerate(employees, start=1):

        logger.info(
            "Batch progress: %s of %s",
            index,
            TOTAL_RECORDS
        )

        try:

            status, message = process_employee(employee)

            logger.info(
                "Employee processing result: %s - %s",
                status,
                message
            )

        except Exception as error:

            # An unexpected error for one record should
            # not stop the remaining batch records.

            worker_code = (
                employee.get("employeeId", "UNKNOWN")
                if isinstance(employee, dict)
                else "UNKNOWN"
            )

            FAILURE_COUNT += 1

            logger.exception(
                "Unexpected error while processing employee %s",
                worker_code
            )

            write_audit(
                worker_code,
                "FAILED",
                f"Unexpected processing error: {error}"
            )

            continue

    # ----------------------------------------------
    # DETERMINE BATCH RESULT
    # ----------------------------------------------

    if FAILURE_COUNT == 0:

        batch_status = "SUCCESS"
        message = "All employee records were processed without failures"

    elif SUCCESS_COUNT > 0 or DUPLICATE_COUNT > 0:

        batch_status = "PARTIAL_SUCCESS"
        message = "Batch completed with some failed employee records"

    else:

        batch_status = "FAILED"
        message = "No employee records were processed successfully"

    return batch_status, message


# --------------------------------------------------
# 7. EXECUTION LIFECYCLE
# --------------------------------------------------

def main():

    try:

        # Create execution record before processing
        start_execution(EXECUTION_ID)

        integration_status, execution_message = run_integration()

    except Exception as error:

        integration_status = "FAILED"
        execution_message = str(error)

        logger.exception("Batch integration execution failed")

    finally:

        # ------------------------------------------
        # SAVE EXECUTION SUMMARY
        # ------------------------------------------

        try:

            finish_execution(
                execution_id=EXECUTION_ID,
                final_status=integration_status,
                total_records=TOTAL_RECORDS,
                success_count=SUCCESS_COUNT,
                failure_count=FAILURE_COUNT,
                duplicate_count=DUPLICATE_COUNT,
                retry_count=RETRY_COUNT,
                message=execution_message
            )

            logger.info("Execution summary saved successfully")

        except Exception:

            logger.exception(
                "Could not update execution summary"
            )

        # ------------------------------------------
        # FINAL LOGGING
        # ------------------------------------------

        logger.info("========================================")
        logger.info("Execution ID: %s", EXECUTION_ID)
        logger.info("Final execution status: %s", integration_status)
        logger.info("Total records: %s", TOTAL_RECORDS)
        logger.info("Successful records: %s", SUCCESS_COUNT)
        logger.info("Failed records: %s", FAILURE_COUNT)
        logger.info("Duplicate records: %s", DUPLICATE_COUNT)
        logger.info("Total retries: %s", RETRY_COUNT)
        logger.info("NewHireToPayroll batch execution finished")
        logger.info("========================================")


# --------------------------------------------------
# 8. APPLICATION ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    main()
