"""Text selection over video memory, and OSC 8 hyperlink click-through."""

from __future__ import annotations

import os

os.environ.setdefault("BROWSER", "true")  # ctrl+click "opens" harmlessly in tests

from conftest import TerminalApp

from textual_tty import Terminal

LINK = "\x1b]8;;https://example.com\x07click me\x1b]8;;\x07"


async def test_drag_selects_text_from_video_memory():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term = app.query_one(Terminal)
        await pilot.pause()
        term.board.parser.feed("hello world")
        await pilot.mouse_down(Terminal, offset=(0, 0))
        await pilot.hover(Terminal, offset=(11, 0))
        await pilot.mouse_up(Terminal, offset=(11, 0))
        await pilot.pause()
        assert app.screen.get_selected_text() == "hello world"


async def test_selection_is_disabled_while_child_tracks_mouse():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term = app.query_one(Terminal)
        await pilot.pause()
        assert term.allow_select is True
        term.board.parser.feed("\x1b[?1000h\x1b[?1006h")
        await pilot.pause(0.1)
        assert term.allow_select is False


class LinkApp(TerminalApp):
    def __init__(self, command) -> None:
        super().__init__(command)
        self.clicked: list[tuple[str, str | None]] = []

    def on_terminal_link_clicked(self, message: Terminal.LinkClicked) -> None:
        self.clicked.append((message.uri, message.link_id))


async def test_link_click_posts_message():
    app = LinkApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term = app.query_one(Terminal)
        await pilot.pause()
        term.board.parser.feed(LINK)

        await pilot.click(Terminal, offset=(2, 0))
        await pilot.pause()
        assert app.clicked == [("https://example.com", None)]

        app.clicked.clear()
        await pilot.click(Terminal, offset=(30, 5))  # not a link cell
        await pilot.pause()
        assert app.clicked == []


async def test_link_hover_shows_pointer():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term = app.query_one(Terminal)
        await pilot.pause()
        term.board.parser.feed(LINK)
        await pilot.hover(Terminal, offset=(2, 0))
        assert term.styles.pointer == "pointer"
        await pilot.hover(Terminal, offset=(30, 5))
        assert term.styles.pointer == "default"
