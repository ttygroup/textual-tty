"""Present events from the board surface as Textual messages."""

from __future__ import annotations

from conftest import TerminalApp, wait_for

from textual_tty import Terminal


async def test_title_change_posts_message():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term = app.query_one(Terminal)
        await pilot.pause()
        term.board.parser.feed("\x1b]0;my session\x07")
        await pilot.pause()
        assert app.titles == [("my session", "my session")]


async def test_bell_posts_message():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term = app.query_one(Terminal)
        await pilot.pause()
        term.board.parser.feed("\x07\x07")
        await pilot.pause()
        assert app.bells == 2


async def test_process_exit_posts_exit_code():
    app = TerminalApp(["sh", "-c", "exit 3"])
    async with app.run_test(size=(40, 10)) as pilot:
        await wait_for(pilot, lambda: app.exit_codes)
        assert app.exit_codes == [3]
