"""
TerminalScrollView: High-performance terminal display widget with direct grid rendering.
"""

from __future__ import annotations

from textual.scroll_view import ScrollView
from textual.geometry import Size
from textual.strip import Strip
from rich.segment import Segment

from ..log import measure_performance


class TerminalScrollView(ScrollView):
    """High-performance terminal display using direct grid rendering."""

    def __init__(self, **kwargs) -> None:
        """Initialize the terminal scroll view."""
        super().__init__(**kwargs)
        self.can_focus = True

    def compose(self):
        """No child widgets - render directly."""
        return []

    def update_content(self) -> None:
        """Update the terminal display."""
        # Get terminal widget (parent)
        terminal = self.parent
        if hasattr(terminal, "height"):
            self.virtual_size = Size(terminal.width, terminal.height)
        self.refresh()

    @measure_performance("TerminalScrollView")
    def render_line(self, visual_y: int) -> Strip:
        """Render a single visual line using terminal's ANSI output."""
        # Account for scrolling
        actual_visual_y = visual_y + int(self.scroll_y)

        # Get terminal widget (parent)
        terminal = self.parent
        if not hasattr(terminal, "get_line_rich"):
            return Strip([Segment(" " * self.size.width)])

        # Check if line exists
        if actual_visual_y >= terminal.height:
            return Strip([Segment(" " * self.size.width)])

        # Get Rich Text line with all formatting, cursors, and padding
        text = terminal.get_line_rich(actual_visual_y, width=self.size.width)
        segments = list(text.render(self.app.console))

        return Strip(segments)
