"""
Program window widget for Textual applications.

This module provides a ProgramWindow widget that combines a Program widget
with a Window from textual-window, creating a draggable window containing
a terminal program that closes when the process exits.
"""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual_window import Window

from .program import Program
from ..log import info


class ProgramWindow(Window):
    """A draggable window containing a terminal program.

    This widget combines the Program widget with Window functionality,
    creating a movable window that automatically closes when the
    contained process exits.
    """

    DEFAULT_CSS = """
    ProgramWindow {
        padding: 0;
        margin: 0;
    }

    ProgramWindow Program {
        padding: 0;
        margin: 0;
        width: 100%;
        height: 100%;
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
        """Initialize the program window.

        Args:
            command: Command to run in the terminal (defaults to shell)
            show_header: Whether to show the header bar in the program
            show_footer: Whether to show the footer bar in the program
            **window_kwargs: Additional arguments passed to Window
        """
        super().__init__(name=name, id=id, classes=classes, disabled=disabled, **window_kwargs)
        self.command = command
        self.show_header = show_header
        self.show_footer = show_footer
        self.program: Optional[Program] = None

    def compose(self) -> ComposeResult:
        """Compose the program window."""
        self.program = Program(command=self.command, show_header=self.show_header, show_footer=self.show_footer)
        yield self.program

    def on_terminal_process_exited(self, event) -> None:
        """Handle when the terminal process exits."""
        info(f"ProgramWindow: Process exited with code {event.exit_code}")
        # Close the window when the process exits
        self.call_later(self.close)

    def get_exit_code(self) -> Optional[int]:
        """Get the exit code of the process if it has exited."""
        if self.program:
            return self.program.get_exit_code()
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
