"""DebugLog: a RichLog fed by stdlib logging.

Attach it anywhere in an app to watch textual_tty and bittty log records live.
"""

from __future__ import annotations

import logging

from textual.widgets import RichLog

_WATCHED_LOGGERS = ("textual_tty", "bittty")


class _WidgetHandler(logging.Handler):
    """Forward log records into the widget."""

    def __init__(self, widget: DebugLog) -> None:
        super().__init__()
        self.widget = widget
        self.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(name)s %(message)s", datefmt="%H:%M:%S"))

    def emit(self, record: logging.LogRecord) -> None:
        self.widget.write(self.format(record))


class DebugLog(RichLog):
    """Displays textual_tty and bittty log output."""

    DEFAULT_CSS = """
    DebugLog {
        background: $surface;
    }
    """

    def __init__(self, level: int = logging.DEBUG, **kwargs) -> None:
        super().__init__(markup=False, highlight=False, wrap=True, **kwargs)
        self._handler = _WidgetHandler(self)
        self._level = level

    def on_mount(self) -> None:
        for name in _WATCHED_LOGGERS:
            logger = logging.getLogger(name)
            logger.setLevel(self._level)
            logger.addHandler(self._handler)

    def on_unmount(self) -> None:
        for name in _WATCHED_LOGGERS:
            logging.getLogger(name).removeHandler(self._handler)
