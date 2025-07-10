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
from .. import constants


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

        # Send SGR mouse movement event
        if self.mouse_sgr_mode:
            mouse_seq = f"{constants.ESC}[<{constants.MOUSE_BUTTON_MOVEMENT};{x};{y}M"
            self.pty.write(mouse_seq.encode("utf-8"))

    async def on_mouse_down(self, event) -> None:
        """Handle mouse button press events."""
        if self.pty is None or not self.mouse_tracking:
            return

        # Convert screen coordinates to terminal coordinates
        x = event.x + 1
        y = event.y + 1

        # Map mouse buttons
        button_map = {
            "left": constants.MOUSE_BUTTON_LEFT,
            "middle": constants.MOUSE_BUTTON_MIDDLE,
            "right": constants.MOUSE_BUTTON_RIGHT,
        }
        button = button_map.get(event.button, constants.MOUSE_BUTTON_LEFT)

        # Add modifier flags
        if event.shift:
            button |= constants.MOUSE_MOD_SHIFT
        if event.meta:
            button |= constants.MOUSE_MOD_META
        if event.ctrl:
            button |= constants.MOUSE_MOD_CTRL

        # Send SGR mouse press event
        if self.mouse_sgr_mode:
            mouse_seq = f"{constants.ESC}[<{button};{x};{y}M"
            self.pty.write(mouse_seq.encode("utf-8"))

    async def on_mouse_up(self, event) -> None:
        """Handle mouse button release events."""
        if self.pty is None or not self.mouse_tracking:
            return

        # Convert screen coordinates to terminal coordinates
        x = event.x + 1
        y = event.y + 1

        # Map mouse buttons
        button_map = {
            "left": constants.MOUSE_BUTTON_LEFT,
            "middle": constants.MOUSE_BUTTON_MIDDLE,
            "right": constants.MOUSE_BUTTON_RIGHT,
        }
        button = button_map.get(event.button, constants.MOUSE_BUTTON_LEFT)

        # Add modifier flags
        if event.shift:
            button |= constants.MOUSE_MOD_SHIFT
        if event.meta:
            button |= constants.MOUSE_MOD_META
        if event.ctrl:
            button |= constants.MOUSE_MOD_CTRL

        # Send SGR mouse release event (lowercase 'm')
        if self.mouse_sgr_mode:
            mouse_seq = f"{constants.ESC}[<{button};{x};{y}m"
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

        # Parse key and route to appropriate input method
        if self._handle_key_input(event):
            # Prevent the key from propagating to Textual (important for tab, etc.)
            event.stop()
            return

        # If we couldn't handle the key, let Textual handle it
        # (but this means focus keys like Tab will still work for navigation)

    def _handle_key_input(self, event) -> bool:
        """Parse Textual key event and route to appropriate Terminal input method."""
        key = event.key

        # Parse modifiers from key string
        modifier = self._parse_modifiers(key)
        base_key = self._extract_base_key(key)

        # Handle printable characters first (use event.character if available)
        if hasattr(event, "character") and event.character and len(event.character) == 1:
            self.input_key(event.character, modifier)
            return True
        elif len(base_key) == 1 and base_key.isprintable():
            self.input_key(base_key, modifier)
            return True

        # Handle function keys (f1, f2, etc.)
        if base_key.startswith("f") and base_key[1:].isdigit():
            try:
                fkey_num = int(base_key[1:])
                self.input_fkey(fkey_num, modifier)
                return True
            except ValueError:
                pass

        # Handle cursor and navigation keys
        if base_key in ["up", "down", "left", "right", "home", "end"]:
            self.input_key(base_key, modifier)
            return True

        # Handle backspace through input_key (it might need mode awareness)
        if base_key == "backspace":
            self.input_key(base_key, modifier)
            return True

        # Handle special keys with raw sequences
        special_keys = {
            "enter": constants.CR,
            "tab": constants.HT,
            "escape": constants.ESC,
            "delete": f"{constants.ESC}[3~",
            "page_up": f"{constants.ESC}[5~",
            "page_down": f"{constants.ESC}[6~",
            "space": " ",
        }

        if base_key in special_keys:
            # TODO: Some of these might need modifier support
            self.input(special_keys[base_key])
            return True

        # Unhandled key
        return False

    def _parse_modifiers(self, key: str) -> int:
        """Extract modifier flags from Textual key string."""
        modifier = constants.KEY_MOD_NONE

        if "ctrl+" in key:
            modifier = constants.KEY_MOD_CTRL
        if "shift+" in key:
            if modifier == constants.KEY_MOD_NONE:
                modifier = constants.KEY_MOD_SHIFT
            elif modifier == constants.KEY_MOD_CTRL:
                modifier = constants.KEY_MOD_SHIFT_CTRL
        if "alt+" in key:
            if modifier == constants.KEY_MOD_NONE:
                modifier = constants.KEY_MOD_ALT
            elif modifier == constants.KEY_MOD_CTRL:
                modifier = constants.KEY_MOD_ALT_CTRL
            elif modifier == constants.KEY_MOD_SHIFT:
                modifier = constants.KEY_MOD_SHIFT_ALT
            elif modifier == constants.KEY_MOD_SHIFT_CTRL:
                modifier = constants.KEY_MOD_SHIFT_ALT_CTRL

        return modifier

    def _extract_base_key(self, key: str) -> str:
        """Extract the base key from a Textual key string (remove modifiers)."""
        # Remove all modifier prefixes
        base = key
        for prefix in ["ctrl+", "shift+", "alt+", "meta+"]:
            base = base.replace(prefix, "")
        return base

    def action_pass_to_terminal(self) -> None:
        """Action handler for keys that should go to terminal."""
        # This will be called for tab key, send it to terminal
        self.input(constants.HT)
