"""
TextualTerminal: Textual widget that provides terminal emulation.

This module provides the TextualTerminal widget that combines the base
Terminal class with Textual's reactive system and UI components.
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

from textual.app import ComposeResult
from textual.widgets import RichLog
from textual.widget import Widget
from textual.reactive import reactive
from textual.message import Message

from .terminal import Terminal


class TextualTerminal(Terminal, Widget):
    """A terminal emulator widget for Textual applications."""

    # Make terminal focusable so it can receive key events
    can_focus = True

    DEFAULT_CSS = """
    TextualTerminal {
        background: black;
        color: white;
    }

    TextualTerminal > RichLog {
        background: black;
        color: white;
        border: none;
        padding: 0;
        margin: 0;
    }
    """

    # Override Terminal attributes as reactive
    title: str = reactive("Terminal", always_update=True)
    cursor_x: int = reactive(0, always_update=True)
    cursor_y: int = reactive(0, always_update=True)
    width: int = reactive(80, always_update=True)
    height: int = reactive(24, always_update=True)

    # Terminal widget specific attributes
    command: str = reactive("/bin/bash", always_update=True)
    width_chars: int = reactive(80, always_update=True)
    height_chars: int = reactive(24, always_update=True)

    def __init__(
        self,
        command: str = "/bin/bash",
        width: int = 80,
        height: int = 24,
        **kwargs: Any,
    ) -> None:
        """Initialize the terminal widget."""
        # Initialize Widget first
        Widget.__init__(self, **kwargs)

        # Then initialize Terminal
        Terminal.__init__(self, command, width, height)

        # Set reactive values
        self.command = command
        self.width_chars = width
        self.height_chars = height

        # RichLog widget for display
        self.rich_log: Optional[RichLog] = None

    # Message classes for events
    class TitleChanged(Message):
        """Posted when terminal title changes."""

        def __init__(self, title: str) -> None:
            self.title = title
            super().__init__()

    class ProcessExited(Message):
        """Posted when terminal process exits."""

        def __init__(self, exit_code: int) -> None:
            self.exit_code = exit_code
            super().__init__()

    class Bell(Message):
        """Posted when terminal bell is triggered."""

        pass

    def compose(self) -> ComposeResult:
        """Compose the terminal widget."""
        self.rich_log = RichLog(
            highlight=False,
            markup=False,
            wrap=False,
            auto_scroll=False,
        )
        yield self.rich_log

    async def on_mount(self) -> None:
        """Handle widget mounting."""
        await self.start_process()

    async def on_unmount(self) -> None:
        """Handle widget unmounting."""
        self.stop_process()

    def _read_from_pty(self) -> None:
        """Override to add display update."""
        # Call parent method
        super()._read_from_pty()

        # Update display asynchronously
        asyncio.create_task(self._update_display())

    async def _update_display(self) -> None:
        """Update the RichLog display with current screen content."""
        if self.rich_log is None:
            return

        # Get the current screen content as Rich renderables
        content = self.get_content()

        # Clear and update the display
        self.rich_log.clear()
        for line in content:
            self.rich_log.write(line)

    def stop_process(self) -> None:
        """Override to post message when process exits."""
        # Call parent method
        super().stop_process()

        # Post exit message
        if self.process:
            exit_code = self.process.poll() or 0
            self.post_message(self.ProcessExited(exit_code))

    def bell(self) -> None:
        """Override to post bell message."""
        self.post_message(self.Bell())

    def set_title(self, title: str) -> None:
        """Override to trigger reactive update."""
        # Update the reactive attribute (this will trigger watchers)
        self.title = title

    # Reactive watchers
    def watch_title(self, old_title: str, new_title: str) -> None:
        """Called when title changes."""
        self.post_message(self.TitleChanged(new_title))

    def watch_width_chars(self, old_width: int, new_width: int) -> None:
        """Called when width changes."""
        self.resize(new_width, self.height_chars)

    def watch_height_chars(self, old_height: int, new_height: int) -> None:
        """Called when height changes."""
        self.resize(self.width_chars, new_height)

    def _set_terminal_size(self) -> None:
        """Set the terminal window size."""
        if self.pty is not None:
            self.pty.resize(self.height_chars, self.width_chars)

    # Input handling (future implementation)
    async def on_key(self, event) -> None:
        """Handle key events."""
        # TODO: Send key events to PTY
        pass
