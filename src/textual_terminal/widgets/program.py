"""
Program widget for Textual applications.

This module provides a Program widget that wraps a Terminal in a convenient
container. A Program represents a command running in a terminal window and
automatically closes when the process terminates.
"""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Header, Footer
from textual.containers import Vertical

from .terminal import Terminal
from ..log import info


class Program(Widget):
    """A program running in a terminal widget.

    This widget wraps a Terminal and provides a convenient way to run
    a specific command. It automatically handles process termination
    and can optionally show header/footer bars.
    """

    DEFAULT_CSS = """
    Program {
        background: black;
        color: white;
        padding: 0;
        margin: 0;
        width: 80;
        height: 24;
    }

    Program > Vertical {
        padding: 0;
        margin: 0;
    }

    Program Terminal {
        height: 100%;
        width: 100%;
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
    ):
        """Initialize the program widget.

        Args:
            command: Command to run in the terminal (defaults to shell)
            show_header: Whether to show the header bar
            show_footer: Whether to show the footer bar
        """
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.command = command or "/bin/bash"
        self.show_header = show_header
        self.show_footer = show_footer
        self.terminal: Optional[Terminal] = None

    def compose(self) -> ComposeResult:
        """Compose the program layout."""
        with Vertical():
            if self.show_header:
                yield Header()

            self.terminal = Terminal(command=self.command)
            yield self.terminal

            if self.show_footer:
                yield Footer()

    def on_mount(self) -> None:
        """Set up event handling when the widget is mounted."""
        if self.terminal:
            # Listen for terminal process events
            self.terminal.add_class("program-terminal")

    def on_terminal_process_exited(self, event: Terminal.ProcessExited) -> None:
        """Handle terminal process exit.

        This method can be overridden in subclasses to customize
        behavior when the process exits.
        """
        info(f"Program: Terminal process exited with code: {event.exit_code}")

        # Schedule window close on next tick so exit code can be retrieved
        self.call_later(self._close_containing_window)

    def _close_containing_window(self) -> None:
        """Close the window containing this program."""
        # Walk up the widget tree to find the containing window
        parent = self.parent
        while parent:
            if hasattr(parent, "close") and "Window" in str(type(parent)):
                info(f"Program: Closing containing window {getattr(parent, 'id', 'unknown')}")
                parent.close()
                return
            parent = parent.parent
        info("Program: Could not find containing window to close")

    def set_command(self, command: str) -> None:
        """Set a new command for the terminal."""
        self.command = command
        if self.terminal:
            self.terminal.command = command

    def get_exit_code(self) -> Optional[int]:
        """Get the exit code of the process if it has exited."""
        if self.terminal and self.terminal.process:
            return self.terminal.process.poll()
        return None

    def is_running(self) -> bool:
        """Check if the process is still running."""
        return self.get_exit_code() is None

    def terminate(self) -> None:
        """Terminate the running process."""
        if self.terminal:
            self.terminal.terminate()
