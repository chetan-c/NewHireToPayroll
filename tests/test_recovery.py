
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INTEGRATION_FOLDER = PROJECT_ROOT / "integration"

sys.path.insert(0, str(INTEGRATION_FOLDER))

import retry_failed


def test_recovery_skips_existing_employee(monkeypatch):

    employee = {
        "employeeId": "TEST900005",
        "firstName": "Recovery",
        "lastName": "Tester"
    }

    audit_records = []
    execution_summary = {}

    monkeypatch.setattr(
        retry_failed,
        "get_failed_worker_codes",
        lambda: {"TEST900005"}
    )

    monkeypatch.setattr(
        retry_failed,
        "load_failed_employees",
        lambda codes: [employee]
    )

    monkeypatch.setattr(
        retry_failed,
        "get_existing_worker_codes",
        lambda codes: {"TEST900005"}
    )

    monkeypatch.setattr(
        retry_failed.integration,
        "start_execution",
        lambda execution_id: None
    )

    monkeypatch.setattr(
        retry_failed.integration,
        "write_audit",
        lambda worker_code, status, message, retry_count=0:
        audit_records.append({
            "worker_code": worker_code,
            "status": status
        })
    )

    def mock_process_employee(employee):
        raise AssertionError(
            "Existing employee must not be sent to payroll"
        )

    monkeypatch.setattr(
        retry_failed.integration,
        "process_employee",
        mock_process_employee
    )

    def mock_finish_execution(**kwargs):
        execution_summary.update(kwargs)

    monkeypatch.setattr(
        retry_failed.integration,
        "finish_execution",
        mock_finish_execution
    )

    retry_failed.main()

    assert retry_failed.integration.DUPLICATE_COUNT == 1
    assert retry_failed.integration.SUCCESS_COUNT == 0
    assert retry_failed.integration.FAILURE_COUNT == 0

    assert len(audit_records) == 1
    assert audit_records[0]["status"] == "DUPLICATE"

    assert execution_summary["final_status"] == "SUCCESS"
    assert execution_summary["duplicate_count"] == 1

    print("Recovery test completed successfully.")
    print("Existing employee skipped:", employee["employeeId"])
    print("Recovery result:", execution_summary["final_status"])
