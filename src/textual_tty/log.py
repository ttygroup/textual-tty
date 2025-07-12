"""
Logging utilities for textual-terminal.
"""

import logging
import functools
import time
import threading
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Any, Dict
from dataclasses import dataclass, field

# Global logger instance
logger: Optional[logging.Logger] = None


def setup_logger(name: str = "textual_tty", log_dir: Path = Path("logs"), level: int = logging.DEBUG) -> logging.Logger:
    """Set up a global logger."""
    global logger

    if logger is None:
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Ensure log directory exists
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "debug.log"

        # Create file handler
        file_handler = logging.FileHandler(log_file, mode="a")
        file_handler.setLevel(level)

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


@dataclass
class PerformanceMetrics:
    """Track performance metrics for PTY operations."""

    bytes_in: int = 0
    bytes_out: int = 0
    calls_in: int = 0
    calls_out: int = 0
    time_in: float = 0.0
    time_out: float = 0.0
    start_time: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary with calculated rates."""
        elapsed = time.time() - self.start_time
        return {
            "elapsed_seconds": elapsed,
            "bytes_in": self.bytes_in,
            "bytes_out": self.bytes_out,
            "calls_in": self.calls_in,
            "calls_out": self.calls_out,
            "time_in": self.time_in,
            "time_out": self.time_out,
            "bytes_in_per_sec": self.bytes_in / elapsed if elapsed > 0 else 0,
            "bytes_out_per_sec": self.bytes_out / elapsed if elapsed > 0 else 0,
            "calls_in_per_sec": self.calls_in / elapsed if elapsed > 0 else 0,
            "calls_out_per_sec": self.calls_out / elapsed if elapsed > 0 else 0,
        }


class PerformanceTracker:
    """Track and log performance metrics."""

    def __init__(self, log_interval: float = 5.0):
        """Initialize the performance tracker.

        Args:
            log_interval: How often to write metrics to disk (seconds)
        """
        self.enabled = False
        self.log_interval = log_interval
        self.metrics: Dict[str, PerformanceMetrics] = {}
        self.lock = threading.Lock()
        self.log_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.log_file: Optional[Path] = None

    def enable(self, log_dir: Path = Path("logs")) -> None:
        """Enable performance tracking."""
        self.enabled = True
        log_dir.mkdir(exist_ok=True)

        # Create timestamped log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = log_dir / f"performance_{timestamp}.jsonl"

        # Start logging thread
        self.stop_event.clear()
        self.log_thread = threading.Thread(target=self._log_loop, daemon=True)
        self.log_thread.start()

        info(f"Performance tracking enabled, logging to {self.log_file}")

    def disable(self) -> None:
        """Disable performance tracking."""
        self.enabled = False
        if self.log_thread:
            self.stop_event.set()
            self.log_thread.join(timeout=1.0)
            self.log_thread = None

        # Write final metrics
        if self.log_file:
            self._write_metrics()

        info("Performance tracking disabled")

    def get_metrics(self, name: str) -> PerformanceMetrics:
        """Get or create metrics for a named component."""
        with self.lock:
            if name not in self.metrics:
                self.metrics[name] = PerformanceMetrics()
            return self.metrics[name]

    def _log_loop(self) -> None:
        """Background thread that periodically writes metrics."""
        while not self.stop_event.is_set():
            if self.stop_event.wait(self.log_interval):
                break
            self._write_metrics()

    def _write_metrics(self) -> None:
        """Write current metrics to log file."""
        if not self.log_file:
            return

        with self.lock:
            # Create snapshot of all metrics
            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "metrics": {name: metrics.to_dict() for name, metrics in self.metrics.items()},
            }

        # Append to JSONL file
        with open(self.log_file, "a") as f:
            f.write(json.dumps(snapshot) + "\n")
            f.flush()


# Global performance tracker instance
_performance_tracker = PerformanceTracker()


def get_performance_tracker() -> PerformanceTracker:
    """Get the global performance tracker."""
    return _performance_tracker


def measure_performance(component: str):
    """Decorator to measure performance of any method.

    Args:
        component: Name of the component/method being measured
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            tracker = get_performance_tracker()
            if not tracker.enabled:
                return func(*args, **kwargs)

            metrics = tracker.get_metrics(f"{component}.{func.__name__}")
            start_time = time.time()

            try:
                result = func(*args, **kwargs)

                # Update metrics
                elapsed = time.time() - start_time
                metrics.calls_in += 1
                metrics.time_in += elapsed

                # Try to get length of result if possible
                try:
                    metrics.bytes_in += len(result)
                except (TypeError, AttributeError):
                    # Result doesn't support len(), that's fine
                    pass

                return result
            except Exception:
                raise

        return wrapper

    return decorator
