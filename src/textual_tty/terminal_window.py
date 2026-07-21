"""TerminalWindow: a Terminal in a Window.

The wiring between the two: the window title follows the child's OSC title,
the bell flashes the window, the window closes when the process exits, and
resizing the window reflows the child (the Terminal fills the content area,
so the board hears about it through the widget's own resize).
"""

from __future__ import annotations

from .widget import Terminal
from .window import Window


class TerminalWindow(Window):
    """A draggable, resizable window running a terminal."""

    DEFAULT_CSS = """
    TerminalWindow {
        width: 84;
        height: 26;
    }

    TerminalWindow > #content {
        background: #000000;
    }

    TerminalWindow.bell > #header {
        background: $warning;
    }
    """

    def __init__(self, command: str | list[str] = "/bin/bash", **window_kwargs) -> None:
        self.terminal = Terminal(command=command)
        super().__init__(self.terminal, title=str(command), **window_kwargs)

    def on_mount(self) -> None:
        super().on_mount()
        self.call_after_refresh(self.terminal.focus)

    def on_terminal_title_changed(self, message: Terminal.TitleChanged) -> None:
        message.stop()
        self.title = message.title

    def on_terminal_bell(self, message: Terminal.Bell) -> None:
        message.stop()
        self.app.bell()
        self.add_class("bell")
        self.set_timer(0.3, lambda: self.remove_class("bell"))

    def on_terminal_process_exited(self, message: Terminal.ProcessExited) -> None:
        message.stop()
        self.remove()
