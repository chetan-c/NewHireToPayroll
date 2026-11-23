

# NewHireToPayroll

![CI](https://github.com/chetan-c/NewHireToPayroll/actions/workflows/tests.yml/badge.svg)

**Automated Employee Onboarding to Payroll Integration — Python, FastAPI and PostgreSQL**

## Overview

NewHireToPayroll is a Python-based integration project that simulates transferring new employee information from an HR system (Workday HCM scenario) to an external payroll system.

It demonstrates how an integration workflow can validate employee information, transform JSON payloads, communicate with REST APIs, store payroll records, handle failures, retry requests, and maintain execution audit logs.

**Note:** This is currently a local simulation. It is not connected to a live Workday HCM tenant or Workday Orchestrate.

## Architecture

```text
HR Source (Simulated Workday HCM)
              |
              v
      Employee JSON Data
              |
              v
      Python Integration
              |
       Employee Validation
              |
       Data Transformation
              |
         REST API POST
              |
              v
       FastAPI Payroll API
              |
              v
       PostgreSQL Database
              |
       +------+------+
       |             |
    Audit Logs   Execution Tracking
       |
       v
 Retry and Recovery Handling
```

## Technology Stack

- **Language:** Python
- **API Framework:** FastAPI
- **Database:** PostgreSQL
- **API Communication:** REST API, HTTP, JSON
- **Libraries:** Requests, Psycopg, Pydantic, Python-dotenv
- **Testing:** Pytest, HTTPX
- **Tools:** VS Code, Postman, Git and GitHub

## Key Features

- Employee onboarding data processing
- Employee data validation
- JSON payload transformation
- REST API integration
- API-key authentication
- PostgreSQL payroll record storage
- Duplicate employee prevention
- Configurable retry mechanism
- Exponential backoff
- Failed employee recovery
- Audit logging
- Execution ID tracking
- Batch employee processing
- Support alerts through application logs
- Automated integration and API tests

## Project Structure

```text
NewHireToPayroll/
│
├── sample-data/
│   └── employee.json
│
├── payroll-api/
│   ├── main.py
│   ├── database.py
│   └── test_db.py
│
├── integration/
│   ├── send_employee.py
│   ├── validator.py
│   ├── logger_config.py
│   ├── audit_client.py
│   ├── notification.py
│   ├── execution_tracker.py
│   └── retry_failed.py
│
├── tests/
│   ├── test_validator.py
│   ├── test_api.py
│   ├── test_execution_tracker.py
│   ├── test_integration_flow.py
│   └── test_recovery.py
│
├── logs/
├── .env
├── .gitignore
└── README.md
```

## Setup and Installation

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd NewHireToPayroll
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install fastapi uvicorn "psycopg[binary]" python-dotenv requests pytest httpx
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```dotenv
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/newhire_payroll
PAYROLL_API_URL=http://127.0.0.1:8000/payroll/employees
PAYROLL_API_KEY=YOUR_GENERATED_SECRET_KEY
MAX_ATTEMPTS=3
RETRY_BASE_DELAY=2
```

Replace the placeholders with your local configuration.

### 5. Configure PostgreSQL

Create a database named:

```sql
CREATE DATABASE newhire_payroll;
```

Create the required `employees`, `integration_logs`, and `integration_executions` tables using the SQL schema provided in the project setup.

### 6. Start the payroll API

Open a terminal:

```powershell
cd payroll-api
uvicorn main:app --reload
```

Health check:

```text
http://127.0.0.1:8000/health
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

### 7. Run the integration

Open another terminal from the project root:

```powershell
python integration/send_employee.py
```

### 8. Run failed employee recovery

```powershell
python integration/retry_failed.py
```

## Testing

Run the complete automated test suite:

```bash
python -m pytest -v
```

The tests cover:

- Employee validation
- API health and authentication
- Execution tracking
- Successful employee processing
- Duplicate employee handling
- Retry after temporary server errors
- Failure after retry exhaustion
- Invalid employee rejection
- Recovery and duplicate reconciliation

## Security

- Store API keys and database credentials in `.env`.
- Do not commit `.env` to GitHub.
- Use fictional employee information for testing.
- Do not include real employee or payroll records in the repository.

## Project Status

The local integration workflow, PostgreSQL persistence, retry and recovery mechanisms, and automated tests have been implemented and tested.

**Future enhancements:**
- Connect to an authorized Workday sandbox tenant.
- Implement actual Workday integration using supported Workday services.
- Explore Workday Orchestrate for workflow automation.
- Add email or messaging-based support notifications.
- Add a monitoring dashboard.

## Learning Outcomes

This project demonstrates practical understanding of:

- Enterprise integration concepts
- REST API development and consumption
- Data validation and transformation
- Python backend development
- PostgreSQL database integration
- Error handling and retry strategies
- Audit logging and execution monitoring
- Automated testing
