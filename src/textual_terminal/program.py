"""
Terminal application with window support.

This module provides the main terminal application that can run either as
a regular Textual app or inside a native window using textual-window.
"""

from __future__ import annotations

import sys
from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer

from .widgets import Terminal


class Program(App):
    """Main terminal application."""

    CSS = """
    Screen {
        padding: 0;
        margin: 0;
    }
    
    Terminal {
        dock: fill;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True, priority=True),
        Binding("ctrl+shift+p", "command_palette", "Command Palette", show=False),
    ]

    def __init__(self, command: Optional[str] = None, show_header: bool = True, show_footer: bool = True, **kwargs):
        """Initialize the terminal application.

        Args:
            command: Command to run in the terminal (defaults to shell)
            show_header: Whether to show the header bar
            show_footer: Whether to show the footer bar
        """
        super().__init__(**kwargs)
        self.command = command or "/bin/bash"
        self.show_header = show_header
        self.show_footer = show_footer

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        if self.show_header:
            yield Header()

        yield Terminal(command=self.command)

        if self.show_footer:
            yield Footer()


def run_windowed():
    """Run the terminal in a native window using textual-window."""
    try:
        from textual_window import TextualWindow
    except ImportError:
        print("Error: textual-window not installed.", file=sys.stderr)
        print("Install with: pip install textual-terminal[window]", file=sys.stderr)
        return 1

    # Create the app
    app = Program()

    # Run it in a window
    window = TextualWindow(
        app,
        title="Textual Terminal",
        width=1024,
        height=768,
    )
    window.run()
    return 0


def run_cli():
    """Run the terminal as a regular Textual app."""
    app = TerminalApp()
    app.run()
    return 0


def main():
    """Main entry point for the application."""
    import argparse

    parser = argparse.ArgumentParser(description="Textual Terminal Emulator")
    parser.add_argument("--window", "-w", action="store_true", help="Run in a native window (requires textual-window)")
    parser.add_argument("--no-header", action="store_true", help="Hide the header bar")
    parser.add_argument("--no-footer", action="store_true", help="Hide the footer bar")
    parser.add_argument("command", nargs="?", default="/bin/bash", help="Command to run (default: /bin/bash)")

    args = parser.parse_args()

    if args.window:
        return run_windowed()
    else:
        # Create app with CLI arguments
        app = Program(
            command=args.command,
            show_header=not args.no_header,
            show_footer=not args.no_footer,
        )
        app.run()
        return 0


if __name__ == "__main__":
    sys.exit(main())
