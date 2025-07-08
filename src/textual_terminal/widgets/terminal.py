"""
Terminal widget for Textual applications.

This module provides the main Terminal widget that can be embedded in Textual apps
to provide terminal emulation capabilities.
"""

from __future__ import annotations

import asyncio
import subprocess
from typing import Any, Optional

from textual.app import ComposeResult
from textual.widgets import RichLog
from textual.widget import Widget
from textual.reactive import reactive
from textual.message import Message

from ..screen import TerminalScreen
from ..parser import Parser
from ..pty import create_pty
from ..log import info, warning, error


class Terminal(Widget):
    """A terminal emulator widget that can run shell commands."""

    DEFAULT_CSS = """
    Terminal {
        background: black;
        color: white;
        scrollbar-gutter: stable;
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
        await self._stop_process()

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
            self._read_task = asyncio.create_task(self._read_from_pty())

        except Exception as e:
            error(f"Failed to start terminal process: {e}")
            await self._stop_process()

    async def _stop_process(self) -> None:
        """Stop the child process and clean up."""
        # Cancel read task
        if self._read_task and not self._read_task.done():
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass

        # Terminate process
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                await asyncio.sleep(0.1)
                if self.process.poll() is None:
                    self.process.kill()
            except ProcessLookupError:
                pass

        # Close PTY
        if self.pty is not None:
            self.pty.close()
            self.pty = None

        self.process = None

    def _set_terminal_size(self) -> None:
        """Set the terminal window size."""
        if self.pty is not None:
            info(f"Setting PTY size to {self.height_chars}x{self.width_chars}")
            # PTY resize should automatically send SIGWINCH to the process
            self.pty.resize(self.height_chars, self.width_chars)
        else:
            warning("No PTY available, cannot resize")

    async def _read_from_pty(self) -> None:
        """Read data from the PTY and process it."""
        try:
            while self.pty is not None and not self.pty.closed:
                # Use asyncio to read without blocking
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, self._read_pty_data)

                if not data:
                    warning("Read returned empty data, process may have exited")
                    break

                # Process the data through the parser
                self.parser.feed(data)

                # Update the display
                await self._update_display()

        except Exception as e:
            error(f"Error reading from terminal: {e}")
        finally:
            # Process has exited
            if self.process:
                exit_code = self.process.poll()
                info(f"Process exited with code: {exit_code}")
                if exit_code is None:
                    exit_code = 0
                self.post_message(self.ProcessExited(exit_code))

    def _read_pty_data(self) -> bytes:
        """Read from PTY (blocking operation for executor)."""
        if self.pty is None:
            return b""

        try:
            return self.pty.read(4096)
        except OSError:
            # PTY is closed, process has exited
            return b""

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
        # Convert Textual key events to terminal input
        key_data = self._convert_key_event(event)
        if key_data:
            self.write(key_data)

    def _convert_key_event(self, event) -> Optional[bytes]:
        """Convert Textual key event to terminal input bytes."""
        # Basic key mapping - expand this as needed
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

        # Handle special keys
        if event.key in key_map:
            return key_map[event.key]

        # Handle printable characters
        if len(event.key) == 1:
            char = event.key

            # Handle Ctrl combinations
            if hasattr(event, "ctrl") and event.ctrl:
                if "a" <= char <= "z":
                    return bytes([ord(char) - ord("a") + 1])
                elif "A" <= char <= "Z":
                    return bytes([ord(char) - ord("A") + 1])

            # Regular character
            return char.encode("utf-8")

        return None

    def on_resize(self, event) -> None:
        """Handle terminal resize."""
        info(f"Terminal resize event: {event.size.width}x{event.size.height}")

        # Calculate new character dimensions based on available space
        # This is a simplified calculation - you might want to use font metrics
        new_width = max(20, min(200, event.size.width // 8))  # Rough char width
        new_height = max(5, min(100, event.size.height // 16))  # Rough char height

        info(f"Calculated terminal size: {new_width}x{new_height} chars")

        if new_width != self.width_chars or new_height != self.height_chars:
            info(f"Terminal resize: {self.width_chars}x{self.height_chars} -> {new_width}x{new_height}")
            self.width_chars = new_width
            self.height_chars = new_height
            self.terminal_screen.resize(new_width, new_height)
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
