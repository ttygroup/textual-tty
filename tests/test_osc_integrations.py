"""OSC side-effects reach the hosting app: notify, clipboard, cwd, pointer, icon title."""

from __future__ import annotations

import base64

from conftest import TerminalApp

from textual_tty import Terminal


async def test_osc9_raises_a_textual_notification():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term = app.query_one(Terminal)
        await pilot.pause()
        term.board.parser.feed("\x1b]9;build finished\x07")
        await pilot.pause()
        assert len(app._notifications) == 1


async def test_osc52_copies_to_the_app_clipboard():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term = app.query_one(Terminal)
        await pilot.pause()
        payload = base64.b64encode(b"copied text").decode()
        term.board.parser.feed(f"\x1b]52;c;{payload}\x07")
        await pilot.pause()
        assert app.clipboard == "copied text"


async def test_osc7_sets_cwd_as_a_plain_path():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term = app.query_one(Terminal)
        await pilot.pause()
        term.board.parser.feed("\x1b]7;file://myhost/home/gaz/src%20dir\x07")
        await pilot.pause()
        assert term.cwd == "/home/gaz/src dir"


async def test_osc22_sets_the_pointer_shape():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term = app.query_one(Terminal)
        await pilot.pause()
        term.board.parser.feed("\x1b]22;hand2\x07")
        await pilot.pause()
        assert term.styles.pointer == "pointer"

        term.board.parser.feed("\x1b]22;definitely-not-a-shape\x07")
        await pilot.pause()
        assert term.styles.pointer == "default"


async def test_osc1_stores_icon_title():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term = app.query_one(Terminal)
        await pilot.pause()
        term.board.parser.feed("\x1b]1;iconic\x07")
        await pilot.pause()
        assert term.icon_title == "iconic"
