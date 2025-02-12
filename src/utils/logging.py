import logging
import sys
from typing import Optional


def setup_logger(
    name: str = "notion_discord_bot", level: Optional[int] = None
) -> logging.Logger:
    """Configure and return a logger instance"""
    logger = logging.getLogger(name)

    # Set log level
    logger.setLevel(level or logging.INFO)

    # Create console handler if none exists
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(console_handler)

    return logger


# Create default logger instance
logger = setup_logger()
