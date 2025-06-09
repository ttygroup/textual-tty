"""Terminal grid data structure for screen content and scrollback."""

from __future__ import annotations

from collections import deque
from typing import Deque, List, Tuple
from rich.segment import Segment
from rich.style import Style


class Grid:
    """A data structure representing the grid of a terminal screen."""

    def __init__(self, width: int, height: int, history: int) -> None:
        """Initialize grid with dimensions and scrollback history size."""
        self.width: int = width
        self.height: int = height
        self.history_size: int = history

        # The visible lines on the screen.
        self.lines: List[List[Segment]] = [[] for _ in range(height)]

        # The scrollback buffer.
        self.history: Deque[List[Segment]] = deque(maxlen=history)

        # The number of lines the user has scrolled back into the history.
        self.scroll_offset: int = 0

    def resize(self, width: int, height: int) -> None:
        """Resize grid, moving lines to/from history as needed."""
        old_height = self.height
        self.width = width
        self.height = height

        if height < old_height:
            # Shrinking - move top lines to history
            lines_to_move = old_height - height
            for i in range(lines_to_move):
                if self.lines:
                    self.history.append(self.lines.pop(0))
        elif height > old_height:
            # Growing - pull lines from history if available
            lines_to_add = height - old_height
            pulled_lines = []

            # Pull from history in reverse order (most recent first)
            while lines_to_add > 0 and self.history:
                pulled_lines.insert(0, self.history.pop())
                lines_to_add -= 1

            # Add empty lines for the rest
            while lines_to_add > 0:
                pulled_lines.insert(0, [])
                lines_to_add -= 1

            # Prepend pulled lines to existing lines
            self.lines = pulled_lines + self.lines

        # Ensure we have exactly the right number of lines
        while len(self.lines) < height:
            self.lines.append([])
        while len(self.lines) > height:
            self.lines.pop()

    def clear(self, sx: int, sy: int, ex: int, ey: int, style: Style) -> None:
        """Clear rectangular region with given style."""
        for y in range(max(0, sy), min(self.height, ey + 1)):
            if sx == 0 and ex >= self.width - 1:
                # Clear entire line
                self.lines[y] = []
            else:
                # Clear partial line - more complex
                # For now, just clear character by character
                for x in range(max(0, sx), min(self.width, ex + 1)):
                    self.set_cell(x, y, " ", style)

    def clear_rect(self, sx: int, sy: int, ex: int, ey: int, style: Style) -> None:
        """Clear rectangular region with given style (alias for clear)."""

    def get_cell(self, x: int, y: int) -> Tuple[str, Style]:
        """Get character and style at (x, y)."""
        if y < 0 or y >= self.height:
            return " ", Style()

        line = self.lines[y]
        current_x = 0

        for segment in line:
            segment_len = Segment.get_line_length([segment])
            if current_x + segment_len > x:
                # Found the segment containing position x
                offset = x - current_x
                # Find the character at this offset
                char_pos = 0
                for ch in segment.text:
                    if char_pos == offset:
                        return ch, segment.style
                    char_pos += Segment.get_line_length([Segment(ch, segment.style)])
                return " ", segment.style
            current_x += segment_len

        # Position is beyond content
        return " ", Style()

    def set_cell(self, x: int, y: int, character: str, style: Style) -> None:
        """Set character and style at (x, y), handling segment splits/merges."""
        if y < 0 or y >= self.height:
            return

        line = self.lines[y]

        # Simple approach: rebuild the line character by character
        # First, extract all current characters with their styles
        chars_and_styles = []
        for segment in line:
            for ch in segment.text:
                chars_and_styles.append((ch, segment.style))

        # Extend with spaces if needed
        while len(chars_and_styles) <= x:
            chars_and_styles.append((" ", Style()))

        # Set the character at position x
        chars_and_styles[x] = (character, style)

        # Rebuild segments by grouping consecutive characters with same style
        new_segments = []
        if chars_and_styles:
            current_text = chars_and_styles[0][0]
            current_style = chars_and_styles[0][1]

            for ch, ch_style in chars_and_styles[1:]:
                if ch_style == current_style:
                    current_text += ch
                else:
                    new_segments.append(Segment(current_text, current_style))
                    current_text = ch
                    current_style = ch_style

            new_segments.append(Segment(current_text, current_style))

        self.lines[y] = new_segments

    def get_line_segments(self, y: int) -> List[Segment]:
        """Get segments for line y."""
        if 0 <= y < self.height:
            return self.lines[y]
        return []

    def scroll_up(self, style: Style) -> None:
        """Scroll up: top line to history, new blank line at bottom."""
        if self.height > 0:
            # Move top line to history
            self.history.append(self.lines[0])
            # Shift all lines up
            self.lines[:-1] = self.lines[1:]
            # Add blank line at bottom
            self.lines[-1] = []

    def compare(self, other: Grid) -> bool:
        """Check if this grid equals another."""
        if self.width != other.width or self.height != other.height:
            return False
        if self.history != other.history:
            return False
        if len(self.lines) != len(other.lines):
            return False
        for i in range(len(self.lines)):
            if self.lines[i] != other.lines[i]:
                return False
        return True

    def duplicate_lines(self, dest_grid: Grid, dest_y: int, src_y: int, count: int) -> None:
        """Copy lines between grids (for alternate screen buffer)."""
        for i in range(count):
            if src_y + i < self.height and dest_y + i < dest_grid.height:
                # Deep copy the segments
                dest_grid.lines[dest_y + i] = [Segment(s.text, s.style) for s in self.lines[src_y + i]]
