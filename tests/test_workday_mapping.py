
from integration.workday_mapping import map_worker_to_payroll


def test_map_worker_to_payroll():
    worker = {
        "employeeId": "TEST100",
        "firstName": "John",
        "lastName": "Smith",
        "email": "john@example.com",
        "department": "IT",
        "jobTitle": "Software Engineer",
        "hireDate": "2026-11-20",
        "company": "ABC Technologies",
        "location": "Bangalore",
        "annualSalary": 1200000,
        "payGroup": "Monthly"
    }

    result = map_worker_to_payroll(worker)

    assert result == {
        "worker_code": "TEST100",
        "first_name": "John",
        "last_name": "Smith",
        "department_name": "IT",
        "job_title": "Software Engineer",
        "annual_salary": 1200000,
        "joining_date": "2026-11-20",
        "pay_group": "Monthly"
    }
