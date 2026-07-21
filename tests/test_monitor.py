"""Monitor: a display-only view of a Board — no process, board drives the size."""

from __future__ import annotations

from textual.app import App, ComposeResult

from textual_tty import Monitor


class MonitorApp(App):
    def compose(self) -> ComposeResult:
        yield Monitor(size=(20, 6))


async def test_monitor_spawns_no_process():
    app = MonitorApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        monitor = app.query_one(Monitor)
        assert monitor.board.process is None
        assert monitor.board.pty is None


async def test_feed_renders_without_manual_refresh():
    app = MonitorApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        monitor = app.query_one(Monitor)
        monitor.feed("\x1b[1;1Hplayback")
        await pilot.pause(0.1)  # a tick repaints
        assert "playback" in monitor.render_line(0).text


async def test_widget_sizes_itself_to_the_board():
    app = MonitorApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        monitor = app.query_one(Monitor)
        assert (monitor.size.width, monitor.size.height) == (20, 6)

        monitor.board.resize(33, 9)
        await pilot.pause(0.1)  # the tick notices and re-layouts
        assert (monitor.size.width, monitor.size.height) == (33, 9)


async def test_cursor_renders_without_focus():
    app = MonitorApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        monitor = app.query_one(Monitor)
        monitor.feed("ab")
        cursor_rgb = monitor.board.palette.cursor
        strip = monitor.render_line(0)
        assert strip._segments[1].style.bgcolor.triplet == cursor_rgb


async def test_sync_output_holds_frames():
    app = MonitorApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        monitor = app.query_one(Monitor)
        seen = monitor._seen_gen
        monitor.feed("\x1b[?2026hheld")
        await pilot.pause(0.1)
        assert monitor._seen_gen == seen
        monitor.feed("\x1b[?2026l")
        await pilot.pause(0.1)
        assert monitor._seen_gen > seen


async def test_selection_extracts_board_text():
    app = MonitorApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        monitor = app.query_one(Monitor)
        monitor.feed("hello cast")
        await pilot.mouse_down(Monitor, offset=(0, 0))
        await pilot.hover(Monitor, offset=(10, 0))
        await pilot.mouse_up(Monitor, offset=(10, 0))
        await pilot.pause()
        assert app.screen.get_selected_text() == "hello cast"
