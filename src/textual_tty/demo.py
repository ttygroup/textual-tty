#!/usr/bin/env python3
"""
Demo: Launch programs in a window in Textual
"""

from __future__ import annotations


import argparse
import logging
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Input, Button, Label, Static

from textual_tty.widgets import TerminalApp, DebugLog
from textual_tty.log import setup_logger


class DemoApp(App):
    """Demo launcher application."""

    CSS = """
    Screen {
        background: black;
    }

    #command-bar {
        height: auto;
        background: $surface;
        padding: 1;
        margin-bottom: 1;
        align: center middle;
    }

    #command-bar Label {
        color: $text;
        margin-right: 1;
        content-align: center middle;
    }

    #command-input {
        width: 1fr;
        margin: 0 1;
        background: $surface;
        color: $text;
    }

    #add-button {
        width: auto;
        min-width: 14;
        margin-left: 1;
    }

    #status {
        height: 1fr;
        background: $surface;
        padding: 1;
        border: solid $accent;
        color: $text;
    }

    #main-content {
        height: 1fr;
        padding: 1;
    }

    /* Windows are positioned absolutely by textual-window */
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+n", "new_terminal", "New Terminal", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.window_count = 0

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header()

        # Command bar
        with Horizontal(id="command-bar"):
            yield Label("Command: ")
            yield Input(
                placeholder="Enter command (default: bash)",
                id="command-input",
                value="bash",
            )
            yield Button("New Terminal", id="add-button", variant="primary")

        # Main content area
        with Vertical(id="main-content"):
            # Status area
            yield Static(
                "Enter a command and press Enter or click 'New Terminal' to create a terminal.\n"
                f"Terminals created: {self.window_count}",
                id="status",
            )

        yield Footer()

        # Debug log
        yield DebugLog()

    def create_terminal(self, command: str) -> None:
        """Create a new terminal window."""
        self.window_count += 1

        # Create a TerminalApp - a draggable window with a terminal emulator
        window = TerminalApp(
            command=command,
            id=f"Terminal {self.window_count}",
            start_open=True,
            starting_horizontal="center",
            starting_vertical="middle",
        )

        # Mount the window
        self.mount(window)

        # Focus the new window
        window.focus()

        # Update status
        self.update_status()

    def update_status(self) -> None:
        """Update the status display."""
        status_widget = self.query_one("#status", Static)
        status_widget.update(
            "Enter a command and press Enter or click 'New Terminal' to create a terminal.\n"
            f"Terminals created: {self.window_count}"
        )

    def on_mount(self) -> None:
        """Focus the command input when app starts."""
        input_widget = self.query_one("#command-input", Input)
        input_widget.focus()
        input_widget.cursor_position = 0
        input_widget.selection_end = len(input_widget.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "add-button":
            self.action_new_terminal()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in the command input."""
        if event.input.id == "command-input":
            self.action_new_terminal()

    def action_new_terminal(self) -> None:
        """Create a new terminal with the command from the input."""
        input_widget = self.query_one("#command-input", Input)
        command = input_widget.value.strip() or "bash"

        self.create_terminal(command)


def main():
    """Run the demo application."""
    parser = argparse.ArgumentParser(description="Run the textual-tty demo app.")
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=Path("logs"),
        help="The directory to store log files.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="DEBUG",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="The logging level to use.",
    )
    args = parser.parse_args()

    # Set up logging
    log_level = getattr(logging, args.log_level.upper(), logging.DEBUG)
    setup_logger(log_dir=args.log_dir, level=log_level)

    app = DemoApp()
    app.run()


if __name__ == "__main__":
    main()
