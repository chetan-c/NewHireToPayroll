
import sys
from pathlib import Path

# Allow Python to import integration modules.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INTEGRATION_FOLDER = PROJECT_ROOT / "integration"

sys.path.insert(0, str(INTEGRATION_FOLDER))

import send_employee


def test_employee_successful_integration(monkeypatch):

    # ------------------------------------------
    # 1. PREPARE TEST EMPLOYEE
    # ------------------------------------------

    employee = {
        "employeeId": "TEST900001",
        "firstName": "Integration",
        "lastName": "Tester",
        "email": "integration.tester@example.com",
        "department": "Engineering",
        "jobTitle": "Software Tester",
        "hireDate": "2026-11-20",
        "company": "ABC Technologies",
        "location": "Bangalore",
        "annualSalary": 500000,
        "payGroup": "Monthly"
    }

    # ------------------------------------------
    # 2. RESET INTEGRATION COUNTERS
    # ------------------------------------------

    monkeypatch.setattr(send_employee, "SUCCESS_COUNT", 0)
    monkeypatch.setattr(send_employee, "FAILURE_COUNT", 0)
    monkeypatch.setattr(send_employee, "DUPLICATE_COUNT", 0)
    monkeypatch.setattr(send_employee, "RETRY_COUNT", 0)

    # ------------------------------------------
    # 3. MOCK PAYROLL API RESPONSE
    # ------------------------------------------

    class MockResponse:

        status_code = 201

        def json(self):
            return {
                "message": "Employee created successfully",
                "worker_code": "TEST900001",
                "payroll_status": "CREATED"
            }

        def raise_for_status(self):
            return None

    captured_request = {}

    def mock_post(url, json, headers, timeout):

        captured_request["url"] = url
        captured_request["payload"] = json
        captured_request["headers"] = headers

        return MockResponse()

    monkeypatch.setattr(
        send_employee.requests,
        "post",
        mock_post
    )

    # ------------------------------------------
    # 4. MOCK AUDIT DATABASE OPERATION
    # ------------------------------------------

    audit_records = []

    def mock_write_audit(
        worker_code,
        status,
        message,
        retry_count=0
    ):

        audit_records.append({
            "worker_code": worker_code,
            "status": status,
            "message": message,
            "retry_count": retry_count
        })

    monkeypatch.setattr(
        send_employee,
        "write_audit",
        mock_write_audit
    )

    # ------------------------------------------
    # 5. EXECUTE EMPLOYEE PROCESSING
    # ------------------------------------------

    status, message = send_employee.process_employee(
        employee
    )

    # ------------------------------------------
    # 6. VERIFY RESULTS
    # ------------------------------------------

    assert status == "SUCCESS"

    assert send_employee.SUCCESS_COUNT == 1
    assert send_employee.FAILURE_COUNT == 0

    assert captured_request["payload"]["worker_code"] == (
        "TEST900001"
    )

    assert captured_request["payload"]["first_name"] == (
        "Integration"
    )

    assert len(audit_records) == 1

    assert audit_records[0]["worker_code"] == "TEST900001"
    assert audit_records[0]["status"] == "SUCCESS"

    print("Integration workflow test completed successfully.")
    print("Employee:", "TEST900001")
    print("Result:", status)
    print("Message:", message)


def test_duplicate_employee_handling(monkeypatch):

    employee = {
        "employeeId": "TEST900002",
        "firstName": "Duplicate",
        "lastName": "Tester",
        "email": "duplicate.tester@example.com",
        "department": "Engineering",
        "jobTitle": "Software Tester",
        "hireDate": "2026-11-20",
        "company": "ABC Technologies",
        "location": "Bangalore",
        "annualSalary": 500000,
        "payGroup": "Monthly"
    }

    # Reset counters
    monkeypatch.setattr(send_employee, "SUCCESS_COUNT", 0)
    monkeypatch.setattr(send_employee, "FAILURE_COUNT", 0)
    monkeypatch.setattr(send_employee, "DUPLICATE_COUNT", 0)
    monkeypatch.setattr(send_employee, "RETRY_COUNT", 0)

    # Simulate first request: employee created.
    # Simulate second request: employee already exists.
    class MockResponse:

        def __init__(self, status_code):
            self.status_code = status_code

        def json(self):
            if self.status_code == 201:
                return {
                    "message": "Employee created successfully",
                    "worker_code": "TEST900002",
                    "payroll_status": "CREATED"
                }

            return {
                "detail": "Employee already exists in payroll"
            }

        def raise_for_status(self):
            return None

    responses = [
        MockResponse(201),
        MockResponse(409)
    ]

    request_count = {"value": 0}

    def mock_post(url, json, headers, timeout):
        response = responses[request_count["value"]]
        request_count["value"] += 1
        return response

    monkeypatch.setattr(
        send_employee.requests,
        "post",
        mock_post
    )

    # Capture audit records
    audit_records = []

    def mock_write_audit(
        worker_code,
        status,
        message,
        retry_count=0
    ):
        audit_records.append({
            "worker_code": worker_code,
            "status": status,
            "message": message
        })

    monkeypatch.setattr(
        send_employee,
        "write_audit",
        mock_write_audit
    )

    # First attempt
    first_status, first_message = send_employee.process_employee(
        employee
    )

    # Second attempt with the same employee
    second_status, second_message = send_employee.process_employee(
        employee
    )

    # Verify results
    assert first_status == "SUCCESS"
    assert second_status == "DUPLICATE"

    assert send_employee.SUCCESS_COUNT == 1
    assert send_employee.DUPLICATE_COUNT == 1
    assert send_employee.FAILURE_COUNT == 0

    assert request_count["value"] == 2

    assert len(audit_records) == 2
    assert audit_records[0]["status"] == "SUCCESS"
    assert audit_records[1]["status"] == "DUPLICATE"

    print("Duplicate employee test completed successfully.")
    print("First request:", first_status)
    print("Second request:", second_status)



def test_employee_retry_after_server_error(monkeypatch):

    employee = {
        "employeeId": "TEST900003",
        "firstName": "Retry",
        "lastName": "Tester",
        "email": "retry.tester@example.com",
        "department": "Engineering",
        "jobTitle": "Software Tester",
        "hireDate": "2026-11-20",
        "company": "ABC Technologies",
        "location": "Bangalore",
        "annualSalary": 500000,
        "payGroup": "Monthly"
    }

    # Reset counters
    monkeypatch.setattr(send_employee, "SUCCESS_COUNT", 0)
    monkeypatch.setattr(send_employee, "FAILURE_COUNT", 0)
    monkeypatch.setattr(send_employee, "DUPLICATE_COUNT", 0)
    monkeypatch.setattr(send_employee, "RETRY_COUNT", 0)

    # Make the test fast: no actual waiting between retries
    monkeypatch.setattr(send_employee.time, "sleep", lambda seconds: None)

    # First two requests fail; third succeeds
    class MockResponse:

        def __init__(self, status_code):
            self.status_code = status_code

        def json(self):
            return {
                "message": "Employee created successfully",
                "worker_code": "TEST900003",
                "payroll_status": "CREATED"
            }

        def raise_for_status(self):
            if self.status_code >= 400:
                import requests
                raise requests.exceptions.HTTPError(
                    f"HTTP {self.status_code}"
                )

    responses = [
        MockResponse(500),
        MockResponse(503),
        MockResponse(201)
    ]

    request_count = {"value": 0}

    def mock_post(url, json, headers, timeout):
        response = responses[request_count["value"]]
        request_count["value"] += 1
        return response

    monkeypatch.setattr(
        send_employee.requests,
        "post",
        mock_post
    )

    audit_records = []

    def mock_write_audit(
        worker_code,
        status,
        message,
        retry_count=0
    ):
        audit_records.append({
            "worker_code": worker_code,
            "status": status,
            "retry_count": retry_count
        })

    monkeypatch.setattr(
        send_employee,
        "write_audit",
        mock_write_audit
    )

    status, message = send_employee.process_employee(employee)

    assert status == "SUCCESS"
    assert request_count["value"] == 3
    assert send_employee.SUCCESS_COUNT == 1
    assert send_employee.RETRY_COUNT == 2
    assert send_employee.FAILURE_COUNT == 0

    assert len(audit_records) == 1
    assert audit_records[0]["status"] == "SUCCESS"
    assert audit_records[0]["retry_count"] == 2

    print("Retry test completed successfully.")
    print("Total API attempts:", request_count["value"])
    print("Retries:", send_employee.RETRY_COUNT)
    print("Final result:", status)


def test_employee_failure_after_retries_exhausted(monkeypatch):

    employee = {
        "employeeId": "TEST900004",
        "firstName": "Failure",
        "lastName": "Tester",
        "email": "failure.tester@example.com",
        "department": "Engineering",
        "jobTitle": "Software Tester",
        "hireDate": "2026-11-20",
        "company": "ABC Technologies",
        "location": "Bangalore",
        "annualSalary": 500000,
        "payGroup": "Monthly"
    }

    monkeypatch.setattr(send_employee, "SUCCESS_COUNT", 0)
    monkeypatch.setattr(send_employee, "FAILURE_COUNT", 0)
    monkeypatch.setattr(send_employee, "DUPLICATE_COUNT", 0)
    monkeypatch.setattr(send_employee, "RETRY_COUNT", 0)

    monkeypatch.setattr(
        send_employee.time,
        "sleep",
        lambda seconds: None
    )

    class MockResponse:

        status_code = 500

        def json(self):
            return {"detail": "Simulated payroll server failure"}

        def raise_for_status(self):
            import requests
            raise requests.exceptions.HTTPError("HTTP 500")

    request_count = {"value": 0}

    def mock_post(url, json, headers, timeout):
        request_count["value"] += 1
        return MockResponse()

    monkeypatch.setattr(
        send_employee.requests,
        "post",
        mock_post
    )

    audit_records = []

    def mock_write_audit(
        worker_code,
        status,
        message,
        retry_count=0
    ):
        audit_records.append({
            "worker_code": worker_code,
            "status": status,
            "retry_count": retry_count
        })

    monkeypatch.setattr(
        send_employee,
        "write_audit",
        mock_write_audit
    )

    status, message = send_employee.process_employee(employee)

    assert status == "FAILED"
    assert request_count["value"] == send_employee.MAX_ATTEMPTS
    assert send_employee.FAILURE_COUNT == 1
    assert send_employee.SUCCESS_COUNT == 0
    assert send_employee.RETRY_COUNT == send_employee.MAX_ATTEMPTS - 1

    assert len(audit_records) == 1
    assert audit_records[0]["status"] == "FAILED"

    print("Permanent failure test completed successfully.")
    print("Total API attempts:", request_count["value"])
    print("Retries:", send_employee.RETRY_COUNT)
    print("Final result:", status)


def test_invalid_employee_rejected_before_api_call(monkeypatch):

    employee = {
        "employeeId": "",
        "firstName": "Invalid",
        "lastName": "Employee",
        "email": "invalid-email",
        "department": "",
        "jobTitle": "Tester",
        "hireDate": "2026-11-20",
        "company": "ABC Technologies",
        "location": "Bangalore",
        "annualSalary": -500000,
        "payGroup": "Monthly"
    }

    monkeypatch.setattr(send_employee, "SUCCESS_COUNT", 0)
    monkeypatch.setattr(send_employee, "FAILURE_COUNT", 0)
    monkeypatch.setattr(send_employee, "DUPLICATE_COUNT", 0)
    monkeypatch.setattr(send_employee, "RETRY_COUNT", 0)

    api_calls = {"value": 0}
    audit_records = []

    def mock_post(url, json, headers, timeout):
        api_calls["value"] += 1
        raise AssertionError("Invalid employee must not reach payroll API")

    def mock_write_audit(
        worker_code,
        status,
        message,
        retry_count=0
    ):
        audit_records.append({
            "worker_code": worker_code,
            "status": status,
            "message": message
        })

    monkeypatch.setattr(send_employee.requests, "post", mock_post)
    monkeypatch.setattr(send_employee, "write_audit", mock_write_audit)

    status, message = send_employee.process_employee(employee)

    assert status == "FAILED"
    assert api_calls["value"] == 0
    assert send_employee.FAILURE_COUNT == 1
    assert send_employee.SUCCESS_COUNT == 0

    assert len(audit_records) == 1
    assert audit_records[0]["status"] == "FAILED"

    print("Validation failure test completed successfully.")
    print("Payroll API calls:", api_calls["value"])
    print("Final result:", status)
