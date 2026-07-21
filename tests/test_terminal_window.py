"""TerminalWindow: the wiring between a Terminal and its Window."""

from __future__ import annotations

from textual.app import App, ComposeResult

from conftest import CaptureConnection, drag, wait_for

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


async def test_child_moves_its_own_window():
    app = DesktopApp(["sleep", "60"])
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        window = app.query_one(TerminalWindow)
        window.terminal.board.parser.feed("\x1b[3;10;5t")
        await pilot.pause()
        assert (window.offset.x, window.offset.y) == (10, 5)


async def test_child_maximizes_and_restores_its_window():
    app = DesktopApp(["sleep", "60"])
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        window = app.query_one(TerminalWindow)
        before = (window.offset, window.region.size)
        window.terminal.board.parser.feed("\x1b[9;1t")
        await pilot.pause()
        assert window.region.size == window.parent.size

        window.terminal.board.parser.feed("\x1b[9;0t")
        await pilot.pause()
        assert (window.offset, window.region.size) == before


async def test_child_resizes_board_and_window_follows():
    app = DesktopApp(["sleep", "60"])
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        window = app.query_one(TerminalWindow)
        window.terminal.board.parser.feed("\x1b[8;20;60t")  # rows;cols
        await pilot.pause(0.1)
        assert (window.terminal.board.width, window.terminal.board.height) == (60, 20)
        assert window.region.size == (62, 22)  # board + side bands / header + footer


async def test_window_position_query_reports_the_dragged_position():
    app = DesktopApp(["sleep", "60"])
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        window = app.query_one(TerminalWindow)
        board = window.terminal.board
        await drag(pilot, TitleBar, (7, 4))
        capture = CaptureConnection()
        board.pty = capture
        board.parser.feed("\x1b[13t")
        assert capture.data == f"\x1b[3;{window.offset.x};{window.offset.y}t"
        assert (window.offset.x, window.offset.y) != (0, 0)


async def test_child_raises_and_lowers_its_window():
    class TwoWindows(App):
        def compose(self) -> ComposeResult:
            yield TerminalWindow(command=["sleep", "60"], id="one")
            yield TerminalWindow(command=["sleep", "60"], id="two")

    app = TwoWindows()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        one = app.query_one("#one", TerminalWindow)
        assert app.screen.children[-1].id == "two"

        one.terminal.board.parser.feed("\x1b[5t")  # raise
        await pilot.pause()
        assert app.screen.children[-1].id == "one"

        one.terminal.board.parser.feed("\x1b[6t")  # lower
        await pilot.pause()
        assert app.screen.children[0].id == "one"
