"""
Debug log widget for displaying debug messages.
"""

import logging
from typing import List
from textual.app import ComposeResult
from textual.widgets import RichLog
from textual.widget import Widget
from rich.text import Text
from ..log import get_logger, setup_logger


class DebugLogHandler(logging.Handler):
    """Custom logging handler that sends logs to a debug widget."""

    def __init__(self, widget: "DebugLog"):
        super().__init__()
        self.widget = widget

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to the widget."""
        try:
            msg = self.format(record)
            self.widget.add_log(msg, record.levelname)
        except (AttributeError, ValueError, TypeError):
            # Don't let logging errors crash the app
            # AttributeError: widget is None or missing methods
            # ValueError: invalid formatting
            # TypeError: type mismatch in formatting
            pass


class DebugLog(Widget):
    """Widget that displays debug log messages."""

    DEFAULT_CSS = """
    DebugLog {
        background: black;
        color: white;
        border: solid white;
        height: 10;
        min-height: 5;
    }

    DebugLog > RichLog {
        background: black;
        color: white;
        border: none;
        padding: 0;
        margin: 0;
    }
    """

    def __init__(self, max_lines: int = 100, **kwargs):
        """Initialize the debug log widget.

        Args:
            max_lines: Maximum number of log lines to keep in memory
            **kwargs: Additional widget arguments
        """
        super().__init__(**kwargs)
        self.max_lines = max_lines
        self.log_lines: List[str] = []
        self.rich_log = None
        self.handler = None

    def compose(self) -> ComposeResult:
        """Compose the debug log widget."""
        self.rich_log = RichLog(
            highlight=True,
            markup=True,
            wrap=True,
            auto_scroll=True,
        )
        yield self.rich_log

    def on_mount(self) -> None:
        """Set up the debug log handler when mounted."""
        setup_logger()

        # Set up handler to capture logs
        self.handler = DebugLogHandler(self)
        formatter = logging.Formatter("%(levelname)s: %(message)s")
        self.handler.setFormatter(formatter)

        # Add handler to the logger
        logger = get_logger()
        logger.addHandler(self.handler)

    def on_unmount(self) -> None:
        """Clean up the debug log handler when unmounted."""
        if self.handler:
            logger = get_logger()
            logger.removeHandler(self.handler)

    def add_log(self, message: str, level: str = "INFO") -> None:
        """Add a log message to the widget.

        Args:
            message: The log message to add
            level: The log level (DEBUG, INFO, WARNING, ERROR, etc.)
        """
        if self.rich_log is None:
            return

        # Create colored text based on log level
        colored_message = self._colorize_message(message, level)
        self.log_lines.append(colored_message)

        # Keep only the last max_lines to prevent memory bloat
        if len(self.log_lines) > self.max_lines:
            self.log_lines = self.log_lines[-self.max_lines :]

        # Update display by clearing and re-rendering all lines
        self.rich_log.clear()
        for line in self.log_lines:
            self.rich_log.write(line)

    def _colorize_message(self, message: str, level: str) -> Text:
        """Apply color formatting to log messages based on level.

        Args:
            message: The log message
            level: The log level

        Returns:
            Rich Text object with appropriate styling
        """
        text = Text(message)

        # Apply colors based on log level
        if level == "DEBUG":
            text.stylize("dim cyan")
        elif level == "INFO":
            text.stylize("white")
        elif level == "WARNING":
            text.stylize("yellow")
        elif level == "ERROR":
            text.stylize("red")
        elif level == "CRITICAL":
            text.stylize("bold red")
        else:
            text.stylize("white")

        return text
