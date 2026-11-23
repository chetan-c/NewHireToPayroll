
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi.testclient import TestClient


# Locate project folders
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PAYROLL_API_FOLDER = PROJECT_ROOT / "payroll-api"

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")

# Allow Python to import main.py from payroll-api
sys.path.insert(0, str(PAYROLL_API_FOLDER))

from main import app


client = TestClient(app)

API_KEY = os.getenv("PAYROLL_API_KEY")


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_missing_api_key():
    response = client.get("/payroll/employees")

    assert response.status_code == 422


def test_invalid_api_key():
    response = client.get(
        "/payroll/employees",
        headers={"X-API-Key": "incorrect-key"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API key"


def test_valid_api_key():
    assert API_KEY, "PAYROLL_API_KEY is missing from .env"

    response = client.get(
        "/payroll/employees",
        headers={"X-API-Key": API_KEY}
    )

    assert response.status_code == 200
    assert "total_employees" in response.json()
    assert "employees" in response.json()
