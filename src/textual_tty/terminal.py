"""
Terminal: Base terminal emulator class.

This module provides the core Terminal class that manages terminal state,
process control, and screen buffers. UI frameworks can subclass this to
create terminal widgets.
"""

from __future__ import annotations

import os
import asyncio
import subprocess
from typing import Any, Optional

from .buffer import Buffer
from .parser import Parser
from .pty_handler import create_pty
from .log import info, warning, error

from rich.text import Text


class Terminal:
    """
    Base terminal emulator with process management and screen buffers.

    This class handles all terminal logic but has no UI dependencies.
    Subclass this to create terminal widgets for specific UI frameworks.
    """

    def __init__(
        self,
        command: str = "/bin/bash",
        width: int = 80,
        height: int = 24,
    ) -> None:
        """Initialize terminal."""
        self.command = command
        self.width = width
        self.height = height

        # Terminal state - these can be made reactive in subclasses
        self.title = "Terminal"
        self.cursor_x = 0
        self.cursor_y = 0
        self.cursor_visible = True

        # Terminal modes
        self.auto_wrap = True
        self.insert_mode = False
        self.application_keypad = False
        self.mouse_tracking = False

        # Screen buffers
        self.primary_buffer = Buffer(width, height)  # With scrollback (future)
        self.alt_buffer = Buffer(width, height)  # No scrollback
        self.current_buffer = self.primary_buffer
        self.in_alt_screen = False

        # Scroll region (top, bottom) - 0-indexed
        self.scroll_top = 0
        self.scroll_bottom = height - 1

        # Character attributes for next write
        self.current_style = None

        # Saved cursor state (for DECSC/DECRC)
        self.saved_cursor_x = 0
        self.saved_cursor_y = 0
        self.saved_style = None

        # Process management
        self.process: Optional[subprocess.Popen] = None
        self.pty: Optional[Any] = None

        # Parser
        self.parser = Parser(self)

    def resize(self, width: int, height: int) -> None:
        """Resize terminal to new dimensions."""
        self.width = width
        self.height = height

        # Resize both buffers
        self.primary_buffer.resize(width, height)
        self.alt_buffer.resize(width, height)

        # Adjust scroll region
        self.scroll_bottom = height - 1

        # Clamp cursor position
        self.cursor_x = min(self.cursor_x, width - 1)
        self.cursor_y = min(self.cursor_y, height - 1)

        # Resize PTY if running
        if self.pty is not None:
            self.pty.resize(height, width)

    def get_content(self):
        """Get current screen content."""
        return self.current_buffer.get_content()

    # Methods called by parser
    def write_text(self, text: str) -> None:
        """Write text at cursor position."""
        # Handle line wrapping or clipping
        if self.cursor_x >= self.width:
            if self.auto_wrap:
                self.line_feed(is_wrapped=True)
                self.cursor_x = 0
            else:
                self.cursor_x = self.width - 1

        # Insert or overwrite based on mode
        if self.insert_mode:
            self.current_buffer.insert(self.cursor_x, self.cursor_y, text, self.current_style)
        else:
            self.current_buffer.set(self.cursor_x, self.cursor_y, text, self.current_style)

        # Move cursor forward
        if self.auto_wrap or self.cursor_x < self.width - 1:
            self.cursor_x += 1

    def move_cursor(self, x: Optional[int], y: Optional[int]) -> None:
        """Move cursor to position."""
        if x is not None:
            self.cursor_x = max(0, min(x, self.width - 1))
        if y is not None:
            self.cursor_y = max(0, min(y, self.height - 1))

    def line_feed(self, is_wrapped: bool = False) -> None:
        """Perform line feed."""
        if self.cursor_y >= self.scroll_bottom:
            # Scroll up within scroll region
            self.current_buffer.scroll_up(1)
        else:
            # Move cursor down
            self.cursor_y += 1

    def carriage_return(self) -> None:
        """Move cursor to beginning of line."""
        self.cursor_x = 0

    def backspace(self) -> None:
        """Move cursor back one position."""
        if self.cursor_x > 0:
            self.cursor_x -= 1
        elif self.cursor_y > 0:
            # Wrap to end of previous line
            self.cursor_y -= 1
            self.cursor_x = self.width - 1

    def clear_screen(self, mode: int = 0) -> None:
        """Clear screen."""
        if mode == 0:  # Clear from cursor to end of screen
            self.current_buffer.clear_region(self.cursor_x, self.cursor_y, self.width, self.height)
        elif mode == 1:  # Clear from beginning of screen to cursor
            self.current_buffer.clear_region(0, 0, self.cursor_x, self.cursor_y)
        elif mode == 2:  # Clear entire screen
            self.current_buffer = Buffer(self.width, self.height)

    def clear_line(self, mode: int = 0) -> None:
        """Clear line."""
        self.current_buffer.clear_line(self.cursor_y, mode)

    def set_mode(self, mode: str, value: bool) -> None:
        """Set terminal mode."""
        if mode == "auto_wrap":
            self.auto_wrap = value
        elif mode == "insert_mode":
            self.insert_mode = value
        elif mode == "cursor_visible":
            self.cursor_visible = value
        elif mode == "application_keypad":
            self.application_keypad = value
        elif mode == "mouse_tracking":
            self.mouse_tracking = value

    def switch_screen(self, alt: bool) -> None:
        """Switch between primary and alternate screen."""
        if alt and not self.in_alt_screen:
            # Switch to alt screen
            self.current_buffer = self.alt_buffer
            self.in_alt_screen = True
        elif not alt and self.in_alt_screen:
            # Switch to primary screen
            self.current_buffer = self.primary_buffer
            self.in_alt_screen = False

    def set_title(self, title: str) -> None:
        """Set terminal title."""
        self.title = title

    def bell(self) -> None:
        """Terminal bell."""
        pass  # Subclasses can override

    def save_cursor(self) -> None:
        """Save cursor position and attributes."""
        self.saved_cursor_x = self.cursor_x
        self.saved_cursor_y = self.cursor_y
        self.saved_style = self.current_style

    def restore_cursor(self) -> None:
        """Restore cursor position and attributes."""
        self.cursor_x = self.saved_cursor_x
        self.cursor_y = self.saved_cursor_y
        self.current_style = self.saved_style

    def set_scroll_region(self, top: int, bottom: int) -> None:
        """Set scroll region."""
        self.scroll_top = max(0, min(top, self.height - 1))
        self.scroll_bottom = max(self.scroll_top, min(bottom, self.height - 1))

    def insert_lines(self, count: int) -> None:
        """Insert blank lines at cursor position."""
        for _ in range(count):
            # Insert blank line at cursor row, shift everything down
            self.current_buffer.lines.insert(self.cursor_y, Text())
            # Remove lines from bottom to maintain screen height
            if len(self.current_buffer.lines) > self.height:
                self.current_buffer.lines.pop()

    def delete_lines(self, count: int) -> None:
        """Delete lines at cursor position."""
        for _ in range(count):
            if self.cursor_y < len(self.current_buffer.lines):
                self.current_buffer.lines.pop(self.cursor_y)
            # Add blank line at bottom
            self.current_buffer.lines.append(Text())

    def insert_characters(self, count: int) -> None:
        """Insert blank characters at cursor position."""
        if not (0 <= self.cursor_y < self.height):
            return
        spaces = " " * count
        self.current_buffer.insert(self.cursor_x, self.cursor_y, spaces)

    def delete_characters(self, count: int) -> None:
        """Delete characters at cursor position."""
        if not (0 <= self.cursor_y < self.height):
            return
        self.current_buffer.delete(self.cursor_x, self.cursor_y, count)

    def scroll_up(self, count: int) -> None:
        """Scroll content up within scroll region."""
        for _ in range(count):
            self.current_buffer.scroll_up(1)

    def scroll_down(self, count: int) -> None:
        """Scroll content down within scroll region."""
        for _ in range(count):
            self.current_buffer.scroll_down(1)

    def set_cursor(self, x: Optional[int], y: Optional[int]) -> None:
        """Set cursor position (alias for move_cursor)."""
        self.move_cursor(x, y)

    # Process management
    async def start_process(self) -> None:
        """Start the child process with PTY."""
        try:
            info(f"Starting terminal process: {self.command}")

            # Create PTY socket
            self.pty = create_pty(self.height, self.width)
            info(f"Created PTY: {self.width}x{self.height}")

            # Spawn process attached to PTY
            self.process = self.pty.spawn_process(self.command)
            info(f"Spawned process: pid={self.process.pid}")

            # Start reading from PTY
            loop = asyncio.get_event_loop()
            loop.add_reader(self.pty.master_fd, self._read_from_pty)

        except Exception as e:
            error(f"Failed to start terminal process: {e}")
            self.stop_process()

    def stop_process(self) -> None:
        """Stop the child process and clean up."""
        if self.pty is None and self.process is None:
            return

        # Remove PTY reader
        if self.pty and self.pty.master_fd:
            try:
                loop = asyncio.get_event_loop()
                loop.remove_reader(self.pty.master_fd)
            except (ValueError, OSError):
                pass

        # Close PTY
        if self.pty is not None:
            self.pty.close()
            self.pty = None

        self.process = None

    def _read_from_pty(self) -> None:
        """Read data from PTY and process it."""
        if self.pty is None or self.pty.closed:
            return

        try:
            data = os.read(self.pty.master_fd, 4096)
            if not data:
                warning("Read returned empty data, process may have exited")
                self.stop_process()
                return

            # Decode UTF-8
            text = data.decode("utf-8", errors="replace")

            # Process through parser
            self.parser.feed(text)

        except OSError as e:
            info(f"PTY read error: {e}")
            self.stop_process()
        except Exception as e:
            error(f"Error reading from terminal: {e}")
            self.stop_process()
