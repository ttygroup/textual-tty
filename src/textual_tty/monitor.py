"""Monitor: a Textual widget that renders a bittty Board's video memory.

A monitor is chrome that only displays: board in, cells out. It has no child
process, no keyboard, and no capabilities to report — players, recorders and
preview panes compose one directly (`Monitor(size=(80, 24))`, then `feed()`).
`Terminal` subclasses it and adds the terminal-ness: process lifecycle, input
forwarding, caps, window messages.

Sizing runs board -> widget here: the widget's content size is the board's
grid, so `width: auto` fits the view to the cast. (Terminal reverses this and
drives the board from the widget's layout size.)
"""

from __future__ import annotations

import webbrowser

from bittty import Board
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


class MonitorChrome(Chrome):
    """The board-facing jack for a display-only view: render hooks only."""

    def __init__(self, widget: Monitor) -> None:
        super().__init__(widget.board)
        self.widget = widget

    def on_sync_output(self, enabled: bool) -> None:
        self.widget.set_sync_output(enabled)


class Monitor(Widget):
    """A read-only view of a bittty Board: video memory rendered as strips."""

    can_focus = False
    CHROME: type[MonitorChrome] = MonitorChrome

    DEFAULT_CSS = """
    Monitor {
        background: #000000;
        color: #e8e8e8;
        width: auto;
        height: auto;
    }
    """

    class LinkClicked(Message):
        """An OSC 8 hyperlink was clicked."""

        def __init__(self, uri: str, link_id: str | None) -> None:
            self.uri = uri
            self.link_id = link_id
            super().__init__()

    def __init__(
        self,
        board: Board | None = None,
        size: tuple[int, int] = (80, 24),
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.board = board if board is not None else Board(width=size[0], height=size[1])
        self._chrome = self.CHROME(self)
        self._chrome.attach()
        self._dirty = False
        self._seen_page = None  # video page rendered last frame
        self._seen_gen = -1  # its generation when we rendered it
        self._last_cursor: tuple[int, int] | None = None  # cursor cell drawn last frame
        self._style_cache: dict = {}  # bittty Style -> Rich Style, valid for one palette generation
        self._palette_gen = -1
        self._sync = False  # mode 2026: hold repaints until the feed releases the frame
        self._cursor_phase = True  # blink: False hides the cursor for half a period
        self._board_size = (self.board.width, self.board.height)  # re-layout when the board resizes
        self._base_pointer = "default"  # the OSC 22 shape; link hover overrides it transiently

    # --- lifecycle --- #

    def on_mount(self) -> None:
        self.set_interval(1 / 60, self._tick)
        self.set_interval(0.5, self._blink)

    # --- feeding: bytes -> video memory -> strips on the tick --- #

    def feed(self, data: str) -> None:
        """Feed terminal output into the emulator; painting happens on the tick.

        A repaint per chunk backpressures a flooding source, so this only
        parses and marks the frame dirty.
        """
        self.board.parser.feed(data)
        self._dirty = True

    def set_sync_output(self, enabled: bool) -> None:
        """Mode 2026: hold repaints while the source composes a frame."""
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

    def _board_size_changed(self, size: tuple[int, int]) -> None:
        """The board's grid changed shape: re-run auto sizing."""
        self.refresh(layout=True)

    def _tick(self) -> None:
        self._check_palette()
        board_size = (self.board.width, self.board.height)
        if board_size != self._board_size:
            self._board_size = board_size
            self._board_size_changed(board_size)
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

    # --- sizing: board -> widget --- #

    def get_content_width(self, container, viewport) -> int:
        return self.board.width

    def get_content_height(self, container, viewport, width: int) -> int:
        return self.board.height

    # --- cursor --- #

    def _cursor_shown(self) -> bool:
        """Whether the cursor is composited at all (blink phase aside)."""
        return self.board.modes.cursor_visible

    def _cursor_style(self, base: RichStyle) -> RichStyle:
        """The cursor cell's style: shape-aware (DECSCUSR), coloured by OSC 12.

        A cell grid can't draw a bar, so bar falls back to the block look.
        """
        if self.board.cursor.shape == "underline":
            return base + RichStyle(underline=True)
        palette = self.board.palette
        return base + RichStyle(color=rich_color(palette.background), bgcolor=rich_color(palette.cursor))

    def _blink(self) -> None:
        """Toggle the blink phase while a blinking cursor is shown."""
        if self._cursor_shown() and self.board.modes.cursor_blinking:
            self._cursor_phase = not self._cursor_phase
            self._refresh_cursor_row()
        elif not self._cursor_phase:
            self._cursor_phase = True
            self._refresh_cursor_row()

    def _refresh_cursor_row(self) -> None:
        self.refresh(Region(0, self.board.cursor.y, self.size.width, 1))

    # --- rendering --- #

    def render_line(self, y: int) -> Strip:
        page = self.board.blitter.current_buffer
        width = self.size.width
        if y >= page.height:
            return Strip.blank(width)

        cursor_x = -1
        if self._cursor_shown() and self._cursor_phase and y == self.board.cursor.y:
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
        strip = Strip(segments).adjust_cell_length(width)

        selection = self.text_selection
        if selection is not None:
            span = selection.get_span(y)
            if span is not None:
                start, end = span
                if end == -1:
                    end = width
                style = self.screen.get_component_rich_style("screen--selection")
                before, selected, after = strip.divide([start, end, width])
                strip = Strip.join([before, selected.apply_style(style), after])
        return strip

    # --- selection: Textual's built-in machinery over video memory --- #

    def get_selection(self, selection) -> tuple[str, str] | None:
        page = self.board.blitter.current_buffer
        text = "\n".join(page.get_line_text(y).rstrip() for y in range(page.height))
        return selection.extract(text), "\n"

    def selection_updated(self, selection) -> None:
        self.refresh()

    # --- hyperlinks + pointer --- #

    def set_pointer(self, shape: str) -> None:
        """OSC 22 — adopt the source's requested mouse-pointer shape."""
        mapped = _POINTER_SHAPES.get(shape, shape)
        self._base_pointer = mapped if mapped in VALID_POINTER else "default"
        self.styles.pointer = self._base_pointer

    def on_mouse_move(self, event: events.MouseMove) -> None:
        # Hovering an OSC 8 link shows a hand; leaving restores the base shape.
        pointer = "pointer" if self.board.link_at(event.offset.x, event.offset.y) else self._base_pointer
        if self.styles.pointer != pointer:
            self.styles.pointer = pointer

    def on_click(self, event: events.Click) -> None:
        link = self.board.link_at(event.offset.x, event.offset.y)
        if link is None:
            return
        uri, link_id = link
        self.post_message(self.LinkClicked(uri, link_id))
        if event.ctrl:
            webbrowser.open(uri)
