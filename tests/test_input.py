"""Textual input events reach the child through the board's display port."""

from __future__ import annotations

from conftest import CaptureConnection, TerminalApp

from textual_tty import Terminal


async def _terminal_with_capture(app, pilot):
    term = app.query_one(Terminal)
    term.focus()
    await pilot.pause()
    capture = CaptureConnection()
    term.board.pty = capture  # swap the transmit pin; the child keeps sleeping
    return term, capture


async def test_keys_are_encoded_by_the_board():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term, capture = await _terminal_with_capture(app, pilot)
        await pilot.press("a", "enter", "up", "home", "f5", "ctrl+c", "backspace")
        assert capture.data == "a\r\x1b[A\x1b[H\x1b[15~\x03\x7f"


async def test_tab_stays_in_the_terminal():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term, capture = await _terminal_with_capture(app, pilot)
        await pilot.press("tab")
        assert capture.data == "\t"
        assert app.focused is term  # tab must not move Textual focus


async def test_mouse_reports_only_when_child_enables_tracking():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term, capture = await _terminal_with_capture(app, pilot)

        await pilot.click(Terminal, offset=(5, 3))
        assert capture.data == ""  # tracking off: the child hears nothing

        term.board.parser.feed("\x1b[?1000h\x1b[?1006h")
        await pilot.click(Terminal, offset=(5, 3))
        assert "\x1b[<0;6;4M" in capture.data  # SGR press, 1-based coords
        assert "\x1b[<0;6;4m" in capture.data  # SGR release


async def test_focus_reports_when_child_enables_1004():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term, capture = await _terminal_with_capture(app, pilot)
        term.board.parser.feed("\x1b[?1004h")
        app.set_focus(None)
        await pilot.pause()
        term.focus()
        await pilot.pause()
        assert "\x1b[O" in capture.data
        assert "\x1b[I" in capture.data
