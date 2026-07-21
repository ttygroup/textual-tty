"""TerminalWindow: the wiring between a Terminal and its Window."""

from __future__ import annotations

from textual.app import App, ComposeResult

from conftest import drag, wait_for

from textual_tty import Terminal, TerminalWindow
from textual_tty.window import ResizeGrip, TitleBar


class DesktopApp(App):
    def __init__(self, command) -> None:
        super().__init__()
        self.command = command

    def compose(self) -> ComposeResult:
        yield TerminalWindow(command=self.command)


async def test_window_closes_when_process_exits():
    app = DesktopApp(["sh", "-c", "exit 0"])
    async with app.run_test(size=(100, 30)) as pilot:
        await wait_for(pilot, lambda: not app.query(TerminalWindow))


async def test_title_follows_osc():
    app = DesktopApp(["sleep", "60"])
    async with app.run_test(size=(100, 30)) as pilot:
        await pilot.pause()
        window = app.query_one(TerminalWindow)
        window.terminal.board.parser.feed("\x1b]2;vim README.md\x07")
        await pilot.pause()
        assert window.title == "vim README.md"
        assert "vim README.md" in app.query_one(TitleBar).render_line(0).text


async def test_terminal_gets_focus_on_mount():
    app = DesktopApp(["sleep", "60"])
    async with app.run_test(size=(100, 30)) as pilot:
        await pilot.pause()
        assert isinstance(app.focused, Terminal)


async def test_resizing_window_reflows_the_board():
    app = DesktopApp(["sleep", "60"])
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        window = app.query_one(TerminalWindow)
        board = window.terminal.board
        before = (board.width, board.height)
        await drag(pilot, ResizeGrip, (8, 4))
        await pilot.pause()
        assert (board.width, board.height) == (before[0] + 8, before[1] + 4)
