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
        # Indexed colours resolve through the board's palette to concrete RGB.
        from bittty.style import Color

        assert segment.style.color.triplet == term.board.palette.resolve(Color("indexed", 1))
        assert segment.style.bold is True


async def test_strip_is_padded_to_widget_width():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term = app.query_one(Terminal)
        await pilot.pause()
        term.board.parser.feed("hi")
        assert term.render_line(0).cell_length == term.size.width


async def test_cursor_renders_in_cursor_colour_when_focused():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term = app.query_one(Terminal)
        term.focus()
        await pilot.pause()
        term.board.parser.feed("abc")
        assert (term.board.cursor.x, term.board.cursor.y) == (3, 0)
        cursor_rgb = term.board.palette.cursor
        strip = term.render_line(0)
        cursor_segment = strip._segments[1]  # after the "abc" run
        assert cursor_segment.style.bgcolor.triplet == cursor_rgb

        # Unfocused, the cursor cell isn't composited.
        app.set_focus(None)
        await pilot.pause()
        strip = term.render_line(0)
        assert all(not (segment.style and segment.style.bgcolor) for segment in strip._segments)


async def test_cursor_shape_underline():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term = app.query_one(Terminal)
        term.focus()
        await pilot.pause()
        term.board.parser.feed("x\x1b[4 q")  # DECSCUSR 4: steady underline
        strip = term.render_line(0)
        cursor_segment = strip._segments[1]
        assert cursor_segment.style.underline is True
        assert cursor_segment.style.bgcolor is None


async def test_blinking_cursor_phase_hides_cursor():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term = app.query_one(Terminal)
        term.focus()
        await pilot.pause()
        term.board.parser.feed("x\x1b[1 q")  # DECSCUSR 1: blinking block
        assert term.board.modes.cursor_blinking
        term._cursor_phase = False  # the half-period the timer toggles into
        strip = term.render_line(0)
        assert all(not (segment.style and segment.style.bgcolor) for segment in strip._segments)


async def test_osc4_redefines_a_colour_and_invalidates_the_cache():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term = app.query_one(Terminal)
        await pilot.pause()
        term.board.parser.feed("\x1b[31mred")
        await pilot.pause(0.1)  # a tick caches the conversion
        term.board.parser.feed("\x1b]4;1;#123456\x07")
        await pilot.pause(0.1)  # a tick sees the new palette generation
        segment = term.render_line(0)._segments[0]
        assert segment.style.color.triplet == (0x12, 0x34, 0x56)


async def test_osc11_tints_the_widget_background():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term = app.query_one(Terminal)
        await pilot.pause()
        term.board.parser.feed("\x1b]11;#204060\x07")
        await pilot.pause(0.1)
        assert term.styles.background.rgb == (0x20, 0x40, 0x60)


async def test_sync_output_holds_repaints():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term = app.query_one(Terminal)
        await pilot.pause()
        seen = term._seen_gen
        term._on_pty_data("\x1b[?2026hheld text")  # the production feed path marks dirty
        await pilot.pause(0.1)
        assert term._seen_gen == seen  # ticks passed, no observation happened
        term._on_pty_data("\x1b[?2026l")
        await pilot.pause(0.1)
        assert term._seen_gen > seen
        assert "held text" in term.render_line(0).text


async def test_tick_repaints_only_dirty_rows():
    app = TerminalApp(["sleep", "60"])
    async with app.run_test(size=(40, 10)) as pilot:
        term = app.query_one(Terminal)
        await pilot.pause()  # let the startup frames settle
        page = term.board.blitter.current_buffer
        seen = page.observe()
        term.board.parser.feed("\x1b[5;1Hxyz")
        assert page.dirty_rows(seen) == [4]
