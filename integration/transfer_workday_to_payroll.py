
import argparse
import os
import uuid
from pathlib import Path

import requests
from dotenv import load_dotenv

from integration.workday_client import WorkdayClient
from integration.workday_mapping import map_worker_to_payroll
from integration.audit_client import record_audit
from integration.execution_tracker import start_execution, finish_execution


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

PAYROLL_API_URL = os.getenv("PAYROLL_API_URL", "").strip()
PAYROLL_API_KEY = os.getenv("PAYROLL_API_KEY", "").strip()


def main():
    parser = argparse.ArgumentParser(
        description="Transfer workers from Mock Workday to Payroll"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Create missing employee records in payroll"
    )
    args = parser.parse_args()

    if not PAYROLL_API_URL or not PAYROLL_API_KEY:
        raise RuntimeError("Payroll API URL or API key is missing from .env")

    headers = {"X-API-Key": PAYROLL_API_KEY}

    print("Connecting to Mock Workday...")
    workday = WorkdayClient(access_token="local-test-token")
    workers = workday.get_all_workers(page_size=2)

    print("Retrieved workers:", len(workers))

    response = requests.get(
        PAYROLL_API_URL,
        headers=headers,
        timeout=30
    )
    response.raise_for_status()

    existing_employees = response.json().get("employees", [])
    existing_codes = {
        employee["worker_code"] for employee in existing_employees
    }

    execution_id = str(uuid.uuid4())

    created = 0
    skipped = 0
    failed = 0
    retry_count = 0

    print("\n" + "=" * 50)
    print("WORKDAY TO PAYROLL TRANSFER")
    print("Mode:", "EXECUTION" if args.execute else "DRY RUN")
    print("Execution ID:", execution_id)
    print("=" * 50)

    if args.execute:
        start_execution(execution_id)

    for worker in workers:
        payroll_data = map_worker_to_payroll(worker)
        worker_code = payroll_data["worker_code"]

        if worker_code in existing_codes:
            print(f"SKIPPED {worker_code}: Already exists in payroll")
            skipped += 1

            if args.execute:
                record_audit(
                    worker_code,
                    "DUPLICATE",
                    "Employee already exists in payroll",
                    execution_id=execution_id
                )
            continue

        if not args.execute:
            print(f"READY {worker_code}: {payroll_data['first_name']} "
                  f"{payroll_data['last_name']}")
            continue

        try:
            result = requests.post(
                PAYROLL_API_URL,
                json=payroll_data,
                headers=headers,
                timeout=30
            )

            if result.status_code == 409:
                print(f"SKIPPED {worker_code}: Duplicate detected by payroll API")
                skipped += 1
                existing_codes.add(worker_code)

                record_audit(
                    worker_code,
                    "DUPLICATE",
                    "Payroll API rejected duplicate employee",
                    execution_id=execution_id
                )
                continue

            result.raise_for_status()

            print(f"CREATED {worker_code}: Payroll record created")
            created += 1
            existing_codes.add(worker_code)

            record_audit(
                worker_code,
                "SUCCESS",
                "Employee transferred successfully from Mock Workday",
                execution_id=execution_id
            )

        except requests.RequestException as error:
            print(f"FAILED {worker_code}: {error}")
            failed += 1

            record_audit(
                worker_code,
                "FAILED",
                str(error)[:500],
                execution_id=execution_id
            )

    if args.execute:
        if failed == 0:
            final_status = "SUCCESS"
        elif created > 0 or skipped > 0:
            final_status = "PARTIAL_SUCCESS"
        else:
            final_status = "FAILED"

        finish_execution(
            execution_id=execution_id,
            final_status=final_status,
            total_records=len(workers),
            success_count=created,
            failure_count=failed,
            duplicate_count=skipped,
            retry_count=retry_count,
            message="Workday-to-Payroll transfer completed"
        )

    print("\n" + "=" * 50)
    print("TRANSFER SUMMARY")
    print("Created:", created)
    print("Skipped:", skipped)
    print("Failed:", failed)

    if not args.execute:
        print("Ready for transfer:", len(workers) - skipped)
        print("No payroll records were created.")

    print("Execution ID:", execution_id)
    print("=" * 50)


if __name__ == "__main__":
    main()
