"""
TerminalScrollView: High-performance terminal display widget with direct grid rendering.
"""

from __future__ import annotations

from typing import List

from textual.scroll_view import ScrollView
from textual.geometry import Size
from textual.strip import Strip
from rich.segment import Segment
from rich.text import Text

from ..log import measure_performance
from ..buffer import Cell
from ..color import get_cursor_code, reset_code


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
        """Render a single visual line directly from grid."""
        # Account for scrolling
        actual_visual_y = visual_y + int(self.scroll_y)

        if actual_visual_y >= len(self._content_grid):
            # Beyond content - return empty line
            return Strip([Segment(" " * self.size.width)])

        row = self._content_grid[actual_visual_y]

        # Build ANSI string from grid row
        parts = []
        cursor_x, cursor_y = self._cursor_position

        # Process each cell up to viewport width
        for x in range(min(len(row), self.size.width)):
            ansi_code, char = row[x]

            # Handle cursor position
            if self._show_cursor and x == cursor_x and actual_visual_y == cursor_y:
                # Add cursor style
                parts.append(ansi_code)
                parts.append(get_cursor_code())
                parts.append(char)
                parts.append(reset_code())
            else:
                # Normal cell
                parts.append(ansi_code)
                parts.append(char)

        # Pad to width if needed
        current_width = min(len(row), self.size.width)
        if current_width < self.size.width:
            # Reset all attributes for padding (including background)
            parts.append(reset_code())
            parts.append(" " * (self.size.width - current_width))

        # Always end with a reset to prevent bleeding to next line
        parts.append(reset_code())

        # Create Rich Text from ANSI string and convert to segments
        ansi_string = "".join(parts)
        text = Text.from_ansi(ansi_string)
        segments = list(text.render(self.app.console))

        return Strip(segments)
