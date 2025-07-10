"""
Logging utilities for textual-terminal.
"""

import logging
import functools
from typing import Optional, Callable, Any

# Global logger instance
logger: Optional[logging.Logger] = None


def setup_logger(name: str = "textual_tty") -> logging.Logger:
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


def exception(msg: str) -> None:
    """Log an exception message with traceback."""
    get_logger().exception(msg)


def trace_calls(func: Callable) -> Callable:
    """Decorator to trace function calls with arguments and return values."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        # Format arguments nicely
        arg_strs = []
        if args:
            arg_strs.extend([repr(arg) for arg in args[1:]])  # Skip 'self'
        if kwargs:
            arg_strs.extend([f"{k}={repr(v)}" for k, v in kwargs.items()])

        args_str = ", ".join(arg_strs) if arg_strs else ""
        class_name = args[0].__class__.__name__ if args else ""
        func_name = f"{class_name}.{func.__name__}" if class_name else func.__name__

        # Write to separate trace log to avoid UI lag
        _trace_log(f"CALL {func_name}({args_str})")

        try:
            result = func(*args, **kwargs)
            _trace_log(f"RETURN {func_name} -> {repr(result) if result is not None else 'None'}")
            return result
        except Exception as e:
            _trace_log(f"EXCEPTION {func_name} -> {type(e).__name__}: {e}")
            raise

    return wrapper


def _trace_log(msg: str) -> None:
    """Log trace messages to separate file."""
    import datetime

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
    with open("trace.log", "a") as f:
        f.write(f"{timestamp} - TRACE - {msg}\n")
        f.flush()
