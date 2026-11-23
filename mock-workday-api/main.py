
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_FILE = PROJECT_ROOT / "sample-data" / "employee.json"

app = FastAPI(
    title="Mock Workday HCM API",
    description="Simulated Workday worker API for integration development",
    version="1.0.0"
)


def load_workers():
    try:
        with open(SOURCE_FILE, "r", encoding="utf-8") as file:
            workers = json.load(file)

        if not isinstance(workers, list):
            raise ValueError("Employee source must contain a JSON list")

        return workers

    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="Employee source file not found"
        )

    except (json.JSONDecodeError, ValueError):
        raise HTTPException(
            status_code=500,
            detail="Invalid employee source data"
        )


@app.get("/health")
def health_check():
    return {
        "status": "running",
        "application": "Mock Workday HCM API"
    }


@app.get("/workers")
def get_workers(
    limit: int = Query(default=2, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    workers = load_workers()

    paginated_workers = workers[offset:offset + limit]

    return {
        "data": paginated_workers,
        "total": len(workers),
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < len(workers)
    }
