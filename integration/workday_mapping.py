
def map_worker_to_payroll(worker):
    """
    Convert normalized Workday worker data
    into the payroll API request format.

    The input fields are provisional. We will connect
    them to the actual Workday response after tenant access.
    """

    return {
        "worker_code": worker["employeeId"],
        "first_name": worker["firstName"],
        "last_name": worker["lastName"],
        "department_name": worker["department"],
        "job_title": worker["jobTitle"],
        "annual_salary": worker["annualSalary"],
        "joining_date": worker["hireDate"],
        "pay_group": worker["payGroup"]
    }
