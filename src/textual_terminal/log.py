"""
Logging utilities for textual-terminal.
"""

import logging
from typing import Optional

# Global logger instance
logger: Optional[logging.Logger] = None


def setup_logger(name: str = "textual_terminal") -> logging.Logger:
    """Set up a global logger."""
    global logger

    if logger is None:
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        # Create file handler only
        file_handler = logging.FileHandler("debug.log", mode="w")
        file_handler.setLevel(logging.DEBUG)

        # Create formatter
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(file_handler)

    return logger


def get_logger() -> logging.Logger:
    """Get the global logger, creating it if necessary."""
    if logger is None:
        return setup_logger()
    return logger


# Convenience functions
def debug(msg: str) -> None:
    """Log a debug message."""
    get_logger().debug(msg)


def info(msg: str) -> None:
    """Log an info message."""
    get_logger().info(msg)


def warning(msg: str) -> None:
    """Log a warning message."""
    get_logger().warning(msg)


def error(msg: str) -> None:
    """Log an error message."""
    get_logger().error(msg)
