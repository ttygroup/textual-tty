"""Terminal: a Monitor plus the terminal-ness — process, keyboard, ports.

The widget composes a Board (never subclasses it) and plugs a chrome adapter
into the board's display port. Rendering is inherited from Monitor; this class
adds the child process lifecycle, input forwarding (keys, mouse, paste, focus),
capability reporting, and the discrete side-effects surfaced as Textual
messages (bell, title, notifications, window control, process exit).
"""

from __future__ import annotations

from urllib.parse import unquote, urlparse

from bittty import Board, TerminalCaps, constants
from textual import events
from textual.message import Message

from .monitor import Monitor, MonitorChrome

# Textual modifier sets -> bittty's xterm-style modifier parameter.
_MODIFIERS = {
    frozenset(): constants.KEY_MOD_NONE,
    frozenset({"shift"}): constants.KEY_MOD_SHIFT,
    frozenset({"alt"}): constants.KEY_MOD_ALT,
    frozenset({"shift", "alt"}): constants.KEY_MOD_SHIFT_ALT,
    frozenset({"ctrl"}): constants.KEY_MOD_CTRL,
    frozenset({"shift", "ctrl"}): constants.KEY_MOD_SHIFT_CTRL,
    frozenset({"alt", "ctrl"}): constants.KEY_MOD_ALT_CTRL,
    frozenset({"shift", "alt", "ctrl"}): constants.KEY_MOD_SHIFT_ALT_CTRL,
}

# Textual key names for keys the board's keymap doesn't name itself.
_NAMED_KEYS = {
    "enter": "\r",
    "tab": "\t",
    "escape": "\x1b",
    "backspace": constants.BS,  # the board applies DECBKM to choose BS or DEL
    "space": " ",
}

_MOUSE_BUTTONS = {
    1: constants.MOUSE_BUTTON_LEFT,
    2: constants.MOUSE_BUTTON_MIDDLE,
    3: constants.MOUSE_BUTTON_RIGHT,
}


def _cwd_path(cwd: str) -> str:
    """OSC 7 carries a file:// URL; give apps a plain path."""
    if cwd.startswith("file://"):
        return unquote(urlparse(cwd).path)
    return cwd


class TerminalChrome(MonitorChrome):
    """The full board-facing jack: render hooks plus session side-effects."""

    def on_bell(self) -> None:
        self.widget.post_message(Terminal.Bell())

    def on_title(self, title: str, icon_title: str) -> None:
        self.widget.icon_title = icon_title
        self.widget.post_message(Terminal.TitleChanged(title, icon_title))

    def on_mouse_mode(self, mode: str, sgr: bool) -> None:
        self.widget.mouse_mode = mode

    def on_notify(self, text: str) -> None:
        self.widget.app.notify(text)

    def on_clipboard(self, selection: str, text: str) -> None:
        if selection == "c":  # the clipboard proper; primary/cut-buffers stay board-side
            self.widget.app.copy_to_clipboard(text)

    def on_cwd(self, cwd: str) -> None:
        self.widget.cwd = _cwd_path(cwd)
        self.widget.post_message(Terminal.CwdChanged(self.widget.cwd))

    def on_pointer(self, shape: str) -> None:
        self.widget.set_pointer(shape)

    def on_prompt_mark(self, mark: str, row: int) -> None:
        """OSC 133 marks become useful with scrollback (logloglog); nothing to do yet."""

    def on_window_request(self, kind: str) -> None:
        self.widget.post_message(Terminal.WindowRequest(kind))

    def on_window_state(self, event) -> None:
        self.widget.post_message(
            Terminal.WindowStateChanged(event.iconified, event.maximized, event.fullscreen, event.position)
        )


class Terminal(Monitor):
    """A terminal emulator widget: a bittty Board rendered as Textual content."""

    can_focus = True
    CHROME = TerminalChrome

    DEFAULT_CSS = """
    Terminal {
        background: #000000;
        color: #e8e8e8;
        width: 100%;
        height: 100%;
    }
    """

    class Bell(Message):
        """The child rang the bell."""

    class TitleChanged(Message):
        """The child set the window or icon title."""

        def __init__(self, title: str, icon_title: str) -> None:
            self.title = title
            self.icon_title = icon_title
            super().__init__()

    class ProcessExited(Message):
        """The child process exited."""

        def __init__(self, exit_code: int) -> None:
            self.exit_code = exit_code
            super().__init__()

    class CwdChanged(Message):
        """The child reported its working directory (OSC 7), as a plain path."""

        def __init__(self, cwd: str) -> None:
            self.cwd = cwd
            super().__init__()

    class WindowRequest(Message):
        """The child asked for a window action: "raise" / "lower" / "refresh"."""

        def __init__(self, kind: str) -> None:
            self.kind = kind
            super().__init__()

    class WindowStateChanged(Message):
        """The child changed window state via XTWINOPS."""

        def __init__(self, iconified: bool, maximized: bool, fullscreen: bool, position: tuple[int, int]) -> None:
            self.iconified = iconified
            self.maximized = maximized
            self.fullscreen = fullscreen
            self.position = position
            super().__init__()

    class BoardResized(Message):
        """The child resized the board itself (CSI 8 t); the chrome should follow."""

        def __init__(self, width: int, height: int) -> None:
            self.width = width
            self.height = height
            super().__init__()

    class LinkClicked(Monitor.LinkClicked):
        """An OSC 8 hyperlink was clicked (Terminal-flavoured handler name)."""

    def __init__(
        self,
        command: str | list[str] = "/bin/bash",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(board=Board(command=command, width=80, height=24), name=name, id=id, classes=classes)
        self._process = None  # our own handle: the board nulls its reference when it reaps
        self._exited = False
        self.mouse_mode = "off"  # the child's mouse-tracking mode, pushed by the chrome
        self.cwd = ""  # the child's OSC 7 working directory, as a plain path
        self.icon_title = ""  # OSC 1; stored but not rendered anywhere yet

    # --- lifecycle --- #

    async def on_mount(self) -> None:
        # Textual composites truecolor and downconverts for the real terminal itself;
        # the widget's own background is the closest physical fact to an OSC 11 answer.
        self._chrome.set_caps(TerminalCaps(color_depth="truecolor", background=self.background_colors[1].rgb))
        self.board.set_pty_data_callback(self.feed)
        await self.board.start_process()
        self._process = self.board.process
        super().on_mount()

    def on_unmount(self) -> None:
        self.board.stop_process()

    def _tick(self) -> None:
        if self._process is not None and not self._exited and self._process.poll() is not None:
            self._exited = True
            self._sync = False  # a dead child can't hold the frame hostage
            self.post_message(self.ProcessExited(self._process.poll()))
        super()._tick()

    def _board_size_changed(self, size: tuple[int, int]) -> None:
        # A change we didn't cause (our on_resize keeps them equal) is the child's
        # CSI 8 t — tell the chrome so the window can follow the board.
        if size != (self.size.width, self.size.height):
            self.post_message(self.BoardResized(*size))

    def _cursor_shown(self) -> bool:
        return super()._cursor_shown() and self.has_focus

    # --- sizing: widget -> board --- #

    def on_resize(self, event: events.Resize) -> None:
        if event.size.width and event.size.height:
            self.board.resize(event.size.width, event.size.height)

    # --- selection arbitration --- #

    @property
    def allow_select(self) -> bool:
        """Selection only while the child isn't tracking the mouse — they never fight."""
        return self.mouse_mode == "off"

    # --- input: Textual events -> the board's display port --- #

    def on_key(self, event: events.Key) -> None:
        *mods, base = event.key.split("+")
        modifier = _MODIFIERS[frozenset("alt" if mod == "meta" else mod for mod in mods)]
        if len(base) > 1 and base[0] == "f" and base[1:].isdigit():
            self.board.display.input_fkey(int(base[1:]), modifier)
        elif event.is_printable and event.character:
            self.board.display.input_key(event.character, modifier)
        else:
            # Named keys the board's keymap knows (up/home/pageup/...) pass through
            # by name; ones it doesn't are translated here. Unknown names are ignored.
            self.board.display.input_key(_NAMED_KEYS.get(base, base), modifier)
        event.stop()
        event.prevent_default()

    def on_paste(self, event: events.Paste) -> None:
        self.board.display.input_paste(event.text)
        event.stop()

    def _input_mouse(self, event: events.MouseEvent, button: int, event_type: str) -> None:
        modifiers = set()
        if event.shift:
            modifiers.add("shift")
        if event.meta:
            modifiers.add("meta")
        if event.ctrl:
            modifiers.add("ctrl")
        self.board.display.input_mouse(event.offset.x + 1, event.offset.y + 1, button, event_type, modifiers)

    def on_mouse_down(self, event: events.MouseDown) -> None:
        self._input_mouse(event, _MOUSE_BUTTONS.get(event.button, constants.MOUSE_BUTTON_LEFT), "press")

    def on_mouse_up(self, event: events.MouseUp) -> None:
        self._input_mouse(event, _MOUSE_BUTTONS.get(event.button, constants.MOUSE_BUTTON_LEFT), "release")

    def on_mouse_move(self, event: events.MouseMove) -> None:
        self._input_mouse(event, constants.MOUSE_BUTTON_MOVEMENT, "move")
        super().on_mouse_move(event)  # link hover pointer

    def on_mouse_scroll_down(self, event: events.MouseScrollDown) -> None:
        self._wheel(event, constants.MOUSE_BUTTON_WHEEL_DOWN, "down")

    def on_mouse_scroll_up(self, event: events.MouseScrollUp) -> None:
        self._wheel(event, constants.MOUSE_BUTTON_WHEEL_UP, "up")

    def _wheel(self, event: events.MouseEvent, button: int, arrow: str) -> None:
        """Wheel arbitration: tracking child, then alternate-scroll arrows, then Textual."""
        if self.mouse_mode != "off":
            self._input_mouse(event, button, "press")
            event.stop()
        elif self.board.blitter.in_alt_screen and self.board.modes.alternate_scroll_mode:
            for _ in range(3):
                self.board.display.input_key(arrow)
            event.stop()

    def on_focus(self) -> None:
        self.board.display.focus_in()
        self._refresh_cursor_row()

    def on_blur(self) -> None:
        self.board.display.focus_out()
        self._refresh_cursor_row()
