"""
TerminalScrollView: High-performance terminal display widget with direct grid rendering.
"""

from __future__ import annotations

from typing import List

from textual.scroll_view import ScrollView
from textual.geometry import Size
from textual.strip import Strip
from rich.segment import Segment
from rich.style import Style

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

        # Convert grid row to ANSI string and then to segments
        line_string = self._grid_row_to_ansi_string(row, actual_visual_y)

        # Parse the ANSI string back to segments for Textual
        segments = self._parse_ansi_to_segments(line_string)

        # Ensure we fill the full width
        segments = self._fill_to_width(segments, self.size.width)

        return Strip(segments)

    def _grid_row_to_ansi_string(self, row: List[Cell], y: int) -> str:
        """Convert a grid row to an ANSI-formatted string."""
        if not row:
            return " " * self.size.width

        result = []
        current_ansi = None

        # Determine which cells to process (up to viewport width)
        cells_to_process = min(len(row), self.size.width)

        for x in range(cells_to_process):
            ansi_code, char = row[x]

            # Add cursor if at this position
            cursor_x, cursor_y = self._cursor_position
            if self._show_cursor and x == cursor_x and y == cursor_y:
                # Apply cursor style (reverse video)
                if ansi_code:
                    result.append(ansi_code)
                result.append(get_cursor_code())
                result.append(char)
                result.append(reset_code())
                current_ansi = None  # Reset state after cursor
            else:
                # Normal character
                if ansi_code != current_ansi:
                    if ansi_code:
                        result.append(ansi_code)
                    elif current_ansi:
                        # Reset if we had an ANSI code but now don't
                        result.append(reset_code())
                    current_ansi = ansi_code
                result.append(char)

        # Pad to width if needed
        remaining = self.size.width - cells_to_process
        if remaining > 0:
            if current_ansi:
                result.append(reset_code())
            result.append(" " * remaining)

        return "".join(result)

    def _parse_ansi_to_segments(self, ansi_string: str) -> List[Segment]:
        """Parse ANSI string back to Rich segments."""
        segments = []
        i = 0
        current_style = Style()
        text_buffer = []

        while i < len(ansi_string):
            if ansi_string[i] == "\033" and i + 1 < len(ansi_string) and ansi_string[i + 1] == "[":
                # Found ANSI escape sequence
                if text_buffer:
                    # Flush any accumulated text
                    segments.append(Segment("".join(text_buffer), current_style))
                    text_buffer = []

                # Find end of sequence
                j = i + 2
                while j < len(ansi_string) and ansi_string[j] not in "mHABCDfHlh":
                    j += 1

                if j < len(ansi_string):
                    # Parse the sequence and update style
                    sequence = ansi_string[i : j + 1]
                    current_style = self._parse_ansi_sequence(sequence, current_style)
                    i = j + 1
                else:
                    # Malformed sequence, skip
                    i += 1
            else:
                # Regular character
                text_buffer.append(ansi_string[i])
                i += 1

        # Flush any remaining text
        if text_buffer:
            segments.append(Segment("".join(text_buffer), current_style))

        return segments

    def _parse_ansi_sequence(self, sequence: str, current_style: Style) -> Style:
        """Parse ANSI sequence and return updated style."""
        if sequence.endswith("m"):
            # SGR sequence
            if sequence == "\033[0m":
                return Style()  # Reset
            elif sequence == "\033[7m":
                return current_style + Style(reverse=True)
            # For other sequences, we could parse them fully,
            # but for now just return current style
        return current_style

    def _fill_to_width(self, segments: List[Segment], width: int) -> List[Segment]:
        """Fill segments to specified width."""
        if width <= 0:
            return segments

        # Calculate current width
        current_width = sum(len(segment.text) for segment in segments)

        if current_width >= width:
            return segments

        # Add padding
        padding_length = width - current_width
        return segments + [Segment(" " * padding_length)]
