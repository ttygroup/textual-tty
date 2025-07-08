"""
Terminal widget for Textual applications.

This module provides the main Terminal widget that can be embedded in Textual apps
to provide terminal emulation capabilities.
"""

from __future__ import annotations

import os
import asyncio
import subprocess
import time
from typing import Any, Optional

from textual.app import ComposeResult
from textual.widgets import RichLog
from textual.widget import Widget
from textual.reactive import reactive
from textual.message import Message

from ..screen import TerminalScreen
from ..parser import Parser
from ..pty_handler import create_pty
from ..log import info, warning, error


class Terminal(Widget):
    """A terminal emulator widget that can run shell commands."""

    # Make terminal focusable so it can receive key events
    can_focus = True

    DEFAULT_CSS = """
    Terminal {
        background: black;
        color: white;
    }

    Terminal > RichLog {
        background: black;
        color: white;
        border: none;
        padding: 0;
        margin: 0;
    }
    """

    # Reactive attributes
    command = reactive("/bin/bash", always_update=True)
    width_chars = reactive(80, always_update=True)
    height_chars = reactive(24, always_update=True)

    class ProcessExited(Message):
        """Message sent when the child process exits."""

        def __init__(self, exit_code: int) -> None:
            self.exit_code = exit_code
            super().__init__()

    def __init__(
        self,
        command: str = "/bin/bash",
        width: int = 80,
        height: int = 24,
        **kwargs: Any,
    ) -> None:
        """Initialize the terminal widget.

        Args:
            command: The command to run in the terminal
            width: Terminal width in characters
            height: Terminal height in characters
        """
        super().__init__(**kwargs)

        self.command = command
        self.width_chars = width
        self.height_chars = height

        # Terminal state
        self.terminal_screen = TerminalScreen(width, height)
        self.parser = Parser(self.terminal_screen)

        # PTY management
        self.process: Optional[subprocess.Popen] = None
        self.pty: Optional[Any] = None

        # RichLog widget for display
        self.rich_log: Optional[RichLog] = None

        # Background tasks
        self._read_task: Optional[asyncio.Task] = None

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
        await self._start_process()

    async def on_unmount(self) -> None:
        """Handle widget unmounting."""
        self._stop_process()

    async def _start_process(self) -> None:
        """Start the child process with PTY."""
        try:
            info(f"Starting terminal process: {self.command}")

            # Create PTY socket
            self.pty = create_pty(self.height_chars, self.width_chars)
            info(f"Created PTY: {self.width_chars}x{self.height_chars}")

            # Spawn process attached to PTY
            self.process = self.pty.spawn_process(self.command)
            info(f"Spawned process: pid={self.process.pid}")

            # Start reading from PTY
            loop = asyncio.get_event_loop()
            loop.add_reader(self.pty.master_fd, self._read_from_pty)

        except Exception as e:
            error(f"Failed to start terminal process: {e}")
            self._stop_process()

    def _stop_process(self) -> None:
        """Stop the child process and clean up."""
        # Prevent multiple calls
        if self.pty is None and self.process is None:
            return

        # Remove PTY reader
        if self.pty and self.pty.master_fd:
            try:
                loop = asyncio.get_event_loop()
                loop.remove_reader(self.pty.master_fd)
            except (ValueError, OSError):
                pass  # Reader may already be removed

        # Close PTY to break the read loop and trigger SIGHUP
        if self.pty is not None:
            self.pty.close()
            self.pty = None

        # Post exit message if process was running
        if self.process:
            # Give the process a moment to exit after PTY close (kernel sends SIGHUP)
            exit_code = self.process.poll()
            if exit_code is None:
                # Wait briefly for process to handle SIGHUP
                time.sleep(0.1)
                exit_code = self.process.poll()

            info(f"Process exited with code: {exit_code}")
            if exit_code is None:
                info("Process did not exit after PTY close (may be disowned/nohup)")
                exit_code = 0
            self.post_message(self.ProcessExited(exit_code))

        self.process = None

    def _set_terminal_size(self) -> None:
        """Set the terminal window size."""
        if self.pty is not None:
            info(f"Setting PTY size to {self.height_chars}x{self.width_chars}")
            # PTY resize should automatically send SIGWINCH to the process
            self.pty.resize(self.height_chars, self.width_chars)
        else:
            warning("No PTY available, cannot resize")

    def _read_from_pty(self) -> None:
        """Read data from the PTY and process it."""
        if self.pty is None or self.pty.closed:
            return

        try:
            data = os.read(self.pty.master_fd, 4096)
            if not data:
                warning("Read returned empty data, process may have exited")
                self._stop_process()
                return

            # Decode UTF-8 - Python's C implementation is very fast
            text = data.decode("utf-8", errors="replace")

            # Process the text through the parser
            self.parser.feed(text)

            # Update the display
            asyncio.create_task(self._update_display())

        except OSError as e:
            # PTY is closed, process has exited
            info(f"PTY read error: {e}")
            self._stop_process()
        except Exception as e:
            error(f"Error reading from terminal: {e}")
            self._stop_process()

    async def _update_display(self) -> None:
        """Update the RichLog display with current screen content."""
        if self.rich_log is None:
            return

        # Get the current screen content as Rich renderables
        content = self.terminal_screen.get_content()

        # Clear and update the display
        self.rich_log.clear()
        for line in content:
            self.rich_log.write(line)

    def write(self, data: str | bytes) -> None:
        """Write data to the terminal input."""
        if self.pty is None:
            return

        if isinstance(data, str):
            data = data.encode("utf-8")

        bytes_written = self.pty.write(data)
        if bytes_written == 0:
            error("Failed to write to terminal")

    async def on_key(self, event) -> None:
        """Handle key events and send to terminal."""
        # Let Ctrl+Q bubble up to app level immediately
        if hasattr(event, "ctrl") and event.ctrl and event.key == "q":
            return

        # Convert Textual key events to terminal input
        key_data = self._convert_key_event(event)
        if key_data:
            self.write(key_data)
            # Prevent further processing of this key
            event.prevent_default()
            event.stop()

    def _convert_key_event(self, event) -> Optional[bytes]:
        """Convert Textual key event to terminal input bytes."""

        # Handle Ctrl combinations first (including Ctrl+C)
        if hasattr(event, "ctrl") and event.ctrl:
            if event.key == "c":
                return b"\x03"  # Ctrl+C (SIGINT)
            elif event.key == "d":
                return b"\x04"  # Ctrl+D (EOF)
            elif event.key == "z":
                return b"\x1a"  # Ctrl+Z (SIGTSTP)
            elif event.key == "q":
                return None  # Don't capture Ctrl+Q, let app handle it
            elif len(event.key) == 1:
                char = event.key.lower()
                if "a" <= char <= "z":
                    return bytes([ord(char) - ord("a") + 1])

        # Use event.character if available (for printable characters)
        if hasattr(event, "character") and event.character:
            return event.character.encode("utf-8")

        # Fall back to key mapping for special keys
        key_map = {
            "enter": b"\r",
            "backspace": b"\x7f",
            "tab": b"\t",
            "escape": b"\x1b",
            "up": b"\x1b[A",
            "down": b"\x1b[B",
            "right": b"\x1b[C",
            "left": b"\x1b[D",
            "home": b"\x1b[H",
            "end": b"\x1b[F",
            "page_up": b"\x1b[5~",
            "page_down": b"\x1b[6~",
            "delete": b"\x1b[3~",
            "insert": b"\x1b[2~",
        }

        return key_map.get(event.key)

    def on_resize(self, event) -> None:
        """Handle terminal resize."""
        info(f"Terminal resize event: {event.size.width}x{event.size.height}")

        # Log RichLog size if available
        if self.rich_log:
            info(f"RichLog size: {self.rich_log.size}")

        # Use RichLog size if available (it's already in characters)
        if self.rich_log:
            new_width = self.rich_log.size.width
            new_height = self.rich_log.size.height
        else:
            # Fallback to event size
            new_width = event.size.width
            new_height = event.size.height

        info(f"Calculated terminal size: {new_width}x{new_height} chars")
        info(f"TerminalScreen current size: {self.terminal_screen.width}x{self.terminal_screen.height}")

        if new_width != self.width_chars or new_height != self.height_chars:
            info(f"Terminal resize: {self.width_chars}x{self.height_chars} -> {new_width}x{new_height}")
            self.width_chars = new_width
            self.height_chars = new_height
            self.terminal_screen.resize(new_width, new_height)
            info(f"TerminalScreen after resize: {self.terminal_screen.width}x{self.terminal_screen.height}")
            self._set_terminal_size()

    def terminate(self) -> None:
        """Terminate the running process."""
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
            except ProcessLookupError:
                pass

    def kill(self) -> None:
        """Force kill the running process."""
        if self.process and self.process.poll() is None:
            try:
                self.process.kill()
            except ProcessLookupError:
                pass
