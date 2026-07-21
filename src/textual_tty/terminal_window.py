"""TerminalWindow: a Terminal in a Window.

The wiring between the two: the window title follows the child's OSC title,
the bell flashes the window, the window closes when the process exits, and
resizing the window reflows the child (the Terminal fills the content area,
so the board hears about it through the widget's own resize).

XTWINOPS runs both ways: the child can raise/lower/move/maximize/resize its
own window, and window moves are written back into the board's registers so
position queries (CSI 13 t) report the truth. Iconify is ignored — there is
no taskbar to minimise to.
"""

from __future__ import annotations

from textual.geometry import Offset

from .widget import Terminal
from .window import TitleBar, Window

# The window chrome around the terminal grid: side bands, header row, footer row.
_CHROME_WIDTH = 2
_CHROME_HEIGHT = 2


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
        self._restore_geometry = None  # pre-maximize (offset, size), while maximized
        super().__init__(self.terminal, title=str(command), **window_kwargs)

    def on_mount(self) -> None:
        super().on_mount()
        self.call_after_refresh(self.terminal.focus)

    # --- board registers follow the real window (queries then report the truth) --- #

    def _sync_position_register(self) -> None:
        self.terminal.board.window_position = (self.offset.x, self.offset.y)

    def _position_window(self) -> None:
        super()._position_window()
        if self.parent is not None:  # reading offset needs a screen; a closed window has none
            self._sync_position_register()

    def on_title_bar_dragged(self, message: TitleBar.Dragged) -> None:
        super().on_title_bar_dragged(message)
        self._sync_position_register()

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

    # --- the child drives its own window (XTWINOPS) --- #

    def on_terminal_window_request(self, message: Terminal.WindowRequest) -> None:
        message.stop()
        if message.kind == "raise":
            self.bring_to_front()
        elif message.kind == "lower":
            self.parent.move_child(self, before=0)
        elif message.kind == "refresh":
            self.refresh()

    def on_terminal_window_state_changed(self, message: Terminal.WindowStateChanged) -> None:
        message.stop()
        if message.position != (self.offset.x, self.offset.y):
            self.offset = Offset(*message.position)
        self._apply_maximize(message.maximized or message.fullscreen)
        # iconified: ignored — no taskbar

    def _apply_maximize(self, maximized: bool) -> None:
        if maximized and self._restore_geometry is None:
            self._restore_geometry = (self.offset, self.region.size)
            self.offset = Offset(0, 0)
            self.styles.width = "100%"
            self.styles.height = "100%"
        elif not maximized and self._restore_geometry is not None:
            offset, size = self._restore_geometry
            self._restore_geometry = None
            self.offset = offset
            self.styles.width = size.width
            self.styles.height = size.height
        self._sync_position_register()

    def on_terminal_board_resized(self, message: Terminal.BoardResized) -> None:
        message.stop()
        self.styles.width = message.width + _CHROME_WIDTH
        self.styles.height = message.height + _CHROME_HEIGHT
