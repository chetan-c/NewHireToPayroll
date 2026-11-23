
from logger_config import logger


def notify_support(worker_code, message):
    """
    Generate a support alert when an integration fails.

    This local implementation writes the alert to the
    console and integration log file.
    """

    logger.error("----------------------------------------")
    logger.error("SUPPORT ALERT")
    logger.error("Integration: NewHireToPayroll")
    logger.error("Employee ID: %s", worker_code)
    logger.error("Failure Details: %s", message)
    logger.error("Action Required: Please investigate.")
    logger.error("----------------------------------------")
