
import logging
from pathlib import Path

# Locate the project directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Create a logs folder
LOG_FOLDER = PROJECT_ROOT / "logs"
LOG_FOLDER.mkdir(exist_ok=True)

# Define the log file
LOG_FILE = LOG_FOLDER / "integration.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("NewHireToPayroll")
