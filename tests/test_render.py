"""The Terminal widget renders the board's video memory as strips."""

from __future__ import annotations

from conftest import TerminalApp, wait_for

from textual_tty import Terminal


async def test_child_output_renders():
    app = TerminalApp(["sh", "-c", "echo hello world; sleep 60"])
    async with app.run_test(size=(60, 20)) as pilot:
        term = app.query_one(Terminal)
        await wait_for(pilot, lambda: "hello world" in term.render_line(0).text)


async def test_board_follows_widget_size():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(60, 20)) as pilot:
        term = app.query_one(Terminal)
        await pilot.pause()
        assert (term.board.width, term.board.height) == (term.size.width, term.size.height)


async def test_sgr_colors_reach_the_strip():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term = app.query_one(Terminal)
        await pilot.pause()
        term.board.parser.feed("\x1b[31;1mred bold")
        strip = term.render_line(0)
        segment = strip._segments[0]
        assert segment.text.startswith("red bold")
        assert segment.style.color.number == 1
        assert segment.style.bold is True


async def test_strip_is_padded_to_widget_width():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term = app.query_one(Terminal)
        await pilot.pause()
        term.board.parser.feed("hi")
        assert term.render_line(0).cell_length == term.size.width


async def test_cursor_renders_reversed_when_focused():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term = app.query_one(Terminal)
        term.focus()
        await pilot.pause()
        term.board.parser.feed("abc")
        assert (term.board.cursor.x, term.board.cursor.y) == (3, 0)
        strip = term.render_line(0)
        cursor_segment = strip._segments[1]  # after the "abc" run
        assert cursor_segment.style.reverse is True

        # Unfocused, the cursor cell isn't composited.
        app.set_focus(None)
        await pilot.pause()
        strip = term.render_line(0)
        assert all(not (segment.style and segment.style.reverse) for segment in strip._segments)


async def test_tick_repaints_only_dirty_rows():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term = app.query_one(Terminal)
        await pilot.pause()  # let the startup frames settle
        page = term.board.blitter.current_buffer
        seen = page.observe()
        term.board.parser.feed("\x1b[5;1Hxyz")
        assert page.dirty_rows(seen) == [4]
