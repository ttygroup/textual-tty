"""
TerminalScrollView: High-performance terminal display widget.
"""

from __future__ import annotations

from typing import List, Dict, Tuple

from textual.scroll_view import ScrollView
from textual.geometry import Size
from textual.strip import Strip
from rich.text import Text
from rich.segment import Segment
from rich.style import Style

from ..log import measure_performance


class TerminalScrollView(ScrollView):
    """High-performance terminal display using direct strip rendering."""

    def __init__(self, **kwargs) -> None:
        """Initialize the terminal scroll view."""
        super().__init__(**kwargs)
        self._content_lines: List[Text] = []
        self._cursor_position: tuple[int, int] = (0, 0)
        self._show_cursor: bool = True

        # Simple cache: (line_index, content_hash) -> List[Segment]
        self._segment_cache: Dict[Tuple[int, int], List[Segment]] = {}

        self.can_focus = True

    def compose(self):
        """No child widgets - render directly."""
        return []

    def update_content(self, lines: List[Text]) -> None:
        """Update the terminal content with new lines."""
        self._content_lines = lines

        # Clear cache when content changes
        self._segment_cache.clear()

        # Calculate virtual size naively - sum all wrapped lines
        total_visual_lines = 0
        max_width = 80  # Default

        if lines and self.size.width > 0:
            for line in lines:
                line_width = len(line.plain)
                visual_lines = max(1, (line_width + self.size.width - 1) // self.size.width)
                total_visual_lines += visual_lines
                max_width = max(max_width, line_width)

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

    def _find_logical_line_for_visual_y(self, visual_y: int) -> Tuple[int, int]:
        """
        Find which logical line contains visual_y and the offset within that line.
        Returns (logical_line_index, visual_line_offset_within_logical_line)
        """
        if not self._content_lines or self.size.width <= 0:
            return (0, 0)

        current_visual = 0

        for logical_idx, line in enumerate(self._content_lines):
            line_width = len(line.plain)
            visual_lines_for_this_logical = max(1, (line_width + self.size.width - 1) // self.size.width)

            if current_visual + visual_lines_for_this_logical > visual_y:
                # Found it! visual_y is within this logical line
                offset_within_logical = visual_y - current_visual
                return (logical_idx, offset_within_logical)

            current_visual += visual_lines_for_this_logical

        # Beyond all lines
        return (len(self._content_lines), 0)

    @measure_performance("TerminalScrollView")
    def render_line(self, visual_y: int) -> Strip:
        """Render a single visual line."""
        # Account for scrolling
        actual_visual_y = visual_y + int(self.scroll_y)

        logical_idx, visual_offset = self._find_logical_line_for_visual_y(actual_visual_y)

        if logical_idx >= len(self._content_lines):
            # Beyond content
            return Strip([Segment(" " * self.size.width)])

        line = self._content_lines[logical_idx]

        # Simple cache key
        content_hash = hash(tuple(line.render(self.app.console)))
        cache_key = (logical_idx, content_hash)

        if cache_key not in self._segment_cache:
            # Render the logical line to segments
            segments = list(line.render(self.app.console))
            self._segment_cache[cache_key] = segments
        else:
            segments = self._segment_cache[cache_key]

        # Handle wrapping - extract the visual line we want
        if self.size.width <= 0:
            return Strip([])

        # Split segments based on width and visual_offset
        wrapped_segments = self._wrap_segments_to_lines(segments, self.size.width)

        if visual_offset < len(wrapped_segments):
            line_segments = wrapped_segments[visual_offset]
        else:
            line_segments = []

        # Fill to end of line using preserved background style
        line_segments = self._fill_line_to_width(line_segments, self.size.width)

        # Add cursor if appropriate (after filling)
        cursor_y = self._cursor_position[1]
        if self._show_cursor and logical_idx == cursor_y:
            cursor_x = self._cursor_position[0]
            # Only show cursor on the visual line that contains cursor_x
            char_start = visual_offset * self.size.width
            char_end = char_start + self.size.width
            if char_start <= cursor_x < char_end:
                line_segments = self._add_cursor_to_segments(line_segments, cursor_x - char_start)

        return Strip(line_segments)

    def _wrap_segments_to_lines(self, segments: List[Segment], width: int) -> List[List[Segment]]:
        """Split segments into visual lines based on width."""
        if width <= 0:
            return [[]]

        wrapped_lines = []
        current_line = []
        current_width = 0

        for segment in segments:
            text = segment.text
            style = segment.style

            while text:
                remaining_width = width - current_width

                if len(text) <= remaining_width:
                    # Fits on current line
                    current_line.append(Segment(text, style))
                    current_width += len(text)
                    text = ""
                else:
                    # Need to split
                    part = text[:remaining_width]
                    text = text[remaining_width:]

                    current_line.append(Segment(part, style))
                    wrapped_lines.append(current_line)

                    current_line = []
                    current_width = 0

        if current_line or not wrapped_lines:
            wrapped_lines.append(current_line)

        return wrapped_lines

    def _add_cursor_to_segments(self, segments: List[Segment], cursor_x: int) -> List[Segment]:
        """Add cursor styling at position cursor_x within the segments."""
        from rich.style import Style

        if not segments and cursor_x == 0:
            # Empty line, cursor at start
            return [Segment(" ", Style(reverse=True))]

        result = []
        current_x = 0

        for segment in segments:
            text = segment.text
            style = segment.style

            if current_x + len(text) <= cursor_x:
                # Cursor is after this segment
                result.append(segment)
                current_x += len(text)
            elif current_x <= cursor_x < current_x + len(text):
                # Cursor is within this segment
                offset = cursor_x - current_x

                before = text[:offset]
                cursor_char = text[offset] if offset < len(text) else " "
                after = text[offset + 1 :]

                if before:
                    result.append(Segment(before, style))
                result.append(Segment(cursor_char, Style(reverse=True)))
                if after:
                    result.append(Segment(after, style))
                current_x += len(text)
            else:
                # Cursor is before this segment
                result.append(segment)
                current_x += len(text)

        # If cursor is beyond all segments, add it
        if cursor_x >= current_x:
            padding = cursor_x - current_x
            if padding > 0:
                result.append(Segment(" " * padding))
            result.append(Segment(" ", Style(reverse=True)))

        return result

    def _fill_line_to_width(self, segments: List[Segment], width: int) -> List[Segment]:
        """Fill line to terminal width using preserved background from zero-length segments."""
        if width <= 0:
            return segments

        # Calculate current width (excluding zero-length segments)
        current_width = sum(len(segment.text) for segment in segments)

        if current_width >= width:
            return segments

        # Look for zero-width space markers that carry preserved background style
        padding_style = Style()
        for segment in reversed(segments):
            if segment.text == "\u200b" and segment.style and segment.style.bgcolor:
                # Found preserved background style marker
                padding_style = Style(bgcolor=segment.style.bgcolor)
                break

        # Add padding to reach full width
        padding_length = width - current_width
        return segments + [Segment(" " * padding_length, padding_style)]
