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
from typing import Any, Optional, Callable

from .buffer import Buffer
from .parser import Parser
from .pty_handler import create_pty
from .log import info, warning, exception

from rich.text import Text
from rich.style import Style


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
        self.mouse_button_tracking = False
        self.mouse_any_tracking = False
        self.mouse_sgr_mode = False
        self.mouse_extended_mode = False

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

        # Last printed character (for REP command)
        self.last_printed_char = " "

        # Saved cursor state (for DECSC/DECRC)
        self.saved_cursor_x = 0
        self.saved_cursor_y = 0
        self.saved_style = None

        # Process management
        self.process: Optional[subprocess.Popen] = None
        self.pty: Optional[Any] = None
        self._pty_reader_task: Optional[asyncio.Task] = None

        # PTY data callback for async handling
        self._pty_data_callback: Optional[Callable[[bytes], None]] = None

        # Parser
        self.parser = Parser(self)

    def set_pty_data_callback(self, callback: Callable[[bytes], None]) -> None:
        """Set callback for handling PTY data asynchronously."""
        self._pty_data_callback = callback

    def _process_pty_data_sync(self, data: bytes) -> None:
        """Process PTY data synchronously (fallback)."""
        text = data.decode("utf-8", errors="replace")
        self.parser.feed(text)

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

        # Move cursor forward by character count
        if self.auto_wrap or self.cursor_x < self.width - 1:
            self.cursor_x += len(text)

        # Remember last character for REP command
        if text:
            self.last_printed_char = text[-1]

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
            self.scroll_up(1)
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
            # Clear current line from cursor to end, padding to full width
            if 0 <= self.cursor_y < len(self.current_buffer.lines):
                line = self.current_buffer.lines[self.cursor_y]
                if self.cursor_x < len(line.plain):
                    # Keep text before cursor, fill rest with spaces to full width
                    kept_part = line[: self.cursor_x]
                    spaces_needed = self.width - self.cursor_x
                    if spaces_needed > 0:
                        spaces = Text(" " * spaces_needed)
                        self.current_buffer.lines[self.cursor_y] = kept_part + spaces
                    else:
                        self.current_buffer.lines[self.cursor_y] = kept_part
            # Clear all lines below cursor
            for y in range(self.cursor_y + 1, min(self.height, len(self.current_buffer.lines))):
                self.current_buffer.lines[y] = Text()
        elif mode == 1:  # Clear from beginning of screen to cursor
            # Clear all lines above cursor
            for y in range(min(self.cursor_y, len(self.current_buffer.lines))):
                self.current_buffer.lines[y] = Text()
            # Clear current line from beginning to cursor
            self.clear_line(1)
        elif mode == 2:  # Clear entire screen
            self.current_buffer = Buffer(self.width, self.height)

    def clear_line(self, mode: int = 0) -> None:
        """Clear line."""
        self.current_buffer.clear_line(self.cursor_y, mode, self.cursor_x)

    def clear_rect(self, x1: int, y1: int, x2: int, y2: int, style: Optional[Style] = None) -> None:
        """Clear a rectangular region."""
        self.current_buffer.clear_region(x1, y1, x2, y2, style)

    def alternate_screen_on(self) -> None:
        """Switch to alternate screen."""
        self.switch_screen(True)

    def alternate_screen_off(self) -> None:
        """Switch to primary screen."""
        self.switch_screen(False)

    def set_mode(self, mode: int, value: bool = True, private: bool = False) -> None:
        """Set terminal mode."""
        if private:
            # DECSET private modes
            if mode == 7:  # Auto wrap
                self.auto_wrap = value
            elif mode == 25:  # Cursor visibility
                self.cursor_visible = value
            elif mode == 1000:  # Basic mouse tracking
                self.mouse_tracking = value
            elif mode == 1002:  # Button event tracking
                self.mouse_button_tracking = value
            elif mode == 1003:  # Any event tracking (movement)
                self.mouse_any_tracking = value
            elif mode == 1006:  # SGR mouse mode
                self.mouse_sgr_mode = value
            elif mode == 1015:  # Extended mouse mode
                self.mouse_extended_mode = value
            # Add other private modes as needed
        else:
            # ANSI modes
            if mode == 4:  # Insert mode
                self.insert_mode = value
            elif mode == 1:  # Application keypad mode
                self.application_keypad = value
            # Add other ANSI modes as needed

    def clear_mode(self, mode, private: bool = False) -> None:
        """Clear terminal mode."""
        self.set_mode(mode, False, private)

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

    def alignment_test(self) -> None:
        """Fill the screen with 'E' characters for alignment testing."""
        from rich.text import Text

        test_line = Text("E" * self.width)
        for y in range(self.height):
            self.current_buffer.lines[y] = test_line

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
        self.current_buffer.insert(self.cursor_x, self.cursor_y, spaces, Style())

    def delete_characters(self, count: int) -> None:
        """Delete characters at cursor position."""
        if not (0 <= self.cursor_y < self.height):
            return
        self.current_buffer.delete(self.cursor_x, self.cursor_y, count)

    def scroll_up(self, count: int) -> None:
        """Scroll content up within scroll region."""
        for _ in range(count):
            # Remove line at top of scroll region
            if self.scroll_top < len(self.current_buffer.lines):
                self.current_buffer.lines.pop(self.scroll_top)
            # Insert blank line at bottom of scroll region
            self.current_buffer.lines.insert(self.scroll_bottom, Text())
            # Ensure we don't exceed buffer size
            while len(self.current_buffer.lines) > self.height:
                self.current_buffer.lines.pop()

    def scroll_down(self, count: int) -> None:
        """Scroll content down within scroll region."""
        for _ in range(count):
            # Remove line at bottom of scroll region
            if self.scroll_bottom < len(self.current_buffer.lines):
                self.current_buffer.lines.pop(self.scroll_bottom)
            # Insert blank line at top of scroll region
            self.current_buffer.lines.insert(self.scroll_top, Text())
            # Ensure we don't exceed buffer size
            while len(self.current_buffer.lines) > self.height:
                self.current_buffer.lines.pop()

    def set_cursor(self, x: Optional[int], y: Optional[int]) -> None:
        """Set cursor position (alias for move_cursor)."""
        self.move_cursor(x, y)

    def repeat_last_character(self, count: int) -> None:
        """Repeat the last printed character count times (REP command)."""
        if count > 0 and self.last_printed_char:
            repeated_text = self.last_printed_char * count
            self.write_text(repeated_text)

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

            # Start async PTY reader task
            self._pty_reader_task = asyncio.create_task(self._async_read_from_pty())

        except Exception:
            exception("Failed to start terminal process")
            self.stop_process()

    def stop_process(self) -> None:
        """Stop the child process and clean up."""
        if self.pty is None and self.process is None:
            return

        # Cancel PTY reader task
        if self._pty_reader_task and not self._pty_reader_task.done():
            self._pty_reader_task.cancel()
            self._pty_reader_task = None

        # Close PTY
        if self.pty is not None:
            self.pty.close()
            self.pty = None

        self.process = None

    async def _async_read_from_pty(self) -> None:
        """Async task to read PTY data and dispatch to callback or process directly."""
        import fcntl

        # Make PTY non-blocking
        flags = fcntl.fcntl(self.pty.master_fd, fcntl.F_GETFL)
        fcntl.fcntl(self.pty.master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        while self.pty is not None and not self.pty.closed:
            try:
                # Wait for data to be available
                loop = asyncio.get_event_loop()
                ready, _, _ = await loop.run_in_executor(
                    None, lambda: __import__("select").select([self.pty.master_fd], [], [], 0.1)
                )

                if not ready:
                    # No data available, yield and continue
                    await asyncio.sleep(0.01)
                    continue

                # Read available data (non-blocking)
                try:
                    data = os.read(self.pty.master_fd, 4096)
                except BlockingIOError:
                    # No data after all, continue
                    await asyncio.sleep(0.01)
                    continue

                if not data:
                    warning("Read returned empty data, process may have exited")
                    self.stop_process()
                    break

                # Use callback if set, otherwise process directly
                if self._pty_data_callback:
                    self._pty_data_callback(data)
                else:
                    self._process_pty_data_sync(data)

                # Yield control to other async operations (like resize)
                await asyncio.sleep(0)

            except asyncio.CancelledError:
                # Task was cancelled, exit cleanly
                break
            except OSError as e:
                info(f"PTY read error: {e}")
                self.stop_process()
                break
            except Exception:
                exception("Error reading from terminal")
                self.stop_process()
                break
