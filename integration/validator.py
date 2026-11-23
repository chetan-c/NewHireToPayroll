
from datetime import date
import re


def validate_employee(employee):

    errors = []

    # Check employee ID
    if not employee.get("employeeId"):
        errors.append("Employee ID is required")

    # Check first name
    if not employee.get("firstName"):
        errors.append("First name is required")

    # Check last name
    if not employee.get("lastName"):
        errors.append("Last name is required")

    # Check email
    email = employee.get("email", "")

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        errors.append("Invalid email address")

    # Check department
    if not employee.get("department"):
        errors.append("Department is required")

    # Check job title
    if not employee.get("jobTitle"):
        errors.append("Job title is required")

    # Check annual salary
    salary = employee.get("annualSalary")

    if (
        isinstance(salary, bool)
        or not isinstance(salary, (int, float))
        or salary <= 0
    ):
        errors.append("Annual salary must be a positive number")

    # Check hire date
    try:
        hire_date = date.fromisoformat(employee.get("hireDate", ""))
        if hire_date > date.today():
            errors.append("Hire date cannot be in the future")
    except (ValueError, TypeError):
        errors.append("Hire date must use YYYY-MM-DD format")

    # Check pay group
    if employee.get("payGroup") not in ["Monthly", "Weekly", "Biweekly"]:
        errors.append("Invalid pay group")

    return errors
