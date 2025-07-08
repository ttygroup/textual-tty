#!/usr/bin/env python3
"""
Demo: Launch programs in a window in Textual
"""

from __future__ import annotations

import os

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Header, Footer, Input, Button, Label, Static
from textual_window import Window

from textual_terminal.widgets import Terminal, Program, DebugLog
from textual_terminal.log import setup_logger


def get_user_shell() -> str:
    """Get the user's default shell from the environment."""
    # Try SHELL environment variable first
    shell = os.environ.get("SHELL")
    if shell and os.path.exists(shell):
        return shell

    # Try to get from passwd database (Unix/Linux only)
    try:
        import pwd

        shell = pwd.getpwuid(os.getuid()).pw_shell
        if shell and os.path.exists(shell):
            return shell
    except (ImportError, AttributeError):
        # pwd module not available (Windows) or getpwuid not available
        pass

    # Platform-specific defaults
    if os.name == "nt":  # Windows
        return os.environ.get("COMSPEC", "cmd.exe")

    # Unix/Linux fallbacks
    for shell in ["/bin/bash", "/bin/sh", "/usr/bin/bash", "/usr/bin/sh"]:
        if os.path.exists(shell):
            return shell

    # Last resort
    return "sh"


# Removed TerminalWindow class - we now use Program widgets in Window widgets


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

    Window > * {
        padding: 0;
        margin: 0;
    }

    .window-content {
        padding: 0;
        margin: 0;
    }

    .window-body {
        padding: 0;
        margin: 0;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+n", "new_terminal", "New Terminal", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.default_shell = get_user_shell()
        self.window_count = 0

        # Set up logging
        setup_logger()

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header()

        # Command bar
        with Horizontal(id="command-bar"):
            yield Label("Command: ")
            yield Input(
                placeholder=f"Enter command (default: {self.default_shell})",
                id="command-input",
                value=self.default_shell,
            )
            yield Button("New Window", id="add-button", variant="primary")

        # Status area
        yield Static(
            "Enter a command and press Enter or click 'New Window' to open a terminal in a new window.\n"
            f"Default shell: {self.default_shell}\n"
            f"Windows opened: {self.window_count}",
            id="status",
        )

        # Debug log
        yield DebugLog()

        yield Footer()

    def create_terminal_window(self, command: str) -> None:
        """Create a new terminal window using textual-window."""
        self.window_count += 1

        # Get the command name for the window title
        cmd_name = "Shell"
        if command:
            cmd_name = command.split()[0]
            cmd_name = os.path.basename(cmd_name)

        window_title = f"{cmd_name}_{self.window_count}"

        # Create the program widget
        program = Program(command=command)

        # Create and show the window
        window = Window(
            program,
            id=window_title,
            name=f"{cmd_name} [{self.window_count}]",
            start_open=True,
        )

        # Add the window to the current app
        self.mount(window)

        # Update status
        self.update_status()

    def update_status(self) -> None:
        """Update the status display."""
        status_widget = self.query_one("#status", Static)
        status_widget.update(
            "Enter a command and press Enter or click 'New Window' to open a terminal in a new window.\n"
            f"Default shell: {self.default_shell}\n"
            f"Windows opened: {self.window_count}"
        )

    def on_mount(self) -> None:
        """Focus the command input when app starts."""
        self.query_one("#command-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "add-button":
            self.action_new_terminal()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in the command input."""
        if event.input.id == "command-input":
            self.action_new_terminal()

    def action_new_terminal(self) -> None:
        """Create a new terminal window with the command from the input."""
        input_widget = self.query_one("#command-input", Input)
        command = input_widget.value.strip() or self.default_shell

        self.create_terminal_window(command)

        # Clear the input for next command
        input_widget.value = self.default_shell
        input_widget.focus()

    def on_terminal_process_exited(self, event: Terminal.ProcessExited) -> None:
        """Handle terminal process exit by removing the window."""
        from ..log import info

        info(f"DemoApp: Terminal process exited with code: {event.exit_code}")
        info(f"DemoApp: Event sender: {event.sender}")
        info(f"DemoApp: Event sender type: {type(event.sender)}")

        # Stop the event from bubbling up further
        event.stop()

        # Find the window containing the terminal that exited
        terminal = event.sender
        if terminal:
            info("DemoApp: Looking for window containing terminal...")
            # Find the window that contains this terminal (through Program widget)
            windows = list(self.query(Window))
            info(f"DemoApp: Found {len(windows)} windows")
            for window in windows:
                info(f"DemoApp: Checking window {window.id}")
                # Check if this window contains a program with the terminal that exited
                programs = list(window.query(Program))
                info(f"DemoApp: Window {window.id} has {len(programs)} programs")
                for program in programs:
                    info(f"DemoApp: Program terminal: {program.terminal}, looking for: {terminal}")
                    if program.terminal is terminal:
                        info(f"DemoApp: Found matching terminal, closing window {window.id}")
                        window.close()
                        return

        info("DemoApp: Could not find window to close")


def main():
    """Run the demo application."""
    app = DemoApp()
    app.run()


if __name__ == "__main__":
    main()
