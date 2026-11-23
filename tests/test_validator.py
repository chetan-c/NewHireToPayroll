
from integration.validator import validate_employee


def get_valid_employee():
    return {
        "employeeId": "100245",
        "firstName": "John",
        "lastName": "Smith",
        "email": "john.smith@example.com",
        "department": "IT",
        "jobTitle": "Software Engineer",
        "hireDate": "2026-11-20",
        "company": "ABC Technologies",
        "location": "Bangalore",
        "annualSalary": 1200000,
        "payGroup": "Monthly"
    }


def test_valid_employee():
    employee = get_valid_employee()

    errors = validate_employee(employee)

    assert errors == []


def test_missing_employee_id():
    employee = get_valid_employee()
    employee["employeeId"] = ""

    errors = validate_employee(employee)

    assert "Employee ID is required" in errors


def test_invalid_email():
    employee = get_valid_employee()
    employee["email"] = "invalid-email"

    errors = validate_employee(employee)

    assert "Invalid email address" in errors


def test_negative_salary():
    employee = get_valid_employee()
    employee["annualSalary"] = -5000

    errors = validate_employee(employee)

    assert "Annual salary must be a positive number" in errors


def test_invalid_pay_group():
    employee = get_valid_employee()
    employee["payGroup"] = "Daily"

    errors = validate_employee(employee)

    assert "Invalid pay group" in errors
