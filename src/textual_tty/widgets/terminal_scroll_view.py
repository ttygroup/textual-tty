"""
TerminalScrollView: High-performance terminal display widget with direct grid rendering.
"""

from __future__ import annotations

from typing import List

from textual.scroll_view import ScrollView
from textual.geometry import Size
from textual.strip import Strip
from rich.segment import Segment

from ..log import measure_performance
from ..buffer import Cell


class TerminalScrollView(ScrollView):
    """High-performance terminal display using direct grid rendering."""

    def __init__(self, **kwargs) -> None:
        """Initialize the terminal scroll view."""
        super().__init__(**kwargs)
        self._content_grid: List[List[Cell]] = []
        self._cursor_position: tuple[int, int] = (0, 0)
        self._show_cursor: bool = True

        self.can_focus = True

    def compose(self):
        """No child widgets - render directly."""
        return []

    def update_content(self, grid: List[List[Cell]]) -> None:
        """Update the terminal content with new grid."""
        self._content_grid = grid

        # Calculate virtual size based on grid
        if grid:
            max_width = max(len(row) for row in grid) if grid else 80
            total_visual_lines = len(grid)
        else:
            max_width = 80
            total_visual_lines = 24

        self.virtual_size = Size(max_width, total_visual_lines)
        self.refresh()

    def set_cursor_position(self, x: int, y: int) -> None:
        """Set the cursor position."""
        self._cursor_position = (x, y)
        self.refresh()

    def set_cursor_visible(self, visible: bool) -> None:
        """Set cursor visibility."""
        self._show_cursor = visible
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
