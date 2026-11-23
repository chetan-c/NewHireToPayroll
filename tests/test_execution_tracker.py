
import sys
import uuid
from pathlib import Path

# Add the project root to Python's import path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from integration.execution_tracker import (
    start_execution,
    finish_execution
)


def test_execution_tracking():

    execution_id = str(uuid.uuid4())

    print("Starting execution tracking test...")

    start_execution(execution_id)

    finish_execution(
        execution_id=execution_id,
        final_status="SUCCESS",
        total_records=1,
        success_count=1,
        failure_count=0,
        duplicate_count=0,
        retry_count=0,
        message="Test execution completed successfully"
    )

    print("Execution tracking test completed!")
    print("Execution ID:", execution_id)


if __name__ == "__main__":
    test_execution_tracking()
