"""Terminal: a Textual widget that is the chrome for a bittty Board.

The widget composes a Board (never subclasses it) and plugs a small chrome
adapter into the board's display port. Discrete side-effects (bell, title,
process exit) surface as ordinary Textual messages; screen content is pulled
from video memory in render_line, repainting only rows the board dirtied.
"""

from __future__ import annotations

from urllib.parse import unquote, urlparse

from bittty import Board, TerminalCaps, constants
from bittty.terminals import Terminal as Chrome
from rich.segment import Segment
from rich.style import Style as RichStyle
from textual import events
from textual.color import Color as TextualColor
from textual.css.constants import VALID_POINTER
from textual.geometry import Region
from textual.message import Message
from textual.strip import Strip
from textual.widget import Widget

from .styles import rich_color, to_rich_style

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

# X11 cursor-font names (what OSC 22 usually carries) -> Textual pointer shapes.
# Names already valid for Textual pass straight through.
_POINTER_SHAPES = {
    "xterm": "text",
    "ibeam": "text",
    "hand": "pointer",
    "hand1": "pointer",
    "hand2": "pointer",
    "cross": "crosshair",
    "watch": "wait",
    "left_ptr": "default",
}


def _cwd_path(cwd: str) -> str:
    """OSC 7 carries a file:// URL; give apps a plain path."""
    if cwd.startswith("file://"):
        return unquote(urlparse(cwd).path)
    return cwd


class _Chrome(Chrome):
    """The board-facing jack: present events become Textual messages."""

    def __init__(self, widget: Terminal) -> None:
        super().__init__(widget.board)
        self.widget = widget

    def on_bell(self) -> None:
        self.widget.post_message(Terminal.Bell())

    def on_title(self, title: str, icon_title: str) -> None:
        self.widget.icon_title = icon_title
        self.widget.post_message(Terminal.TitleChanged(title, icon_title))

    def on_sync_output(self, enabled: bool) -> None:
        self.widget.set_sync_output(enabled)

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
        self._style_cache: dict = {}  # bittty Style -> Rich Style, valid for one palette generation
        self._palette_gen = -1
        self._sync = False  # mode 2026: hold repaints until the child releases the frame
        self._cursor_phase = True  # blink: False hides the cursor for half a period
        self.mouse_mode = "off"  # the child's mouse-tracking mode, pushed by the chrome
        self._board_size = (self.board.width, self.board.height)  # detects child-driven CSI 8 t resizes
        self.cwd = ""  # the child's OSC 7 working directory, as a plain path
        self.icon_title = ""  # OSC 1; stored but not rendered anywhere yet
        self._base_pointer = "default"  # the OSC 22 shape; link hover overrides it transiently

    # --- lifecycle --- #

    def set_pointer(self, shape: str) -> None:
        """OSC 22 — adopt the child's requested mouse-pointer shape."""
        mapped = _POINTER_SHAPES.get(shape, shape)
        self._base_pointer = mapped if mapped in VALID_POINTER else "default"
        self.styles.pointer = self._base_pointer

    async def on_mount(self) -> None:
        # Textual composites truecolor and downconverts for the real terminal itself;
        # the widget's own background is the closest physical fact to an OSC 11 answer.
        self._chrome.set_caps(TerminalCaps(color_depth="truecolor", background=self.background_colors[1].rgb))
        self.board.set_pty_data_callback(self._on_pty_data)
        await self.board.start_process()
        self._process = self.board.process
        self.set_interval(1 / 60, self._tick)
        self.set_interval(0.5, self._blink)

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

    def set_sync_output(self, enabled: bool) -> None:
        """Mode 2026: hold repaints while the child composes a frame."""
        self._sync = enabled
        if not enabled:
            self._dirty = True  # flush everything held back during the sync

    def _check_palette(self) -> None:
        """A palette op ran: drop cached conversions and re-tint the widget defaults."""
        palette = self.board.palette
        if palette.generation == self._palette_gen:
            return
        self._palette_gen = palette.generation
        self._style_cache.clear()
        self.styles.color = TextualColor(*palette.foreground)
        self.styles.background = TextualColor(*palette.background)
        self.refresh()

    def _to_rich(self, style) -> RichStyle:
        cached = self._style_cache.get(style)
        if cached is None:
            cached = self._style_cache[style] = to_rich_style(style, self.board.palette)
        return cached

    def _tick(self) -> None:
        if self._process is not None and not self._exited and self._process.poll() is not None:
            self._exited = True
            self._sync = False  # a dead child can't hold the frame hostage
            self.post_message(self.ProcessExited(self._process.poll()))
        self._check_palette()
        board_size = (self.board.width, self.board.height)
        if board_size != self._board_size:
            self._board_size = board_size
            # A change we didn't cause (our on_resize keeps them equal) is the child's
            # CSI 8 t — tell the chrome so the window can follow the board.
            if board_size != (self.size.width, self.size.height):
                self.post_message(self.BoardResized(*board_size))
        if not self._dirty or self._sync:
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

    def _cursor_style(self, base: RichStyle) -> RichStyle:
        """The cursor cell's style: shape-aware (DECSCUSR), coloured by OSC 12.

        A cell grid can't draw a bar, so bar falls back to the block look.
        """
        if self.board.cursor.shape == "underline":
            return base + RichStyle(underline=True)
        palette = self.board.palette
        return base + RichStyle(color=rich_color(palette.background), bgcolor=rich_color(palette.cursor))

    def _blink(self) -> None:
        """Toggle the blink phase while a blinking cursor is focused."""
        if self.has_focus and self.board.modes.cursor_blinking:
            self._cursor_phase = not self._cursor_phase
            self._refresh_cursor_row()
        elif not self._cursor_phase:
            self._cursor_phase = True
            self._refresh_cursor_row()

    def render_line(self, y: int) -> Strip:
        page = self.board.blitter.current_buffer
        width = self.size.width
        if y >= page.height:
            return Strip.blank(width)

        cursor_x = -1
        if self.has_focus and self._cursor_phase and self.board.modes.cursor_visible and y == self.board.cursor.y:
            cursor_x = self.board.cursor.x

        segments = []
        run: list[str] = []
        run_style = None
        row = page.grid[y]
        for x, (style, char) in enumerate(row[:width]):
            if x == cursor_x:
                if run:
                    segments.append(Segment("".join(run), self._to_rich(run_style)))
                    run = []
                segments.append(Segment(char, self._cursor_style(self._to_rich(style))))
                run_style = None
                continue
            if style is not run_style and style != run_style:
                if run:
                    segments.append(Segment("".join(run), self._to_rich(run_style)))
                    run = []
                run_style = style
            run.append(char)
        if run:
            segments.append(Segment("".join(run), self._to_rich(run_style)))
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

    def _refresh_cursor_row(self) -> None:
        """The cursor only draws when focused, so focus changes repaint its row."""
        self.refresh(Region(0, self.board.cursor.y, self.size.width, 1))
