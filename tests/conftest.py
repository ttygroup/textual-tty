"""Shared fixtures: real apps, real boards, real children — no mocks."""

from __future__ import annotations

from textual.app import App, ComposeResult

from textual_tty import Terminal


class TerminalApp(App):
    """A minimal app hosting one Terminal, recording its messages."""

    def __init__(self, command: str | list[str]) -> None:
        super().__init__()
        self.command = command
        self.titles: list[tuple[str, str]] = []
        self.bells = 0
        self.exit_codes: list[int] = []

    def compose(self) -> ComposeResult:
        yield Terminal(command=self.command)

    def on_terminal_title_changed(self, message: Terminal.TitleChanged) -> None:
        self.titles.append((message.title, message.icon_title))

    def on_terminal_bell(self, message: Terminal.Bell) -> None:
        self.bells += 1

    def on_terminal_process_exited(self, message: Terminal.ProcessExited) -> None:
        self.exit_codes.append(message.exit_code)


class CaptureConnection:
    """A capture jack for the host port: collects bytes headed to the child."""

    def __init__(self) -> None:
        self.written: list[str] = []

    def write(self, data: str) -> None:
        self.written.append(data)

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass

    @property
    def data(self) -> str:
        return "".join(self.written)


async def drag(pilot, selector, delta) -> None:
    """Press at the widget's origin, move by delta, release at the end position.

    Positions are pinned in screen coordinates up front: pilot's mouse_up posts a
    leading MouseMove at its own target, so releasing anywhere else would count
    as more dragging.
    """
    widget = pilot.app.query_one(selector)
    end = widget.region.offset + delta
    await pilot.mouse_down(selector)
    await pilot.hover(None, offset=(end.x, end.y))
    await pilot.mouse_up(None, offset=(end.x, end.y))


async def wait_for(pilot, condition, timeout: float = 5.0) -> None:
    """Pause the pilot until condition() is true (child processes take a moment)."""
    for _ in range(int(timeout / 0.05)):
        if condition():
            return
        await pilot.pause(0.05)
    raise TimeoutError("condition never became true")
