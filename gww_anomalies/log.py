"""Set up consistent logging across application."""
import logging
import sys


def setup_log(logger_name: str) -> logging.Logger:
    """Set up logging."""
    logger = logging.getLogger(logger_name)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.INFO)
    return logger
