"""The textual-tty demo: launch commands in draggable terminal windows."""

from __future__ import annotations

import os
import shlex
import sys

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.geometry import Offset
from textual.widgets import Button, Footer, Header, Input

from .debug_log import DebugLog
from .terminal_window import TerminalWindow
from .widget import Terminal
from .window import Window


class DemoApp(App):
    """A desktop of terminal windows."""

    TITLE = "textual-tty"

    CSS = """
    #launcher {
        dock: top;
        height: 3;
        padding: 0 1;
        background: $surface;
    }

    #command {
        width: 1fr;
    }

    #desktop {
        width: 100%;
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("ctrl+n", "new_terminal", "New terminal", priority=True),
        Binding("ctrl+q", "quit", "Quit", priority=True),
        Binding("f12", "toggle_debug", "Debug log", priority=True),
    ]

    def __init__(self, command: list[str] | None = None) -> None:
        super().__init__()
        self._initial_command = command
        self._spawned = 0

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="launcher"):
            yield Input(placeholder="command to run (empty for your shell)", id="command")
            yield Button("Launch", id="launch")
        yield Container(id="desktop")
        yield Footer()

    def on_mount(self) -> None:
        if self._initial_command:
            self._spawn(self._initial_command)

    # --- spawning windows --- #

    def _spawn(self, command: str | list[str]) -> None:
        window = TerminalWindow(command=command)
        self.query_one("#desktop").mount(window)
        # Cascade so consecutive windows don't stack exactly on top of each other.
        nudge = self._spawned % 5
        self._spawned += 1
        window.call_after_refresh(lambda: setattr(window, "offset", window.offset + Offset(nudge * 4, nudge * 2)))

    def _default_shell(self) -> str:
        return os.environ.get("SHELL") or os.environ.get("COMSPEC") or "/bin/sh"

    def _launch_from_input(self) -> None:
        text = self.query_one("#command", Input).value.strip()
        self._spawn(shlex.split(text) if text else self._default_shell())

    def on_input_submitted(self, message: Input.Submitted) -> None:
        self._launch_from_input()

    def on_button_pressed(self, message: Button.Pressed) -> None:
        self._launch_from_input()

    # --- actions --- #

    def action_new_terminal(self) -> None:
        """Open a shell — in the focused terminal's directory when it told us one (OSC 7)."""
        shell = self._default_shell()
        focused = self.focused
        if isinstance(focused, Terminal) and focused.cwd:
            self._spawn(["sh", "-c", f"cd {shlex.quote(focused.cwd)} && exec {shlex.quote(shell)}"])
        else:
            self._spawn(shell)

    def action_toggle_debug(self) -> None:
        existing = self.query("#debug-window")
        if existing:
            existing.remove()
        else:
            window = Window(DebugLog(), title="debug log", id="debug-window", starting_vertical="bottom")
            self.query_one("#desktop").mount(window)


def main() -> None:
    command = sys.argv[1:] or None
    DemoApp(command=command).run()


if __name__ == "__main__":
    main()
