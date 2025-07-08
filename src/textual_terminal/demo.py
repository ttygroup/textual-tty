"""
Demo application showing multiple terminal windows.

This demo allows spawning multiple terminal instances with custom commands.
"""

from __future__ import annotations

import os
from typing import List

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Header, Footer, Input, Button, Label, TabbedContent, TabPane

from .widgets import Terminal


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


class DemoApp(App):
    """Demo application with multiple terminals."""

    CSS = """
    Screen {
        background: $surface;
    }

    #command-bar {
        height: 3;
        background: $panel;
        padding: 0 1;
        dock: top;
    }

    #command-input {
        width: 1fr;
        margin: 0 1;
    }

    #add-button {
        width: auto;
        min-width: 12;
    }

    TabbedContent {
        height: 1fr;
    }

    TabPane {
        padding: 0;
    }

    Terminal {
        height: 100%;
        width: 100%;
    }

    .terminal-container {
        height: 100%;
        width: 100%;
        overflow: hidden;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+n", "new_terminal", "New Terminal", show=True),
        Binding("ctrl+w", "close_terminal", "Close Terminal", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.default_shell = get_user_shell()
        self.terminals: List[Terminal] = []
        self.terminal_count = 1  # Start at 1 since we create one initially

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
            yield Button("Add Terminal", id="add-button", variant="primary")

        # Tabbed content for terminals
        with TabbedContent(id="terminal-tabs"):
            # Start with one terminal
            with TabPane("Shell [1]", id="terminal-1"):
                terminal = Terminal(command=self.default_shell)
                self.terminals.append(terminal)
                yield terminal

        yield Footer()

    async def add_terminal_tab(self, command: str) -> None:
        """Add a new terminal tab."""
        self.terminal_count += 1

        # Get the command name for the tab
        cmd_name = "Shell"
        if command:
            # Extract just the program name from the path
            cmd_name = command.split()[0]
            cmd_name = os.path.basename(cmd_name)

        tab_label = f"{cmd_name} [{self.terminal_count}]"
        tab_id = f"terminal-{self.terminal_count}"

        # Create terminal
        terminal = Terminal(command=command)
        self.terminals.append(terminal)

        # Create a new terminal pane
        class TerminalPane(TabPane):
            def compose(self) -> ComposeResult:
                yield terminal

        # Get the TabbedContent widget and add the new pane
        tabbed_content = self.query_one("#terminal-tabs", TabbedContent)
        new_pane = TerminalPane(tab_label, id=tab_id)
        await tabbed_content.add_pane(new_pane)

        # Switch to the new tab
        tabbed_content.active = tab_id

    def on_mount(self) -> None:
        """Focus the command input when app starts."""
        self.query_one("#command-input", Input).focus()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "add-button":
            await self.action_new_terminal()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in the command input."""
        if event.input.id == "command-input":
            await self.action_new_terminal()

    async def action_new_terminal(self) -> None:
        """Create a new terminal with the command from the input."""
        input_widget = self.query_one("#command-input", Input)
        command = input_widget.value.strip() or self.default_shell

        await self.add_terminal_tab(command)

        # Clear the input for next command
        input_widget.value = self.default_shell
        input_widget.focus()

    async def action_close_terminal(self) -> None:
        """Close the current terminal tab."""
        tabbed_content = self.query_one("#terminal-tabs", TabbedContent)

        # Get current tab
        if tabbed_content.active_pane:
            # Find and remove the terminal
            for terminal in tabbed_content.active_pane.query(Terminal):
                if terminal in self.terminals:
                    self.terminals.remove(terminal)
                    await terminal._stop_process()

            # Remove the tab
            await tabbed_content.remove_pane(tabbed_content.active)

            # If no tabs left, quit the app
            if tabbed_content.tab_count == 0:
                self.exit()

    async def on_terminal_process_exited(self, message: Terminal.ProcessExited) -> None:
        """Handle terminal process exit."""
        # Find which terminal exited
        terminal = message._sender
        if terminal in self.terminals:
            # Update the tab label to show it's closed
            tabbed_content = self.query_one("#terminal-tabs", TabbedContent)
            for pane in tabbed_content.children:
                if isinstance(pane, TabPane) and terminal in pane.query(Terminal):
                    # Update tab label
                    old_title = pane.title
                    if "[exited]" not in old_title:
                        pane.title = f"{old_title} [exited]"


def main():
    """Run the demo application."""
    app = DemoApp()
    app.run()


if __name__ == "__main__":
    main()
