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

    # Let focus pass through to the terminal inside
    can_focus = False

    DEFAULT_CSS = """
    ProgramWindow {
        padding: 0;
        margin: 0;
        width: 83;
        height: 28;
    }

    ProgramWindow #content_pane {
        padding: 0;
        margin: 0;
    }

    ProgramWindow Terminal RichLog {
        scrollbar-size: 0 0;
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
        self.program: Optional[Program] = None

    def compose(self) -> ComposeResult:
        """Compose the program window."""
        self.program = Program(command=self.command, show_header=self.show_header, show_footer=self.show_footer)
        yield self.program

    def on_program_program_exited(self, event: Program.ProgramExited) -> None:
        """Handle when the program process exits."""
        info(f"ProgramWindow: Program exited with code {event.exit_code}")
        # Close the window when the program exits
        self.call_later(self.remove)

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
