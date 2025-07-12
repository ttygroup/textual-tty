#!/usr/bin/env python3
"""
Passthrough demo - full-screen Textual terminal with mouse support.

Simple passthrough terminal that runs a command and displays it full-screen
with mouse cursor support for asciinema recording.
"""

import argparse
import asyncio
from textual.app import App, ComposeResult
from textual_tty.widgets import TextualTerminal


class PassthroughApp(App):
    """Full-screen terminal application."""

    CSS = """
    Screen {
        layout: vertical;
        padding: 0;
        margin: 0;
    }

    TextualTerminal {
        width: 100%;
        height: 100%;
        border: none;
        margin: 0;
        padding: 0;
    }
    """

    def __init__(self, command, **kwargs):
        super().__init__(**kwargs)
        self.command = command

    def compose(self) -> ComposeResult:
        """Create the terminal widget."""
        terminal = TextualTerminal(command=self.command)
        # Enable mouse cursor display for asciinema recording
        terminal.show_mouse = True
        yield terminal

    def on_textual_terminal_process_exited(self, message) -> None:
        """Handle terminal process exit."""
        self.exit(message.exit_code)

    def on_unmount(self) -> None:
        """Clean up when app exits."""
        # Turn off mouse reporting
        import sys

        sys.stdout.write("\033[?1003l\033[?1000l\033[?1015l\033[?1006l")
        sys.stdout.flush()


async def main():
    parser = argparse.ArgumentParser(description="Full-screen terminal passthrough with mouse support")
    parser.add_argument("command", nargs="*", default=["/bin/bash"], help="Command to run (default: /bin/bash)")

    args = parser.parse_args()
    command = args.command if len(args.command) > 0 else ["/bin/bash"]

    app = PassthroughApp(command=command)
    await app.run_async()


if __name__ == "__main__":
    asyncio.run(main())
