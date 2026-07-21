"""Terminal: a Textual widget that is the chrome for a bittty Board.

The widget composes a Board (never subclasses it) and plugs a small chrome
adapter into the board's display port. Discrete side-effects (bell, title,
process exit) surface as ordinary Textual messages; screen content is pulled
from video memory in render_line, repainting only rows the board dirtied.
"""

from __future__ import annotations

from bittty import Board, TerminalCaps, constants
from bittty.terminals import Terminal as Chrome
from rich.segment import Segment
from rich.style import Style as RichStyle
from textual import events
from textual.geometry import Region
from textual.message import Message
from textual.strip import Strip
from textual.widget import Widget

from .styles import to_rich_style

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

_CURSOR = RichStyle(reverse=True)


class _Chrome(Chrome):
    """The board-facing jack: present events become Textual messages."""

    def __init__(self, widget: Terminal) -> None:
        super().__init__(widget.board)
        self.widget = widget

    def on_bell(self) -> None:
        self.widget.post_message(Terminal.Bell())

    def on_title(self, title: str, icon_title: str) -> None:
        self.widget.post_message(Terminal.TitleChanged(title, icon_title))


class Terminal(Widget):
    """A terminal emulator widget: a bittty Board rendered as Textual content."""

    can_focus = True

    DEFAULT_CSS = """
    Terminal {
        background: #000000;
        color: #e8e8e8;
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

    def __init__(
        self,
        command: str | list[str] = "/bin/bash",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.board = Board(command=command, width=80, height=24)
        self._chrome = _Chrome(self)
        self._chrome.attach()
        self._dirty = False
        self._seen_page = None  # video page rendered last frame
        self._seen_gen = -1  # its generation when we rendered it
        self._last_cursor: tuple[int, int] | None = None  # cursor cell drawn last frame
        self._process = None  # our own handle: the board nulls its reference when it reaps
        self._exited = False

    # --- lifecycle --- #

    async def on_mount(self) -> None:
        # Textual composites truecolor and downconverts for the real terminal itself.
        self._chrome.set_caps(TerminalCaps(color_depth="truecolor"))
        self.board.set_pty_data_callback(self._on_pty_data)
        await self.board.start_process()
        self._process = self.board.process
        self.set_interval(1 / 60, self._tick)

    def on_unmount(self) -> None:
        self.board.stop_process()

    # --- output: PTY -> video memory -> strips --- #

    def _on_pty_data(self, data: str) -> None:
        """Feed child output into the emulator; painting happens on the tick.

        A repaint per PTY chunk backpressures a flooding child, so the callback
        only parses and marks the frame dirty.
        """
        self.board.parser.feed(data)
        self._dirty = True

    def _tick(self) -> None:
        if self._process is not None and not self._exited and self._process.poll() is not None:
            self._exited = True
            self.post_message(self.ProcessExited(self._process.poll()))
        if not self._dirty:
            return
        self._dirty = False

        page = self.board.blitter.current_buffer
        rows = set(page.dirty_rows(self._seen_gen)) if page is self._seen_page else set(range(page.height))
        self._seen_page = page
        self._seen_gen = page.observe()

        # Cursor motion doesn't touch video memory, so track its row ourselves.
        cursor = (self.board.cursor.x, self.board.cursor.y) if self.board.modes.cursor_visible else None
        if cursor != self._last_cursor:
            for old in (self._last_cursor, cursor):
                if old is not None:
                    rows.add(old[1])
            self._last_cursor = cursor

        if len(rows) >= self.size.height:
            self.refresh()
        else:
            width = self.size.width
            self.refresh(*(Region(0, y, width, 1) for y in rows))

    def render_line(self, y: int) -> Strip:
        page = self.board.blitter.current_buffer
        width = self.size.width
        if y >= page.height:
            return Strip.blank(width)

        cursor_x = -1
        if self.has_focus and self.board.modes.cursor_visible and y == self.board.cursor.y:
            cursor_x = self.board.cursor.x

        segments = []
        run: list[str] = []
        run_style = None
        row = page.grid[y]
        for x, (style, char) in enumerate(row[:width]):
            if x == cursor_x:
                if run:
                    segments.append(Segment("".join(run), to_rich_style(run_style)))
                    run = []
                segments.append(Segment(char, to_rich_style(style) + _CURSOR))
                run_style = None
                continue
            if style is not run_style and style != run_style:
                if run:
                    segments.append(Segment("".join(run), to_rich_style(run_style)))
                    run = []
                run_style = style
            run.append(char)
        if run:
            segments.append(Segment("".join(run), to_rich_style(run_style)))
        return Strip(segments).adjust_cell_length(width)

    def on_resize(self, event: events.Resize) -> None:
        if event.size.width and event.size.height:
            self.board.resize(event.size.width, event.size.height)

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

    def on_mouse_scroll_down(self, event: events.MouseScrollDown) -> None:
        self._input_mouse(event, constants.MOUSE_BUTTON_WHEEL_DOWN, "press")

    def on_mouse_scroll_up(self, event: events.MouseScrollUp) -> None:
        self._input_mouse(event, constants.MOUSE_BUTTON_WHEEL_UP, "press")

    def on_focus(self) -> None:
        self.board.display.focus_in()
        self._refresh_cursor_row()

    def on_blur(self) -> None:
        self.board.display.focus_out()
        self._refresh_cursor_row()

    def _refresh_cursor_row(self) -> None:
        """The cursor only draws when focused, so focus changes repaint its row."""
        self.refresh(Region(0, self.board.cursor.y, self.size.width, 1))
