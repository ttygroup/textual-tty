"""Window: drag to move, grip to resize, close button closes."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Static

from conftest import drag

from textual_tty.window import CloseButton, ResizeGrip, TitleBar, Window


class WindowApp(App):
    def compose(self) -> ComposeResult:
        yield Window(Static("content"), title="test window", id="win")


async def test_title_shows_in_title_bar():
    app = WindowApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        assert "test window" in app.query_one(TitleBar).render_line(0).text
        app.query_one(Window).title = "renamed"
        await pilot.pause()
        assert "renamed" in app.query_one(TitleBar).render_line(0).text


async def test_dragging_title_bar_moves_window():
    app = WindowApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        window = app.query_one(Window)
        before = window.offset
        await drag(pilot, TitleBar, (5, 3))
        assert window.offset == before + (5, 3)


async def test_dragging_grip_resizes_window():
    app = WindowApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        window = app.query_one(Window)
        before = window.region.size
        await drag(pilot, ResizeGrip, (6, 2))
        await pilot.pause()
        assert window.region.size == (before.width + 6, before.height + 2)


async def test_resize_clamps_to_minimum():
    app = WindowApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        window = app.query_one(Window)
        grip = app.query_one(ResizeGrip)
        # Drag to the screen origin: a huge negative total that must clamp.
        await drag(pilot, ResizeGrip, -grip.region.offset)
        await pilot.pause()
        assert window.region.size == (Window.MIN_WIDTH, Window.MIN_HEIGHT)


async def test_close_button_removes_window():
    app = WindowApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        await pilot.click(CloseButton)
        await pilot.pause()
        assert not app.query(Window)
