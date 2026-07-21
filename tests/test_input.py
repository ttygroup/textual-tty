"""Textual input events reach the child through the board's display port."""

from __future__ import annotations

from textual import events

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


async def test_paste_is_raw_without_bracketed_mode():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term, capture = await _terminal_with_capture(app, pilot)
        term.post_message(events.Paste("hello world"))
        await pilot.pause()
        assert capture.data == "hello world"


async def test_paste_is_bracketed_when_child_enables_2004():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term, capture = await _terminal_with_capture(app, pilot)
        term.board.parser.feed("\x1b[?2004h")
        term.post_message(events.Paste("hello"))
        await pilot.pause()
        assert capture.data == "\x1b[200~hello\x1b[201~"


async def test_wheel_reports_when_child_tracks_mouse():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term, capture = await _terminal_with_capture(app, pilot)
        term.board.parser.feed("\x1b[?1000h\x1b[?1006h")
        await pilot.pause(0.1)  # the chrome pushes the new mouse mode
        assert term.mouse_mode == "basic"
        await pilot.mouse_down(Terminal, offset=(5, 3), button=4)  # wheel-up in Textual terms
        term.post_message(events.MouseScrollUp(term, 5, 3, 0, 0, 0, False, False, False))
        await pilot.pause()
        assert "\x1b[<64;6;4M" in capture.data


async def test_wheel_becomes_arrows_in_alternate_scroll():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term, capture = await _terminal_with_capture(app, pilot)
        term.board.parser.feed("\x1b[?1049h\x1b[?1007h")  # alt screen + alternate scroll
        term.post_message(events.MouseScrollDown(term, 5, 3, 0, 0, 0, False, False, False))
        await pilot.pause()
        assert capture.data == "\x1b[B\x1b[B\x1b[B"


async def test_wheel_is_silent_when_nothing_wants_it():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term, capture = await _terminal_with_capture(app, pilot)
        term.post_message(events.MouseScrollDown(term, 5, 3, 0, 0, 0, False, False, False))
        await pilot.pause()
        assert capture.data == ""
