"""
Terminal app widget for Textual applications.

This module provides a TerminalApp widget that combines a TextualTerminal widget
with a Window from textual-window, creating a draggable window containing
a terminal that closes when the process exits.
"""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual_window import Window

from .textual_terminal import TextualTerminal
from ..log import info


class TerminalApp(Window):
    """A draggable window containing a terminal emulator.

    This widget combines the TextualTerminal widget with Window functionality,
    creating a movable window that automatically closes when the
    terminal process exits.
    """

    # Let focus pass through to the terminal inside
    can_focus = False

    DEFAULT_CSS = """
    TerminalApp {
        padding: 0;
        margin: 0;
        width: 83;
        height: 28;
        background: black;
    }

    TerminalApp #content_pane {
        padding: 0;
        margin: 0;
        background: black;
    }

    TerminalApp TextualTerminal {
        padding: 0;
        margin: 0;
        width: 100%;
        height: 100%;
        background: black;
        color: white;
    }

    TerminalApp TextualTerminal > RichLog {
        scrollbar-size: 0 0;
        background: black;
        color: white;
    }
    """

    def __init__(
        self,
        command: Optional[str] = None,
        show_header: bool = False,
        show_footer: bool = False,
        *,
        name: Optional[str] = None,
        id: Optional[str] = None,
        classes: Optional[str] = None,
        disabled: bool = False,
        **window_kwargs,
    ):
        # Create styles_dict for the Window constructor
        styles_dict = {"width": 83, "height": 28}
        # Merge with any existing styles_dict from window_kwargs
        if "styles_dict" in window_kwargs:
            styles_dict.update(window_kwargs["styles_dict"])
            del window_kwargs["styles_dict"]

        super().__init__(name=name, id=id, classes=classes, disabled=disabled, styles_dict=styles_dict, **window_kwargs)
        self.command = command
        self.show_header = show_header
        self.show_footer = show_footer
        self.terminal: Optional[TextualTerminal] = None

    def compose(self) -> ComposeResult:
        """Compose the terminal app window."""
        self.terminal = TextualTerminal(command=self.command or "/bin/bash")
        yield self.terminal

    def on_mount(self) -> None:
        """Handle when the window is mounted."""
        # Auto-focus the terminal when the window opens (after refresh)
        self.call_after_refresh(self._focus_terminal)

    def _focus_terminal(self) -> None:
        """Focus the terminal."""
        if self.terminal:
            self.terminal.focus()

    def on_textual_terminal_process_exited(self, event: TextualTerminal.ProcessExited) -> None:
        """Handle when the terminal process exits."""
        info(f"TerminalApp: Terminal process exited with code {event.exit_code}")
        # Close the window when the program exits
        self.call_later(self.remove)

    def get_exit_code(self) -> Optional[int]:
        """Get the exit code of the process if it has exited."""
        if self.terminal and self.terminal.process:
            return self.terminal.process.poll()
        return None

    def is_running(self) -> bool:
        """Check if the process is still running."""
        if self.program:
            return self.program.is_running()
        return False

    def terminate(self) -> None:
        """Terminate the running process."""
        if self.program:
            self.program.terminate()
