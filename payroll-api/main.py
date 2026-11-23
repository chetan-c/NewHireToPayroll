
import os
import secrets
from pathlib import Path
from datetime import date

import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field, field_validator, ConfigDict

from database import get_connection


# --------------------------------------------------
# 1. LOAD ENVIRONMENT VARIABLES
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("PAYROLL_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "PAYROLL_API_KEY is missing. "
        "Please configure it in the root .env file."
    )


# --------------------------------------------------
# 2. CREATE FASTAPI APPLICATION
# --------------------------------------------------

app = FastAPI(
    title="NewHireToPayroll API",
    description="Simulated external payroll API connected to PostgreSQL",
    version="3.1.0"
)


# --------------------------------------------------
# 3. API KEY AUTHENTICATION
# --------------------------------------------------

def verify_api_key(x_api_key: str = Header(...)):
    """
    Verify the API key sent by the integration client.
    """

    if not secrets.compare_digest(x_api_key, API_KEY):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    return True


# --------------------------------------------------
# 4. EMPLOYEE REQUEST MODEL
# --------------------------------------------------

class PayrollEmployee(BaseModel):

    model_config = ConfigDict(str_strip_whitespace=True)

    worker_code: str = Field(min_length=1, max_length=50)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    department_name: str = Field(min_length=1, max_length=100)
    job_title: str = Field(min_length=1, max_length=150)
    annual_salary: float = Field(gt=0)
    joining_date: date
    pay_group: str

    @field_validator("pay_group")
    @classmethod
    def validate_pay_group(cls, value):

        allowed_pay_groups = [
            "Monthly",
            "Weekly",
            "Biweekly"
        ]

        if value not in allowed_pay_groups:
            raise ValueError("Invalid pay group")

        return value


# --------------------------------------------------
# 5. HEALTH CHECK ENDPOINT
# --------------------------------------------------

@app.get("/health")
def health_check():

    return {
        "status": "running",
        "application": "NewHireToPayroll API",
        "version": "3.1.0"
    }


# --------------------------------------------------
# 6. CREATE EMPLOYEE ENDPOINT
# --------------------------------------------------

@app.post(
    "/payroll/employees",
    status_code=201,
    dependencies=[Depends(verify_api_key)]
)
def create_employee(employee: PayrollEmployee):

    try:

        with get_connection() as connection:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    INSERT INTO employees (
                        worker_code,
                        first_name,
                        last_name,
                        department_name,
                        job_title,
                        annual_salary,
                        joining_date,
                        pay_group
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (
                        employee.worker_code,
                        employee.first_name,
                        employee.last_name,
                        employee.department_name,
                        employee.job_title,
                        employee.annual_salary,
                        employee.joining_date,
                        employee.pay_group
                    )
                )

                database_id = cursor.fetchone()[0]

        return {
            "message": "Employee created successfully",
            "database_id": database_id,
            "worker_code": employee.worker_code,
            "employee_name": (
                employee.first_name + " " + employee.last_name
            ),
            "payroll_status": "CREATED"
        }

    except psycopg.errors.UniqueViolation:

        raise HTTPException(
            status_code=409,
            detail="Employee already exists in payroll"
        )

    except psycopg.Error:

        raise HTTPException(
            status_code=500,
            detail="Database operation failed"
        )


# --------------------------------------------------
# 7. GET ALL EMPLOYEES ENDPOINT
# --------------------------------------------------

@app.get(
    "/payroll/employees",
    dependencies=[Depends(verify_api_key)]
)
def get_employees():

    try:

        with get_connection() as connection:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        id,
                        worker_code,
                        first_name,
                        last_name,
                        department_name,
                        job_title,
                        annual_salary,
                        joining_date,
                        pay_group,
                        created_at
                    FROM employees
                    ORDER BY id;
                    """
                )

                rows = cursor.fetchall()

                employees = [
                    {
                        "id": row[0],
                        "worker_code": row[1],
                        "first_name": row[2],
                        "last_name": row[3],
                        "department_name": row[4],
                        "job_title": row[5],
                        "annual_salary": float(row[6]),
                        "joining_date": row[7].isoformat(),
                        "pay_group": row[8],
                        "created_at": row[9].isoformat()
                    }
                    for row in rows
                ]

        return {
            "total_employees": len(employees),
            "employees": employees
        }

    except psycopg.Error:

        raise HTTPException(
            status_code=500,
            detail="Could not retrieve employees from database"
        )
