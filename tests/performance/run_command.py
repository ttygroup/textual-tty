#!/usr/bin/env python3
"""
Performance test app that runs a command in a full-screen terminal.

This app creates a full-screen TextualTerminal widget, runs the specified command,
and exits when the command completes.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.widgets import Static

from textual_tty.widgets import TextualTerminal
from textual_tty.log import info, debug, get_performance_tracker


class FullScreenTerminalApp(App):
    """A full-screen terminal app for running commands."""

    CSS = """
    Screen {
        padding: 0;
        margin: 0;
        background: black;
    }

    TextualTerminal {
        width: 100%;
        height: 100%;
        padding: 0;
        margin: 0;
        background: black;
        color: white;
    }

    TextualTerminal > TerminalScrollView {
        scrollbar-size: 0 0;
        background: black;
        color: white;
    }

    #placeholder {
        width: 100%;
        height: 100%;
        content-align: center middle;
        color: red;
    }
    """

    def __init__(self, command: Optional[str] = None):
        super().__init__()
        self.command = command
        self.terminal: Optional[TextualTerminal] = None
        self.exit_code: Optional[int] = None

    def compose(self) -> ComposeResult:
        """Compose the terminal app."""
        if self.command:
            self.terminal = TextualTerminal(command=self.command)
            yield self.terminal
        else:
            yield Static("No command specified!", id="placeholder")

    def on_mount(self) -> None:
        """Handle when app is mounted."""
        if self.terminal:
            self.terminal.focus()
            info(f"Started command: {self.command}")

            # Enable performance tracking
            tracker = get_performance_tracker()
            log_dir = Path(__file__).parent.parent.parent / "logs"
            tracker.enable(log_dir)
            info(f"Performance tracking enabled for command: {self.command}")

    def on_textual_terminal_process_exited(self, event: TextualTerminal.ProcessExited) -> None:
        """Handle when the terminal process exits."""
        self.exit_code = event.exit_code
        info(f"Command exited with code: {self.exit_code}")
        debug(f"Process exited: command='{self.command}', exit_code={self.exit_code}")

        # Disable performance tracking before exit
        tracker = get_performance_tracker()
        tracker.disable()

        self.exit()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python run_command.py <command> [args...]")
        print("Example: python run_command.py ls -la")
        sys.exit(1)

    # Join all arguments as the command
    command = " ".join(sys.argv[1:])

    # Create and run the app
    app = FullScreenTerminalApp(command=command)
    app.run()

    # Exit with the same code as the command
    if app.exit_code is not None:
        sys.exit(app.exit_code)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
