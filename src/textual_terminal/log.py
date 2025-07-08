"""
Debug logging utilities for textual-terminal.
"""

import logging
import sys
from typing import Optional

# Global logger instance
debug_logger: Optional[logging.Logger] = None


def setup_debug_logger(name: str = "textual_terminal") -> logging.Logger:
    """Set up a global debug logger."""
    global debug_logger

    if debug_logger is None:
        debug_logger = logging.getLogger(name)
        debug_logger.setLevel(logging.DEBUG)

        # Create handler that writes to stderr
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(logging.DEBUG)

        # Create formatter
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)

        # Add handler to logger
        debug_logger.addHandler(handler)

    return debug_logger


def get_debug_logger() -> logging.Logger:
    """Get the global debug logger, creating it if necessary."""
    if debug_logger is None:
        return setup_debug_logger()
    return debug_logger


# Convenience functions
def debug(msg: str) -> None:
    """Log a debug message."""
    get_debug_logger().debug(msg)


def info(msg: str) -> None:
    """Log an info message."""
    get_debug_logger().info(msg)


def warning(msg: str) -> None:
    """Log a warning message."""
    get_debug_logger().warning(msg)


def error(msg: str) -> None:
    """Log an error message."""
    get_debug_logger().error(msg)
