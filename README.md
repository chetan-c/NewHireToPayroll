
# NewHireToPayroll

### Workday HCM to Payroll Integration Simulation

A Python-based employee integration project that simulates retrieving new-hire records from Workday HCM, validating and transforming employee data, and transferring it to a payroll system through REST APIs.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-API-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue)
![Pytest](https://img.shields.io/badge/Tests-26%20passed-success)
![Integration](https://img.shields.io/badge/Integration-Workday%20Simulation-orange)

---

## Project Overview

NewHireToPayroll demonstrates an employee onboarding integration workflow.

The application retrieves worker information from a locally hosted Mock Workday HCM REST API, validates and maps the data, and sends new employee records to a simulated payroll API.

PostgreSQL stores employee records, while audit logs and execution tracking provide traceability.

**Important:** This project currently uses a Mock Workday API for development and testing. It is not connected to a live Workday tenant.

## Architecture

```mermaid
flowchart TD
    A["Mock Workday HCM API"] --> B["Python Integration"]
    B --> C["Retrieve Worker Records"]
    C --> D["Validate Employee Data"]
    D --> E["Map Workday Data to Payroll Format"]
    E --> F["Duplicate Detection"]
    F --> G["Payroll REST API - FastAPI"]
    G --> H[("PostgreSQL Database")]
    B --> I["Execution Tracking"]
    B --> J["Audit Logging"]
    B --> K["Retry and Recovery"]
```

## Screenshots

### Mock Workday API

![Mock Workday API](screenshots/workday-api.png)

### API Documentation

![Swagger UI](screenshots/swagger-ui.png)

### API Health Check

![Health Check](screenshots/health-check.png)

### Automated Tests

![Pytest Results](screenshots/pytest-results.png)

### GitHub Actions CI

![GitHub Actions](screenshots/github-actions.png)

## Key Features

- Mock Workday HCM REST API.
- HTTP-based worker retrieval.
- Pagination support.
- Employee data validation.
- Data mapping and transformation.
- Payroll REST API using FastAPI.
- API-key authentication.
- PostgreSQL database integration.
- Duplicate employee prevention.
- Dry-run and execution modes.
- Retry and failed-record recovery.
- Execution tracking with unique execution IDs.
- Audit logging.
- Automated testing with Pytest.
- GitHub Actions CI workflow.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Integration logic |
| FastAPI | Mock Workday and Payroll APIs |
| REST APIs | System communication |
| Requests | HTTP client |
| PostgreSQL | Persistent storage |
| Psycopg | PostgreSQL connectivity |
| Pydantic | Request validation |
| Pytest | Automated testing |
| Git & GitHub | Version control |
| GitHub Actions | Continuous integration |

## Project Structure

```text
NewHireToPayroll/
│
├── sample-data/
│   └── employee.json
│
├── mock-workday-api/
│   └── main.py
│
├── payroll-api/
│   ├── main.py
│   ├── database.py
│   ├── audit.py
│   └── db_connection_check.py
│
├── integration/
│   ├── __init__.py
│   ├── send_employee.py
│   ├── validator.py
│   ├── logger_config.py
│   ├── audit_client.py
│   ├── notification.py
│   ├── execution_tracker.py
│   ├── retry_failed.py
│   ├── workday_client.py
│   ├── workday_config.py
│   ├── workday_mapping.py
│   ├── test_workday_connection.py
│   └── transfer_workday_to_payroll.py
│
├── tests/
│   ├── test_validator.py
│   ├── test_api.py
│   ├── test_execution_tracker.py
│   ├── test_integration_flow.py
│   ├── test_recovery.py
│   ├── test_workday_client.py
│   ├── test_workday_config.py
│   ├── test_workday_mapping.py
│   └── test_workday_pagination.py
│
├── screenshots/
│   ├── github-actions.png
│   ├── health-check.png
│   ├── pytest-results.png
│   ├── swagger-ui.png
│   └── workday-api.png
│
├── logs/
├── .github/
│   └── workflows/
│       └── tests.yml
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup and Installation

### 1. Clone the repository

```bash
git clone https://github.com/chetan-c/NewHireToPayroll.git
cd NewHireToPayroll
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create your local `.env` file from the example:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and configure your own database password and API key.

The configuration includes:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/newhire_payroll
PAYROLL_API_URL=http://127.0.0.1:8000/payroll/employees
PAYROLL_API_KEY=YOUR_API_KEY
MAX_ATTEMPTS=3
RETRY_BASE_DELAY=2
WORKDAY_BASE_URL=http://127.0.0.1:8001
```

Never commit your `.env` file or expose API keys and database passwords.

### 5. Start the local APIs

Open separate terminals from the project root.

**Mock Workday API:**

```bash
uvicorn main:app --reload --app-dir mock-workday-api --port 8001
```

**Payroll API:**

```bash
uvicorn main:app --reload --app-dir payroll-api --port 8000
```

### 6. Run the integration

Retrieve workers from Mock Workday:

```bash
python -m integration.test_workday_connection
```

Run a safe dry-run:

```bash
python -m integration.transfer_workday_to_payroll
```

Execute the transfer:

```bash
python -m integration.transfer_workday_to_payroll --execute
```

### 7. Run automated tests

```bash
pytest -v
```

## Verified Results

The project has successfully demonstrated:

- Retrieval of five worker records from the Mock Workday API.
- Pagination across multiple API requests.
- Detection of four existing payroll employees.
- Successful transfer of one new employee.
- Prevention of duplicate employee creation.
- PostgreSQL execution tracking and audit records.

Example execution:

| Metric | Result |
|---|---:|
| Workers retrieved | 5 |
| Employees created | 1 |
| Duplicates skipped | 4 |
| Failed records | 0 |
| Execution status | SUCCESS |

**Automated testing:** 26 tests passed, with one non-failing deprecation warning in the latest recorded full test run.

## Security and Reliability

- API-key authentication for payroll endpoints.
- Environment variables for sensitive configuration.
- `.gitignore` protection for local secrets.
- Input validation before employee processing.
- Duplicate prevention using employee identifiers.
- Error handling and retry/recovery mechanisms.
- Execution IDs and audit records for traceability.

## Current Project Status

This is a working local integration simulation.

The Mock Workday API uses sample employee data and a local development token. Actual Workday tenant authentication, tenant-specific API configuration, and validation against a real Workday response remain future work pending authorized tenant access.

## Future Enhancements

- Connect to an authorized Workday tenant.
- Implement tenant-specific authentication.
- Adapt worker mapping to actual Workday API responses.
- Add real-time integration monitoring.
- Integrate email or messaging notifications.

## Learning Outcomes

Through this project, I gained practical experience with:

- Enterprise system integration concepts.
- REST API development and consumption.
- Python-based data transformation.
- Database operations using PostgreSQL.
- Authentication and configuration management.
- Error handling, retry mechanisms, and recovery.
- Audit logging and execution monitoring.
- Automated testing and CI/CD.

---

## Author

**Chetan Kamble**

- GitHub: https://github.com/chetan-c
- LinkedIn: https://www.linkedin.com/in/chetan-kamble01/
- Portfolio: https://chetan-c.github.io/PortFolio_/

---

*Built as a hands-on enterprise integration learning project.*
