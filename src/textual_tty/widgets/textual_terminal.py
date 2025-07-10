"""
TextualTerminal: Textual widget that provides terminal emulation.

This module provides the TextualTerminal widget that combines the base
Terminal class with Textual's reactive system and UI components.
"""

from __future__ import annotations

from typing import Any, Optional

from textual.app import ComposeResult
from textual.widgets import RichLog
from textual.widget import Widget
from textual.reactive import reactive
from textual.message import Message

from ..terminal import Terminal
from ..log import debug


class TextualTerminal(Terminal, Widget):
    """A terminal emulator widget for Textual applications."""

    # Make terminal focusable so it can receive key events
    can_focus = True

    # Override tab behavior to prevent focus changes
    BINDINGS = [
        ("tab", "pass_to_terminal", ""),
    ]

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

    # Terminal attributes as reactive
    title: str = reactive("Terminal", always_update=True)
    cursor_x: int = reactive(0, always_update=True)
    cursor_y: int = reactive(0, always_update=True)
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

        # Set up async PTY handling
        self.set_pty_data_callback(self._handle_pty_data)

    # Message classes for events
    class PTYDataMessage(Message):
        """Message containing PTY data."""

        def __init__(self, data: bytes) -> None:
            self.data = data
            super().__init__()

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

    async def on_resize(self, event) -> None:
        """Handle widget resize events from Textual."""
        debug(f"on_resize called with event: {event}")

        # Convert pixel size to character size (approximate)
        # Textual widgets have size in terms of console cells
        if hasattr(event, "size"):
            new_width = event.size.width
            new_height = event.size.height
            debug(f"event size: {new_width}x{new_height}")
        else:
            # Fallback to current widget size
            new_width = self.size.width
            new_height = self.size.height
            debug(f"widget size: {new_width}x{new_height}")

        # Update terminal dimensions
        if new_width > 0 and new_height > 0:
            debug(f"setting width_chars={new_width}, height_chars={new_height}")
            self.width_chars = new_width
            self.height_chars = new_height

    def _handle_pty_data(self, data: bytes) -> None:
        """Handle PTY data by posting a Textual message."""
        self.post_message(self.PTYDataMessage(data))

    async def on_textual_terminal_ptydata_message(self, message: PTYDataMessage) -> None:
        """Handle PTY data messages through Textual's message system."""
        # Process the PTY data
        text = message.data.decode("utf-8", errors="replace")
        self.parser.feed(text)

        # Update display
        await self._update_display()

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
        # Get exit code before cleaning up the process
        exit_code = 0
        if self.process:
            exit_code = self.process.poll() or 0

        # Call parent method (this will set self.process = None)
        super().stop_process()

        # Post exit message
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
        debug(f"width_chars changed from {old_width} to {new_width}")
        # Update the base Terminal size
        super().resize(new_width, self.height_chars)
        # Notify the PTY process about the size change
        self._set_terminal_size()

    def watch_height_chars(self, old_height: int, new_height: int) -> None:
        """Called when height changes."""
        debug(f"height_chars changed from {old_height} to {new_height}")
        # Update the base Terminal size
        super().resize(self.width_chars, new_height)
        # Notify the PTY process about the size change
        self._set_terminal_size()

    def _set_terminal_size(self) -> None:
        """Set the terminal window size."""
        if self.pty is not None:
            self.pty.resize(self.height_chars, self.width_chars)

    # Input handling
    async def on_mouse_move(self, event) -> None:
        """Handle mouse movement events."""
        if self.pty is None or not self.mouse_any_tracking:
            return

        # Convert screen coordinates to terminal coordinates
        x = event.x + 1  # Terminal coordinates are 1-based
        y = event.y + 1

        # Send SGR mouse movement event (button 35 = movement, no buttons pressed)
        if self.mouse_sgr_mode:
            mouse_seq = f"\033[<35;{x};{y}M"
            self.pty.write(mouse_seq.encode("utf-8"))

    async def on_mouse_down(self, event) -> None:
        """Handle mouse button press events."""
        if self.pty is None or not self.mouse_tracking:
            return

        # Convert screen coordinates to terminal coordinates
        x = event.x + 1
        y = event.y + 1

        # Map mouse buttons (0=left, 1=middle, 2=right)
        button_map = {"left": 0, "middle": 1, "right": 2}
        button = button_map.get(event.button, 0)

        # Add modifier flags
        if event.shift:
            button |= 4
        if event.alt:
            button |= 8
        if event.ctrl:
            button |= 16

        # Send SGR mouse press event
        if self.mouse_sgr_mode:
            mouse_seq = f"\033[<{button};{x};{y}M"
            self.pty.write(mouse_seq.encode("utf-8"))

    async def on_mouse_up(self, event) -> None:
        """Handle mouse button release events."""
        if self.pty is None or not self.mouse_tracking:
            return

        # Convert screen coordinates to terminal coordinates
        x = event.x + 1
        y = event.y + 1

        # Map mouse buttons
        button_map = {"left": 0, "middle": 1, "right": 2}
        button = button_map.get(event.button, 0)

        # Add modifier flags
        if event.shift:
            button |= 4
        if event.alt:
            button |= 8
        if event.ctrl:
            button |= 16

        # Send SGR mouse release event (lowercase 'm')
        if self.mouse_sgr_mode:
            mouse_seq = f"\033[<{button};{x};{y}m"
            self.pty.write(mouse_seq.encode("utf-8"))

    async def on_key(self, event) -> None:
        """Handle key events."""
        if self.pty is None:
            return

        # Don't intercept certain app-level keys
        app_keys = {"ctrl+q", "ctrl+n"}  # Add other app bindings as needed
        if event.key in app_keys:
            # Let the app handle these keys
            return

        # Convert key to terminal escape sequence
        key_data = self._key_to_terminal_data(event)
        if key_data:
            self.pty.write(key_data.encode("utf-8"))
            # Prevent the key from propagating to Textual (important for tab, etc.)
            event.stop()
            return

        # If we couldn't handle the key, let Textual handle it
        # (but this means focus keys like Tab will still work for navigation)

    def _key_to_terminal_data(self, event) -> str:
        """Convert Textual key event to terminal input data."""
        key = event.key

        # Handle printable characters - use the actual character if available
        if hasattr(event, "character") and event.character and len(event.character) == 1:
            return event.character
        elif len(key) == 1 and key.isprintable():
            return key

        # Handle Ctrl combinations
        if key.startswith("ctrl+"):
            ctrl_key = key[5:]  # Remove 'ctrl+'
            if len(ctrl_key) == 1:
                # Convert to control character (Ctrl+A = \x01, Ctrl+B = \x02, etc.)
                char = ctrl_key.upper()
                if "A" <= char <= "Z":
                    return chr(ord(char) - ord("A") + 1)
                elif char == "0":
                    return "\x00"  # Ctrl+0 = NULL
                elif char == "\\":
                    return "\x1c"  # Ctrl+\ = FS
                elif char == "]":
                    return "\x1d"  # Ctrl+] = GS
                elif char == "^":
                    return "\x1e"  # Ctrl+^ = RS
                elif char == "_":
                    return "\x1f"  # Ctrl+_ = US

        # Special keys
        key_map = {
            "enter": "\r",
            "tab": "\t",
            "escape": "\x1b",
            "backspace": "\x7f",
            "delete": "\x1b[3~",
            "up": "\x1b[A",
            "down": "\x1b[B",
            "right": "\x1b[C",
            "left": "\x1b[D",
            "home": "\x1b[H",
            "end": "\x1b[F",
            "page_up": "\x1b[5~",
            "page_down": "\x1b[6~",
            "f1": "\x1bOP",
            "f2": "\x1bOQ",
            "f3": "\x1bOR",
            "f4": "\x1bOS",
            "f5": "\x1b[15~",
            "f6": "\x1b[17~",
            "f7": "\x1b[18~",
            "f8": "\x1b[19~",
            "f9": "\x1b[20~",
            "f10": "\x1b[21~",
            "f11": "\x1b[23~",
            "f12": "\x1b[24~",
            "space": " ",
        }
        return key_map.get(key, "")

    def action_pass_to_terminal(self) -> None:
        """Action handler for keys that should go to terminal."""
        # This will be called for tab key, send it to terminal
        if self.pty:
            self.pty.write(b"\t")
