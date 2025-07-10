"""
Terminal Buffer: Rich Text-based terminal content storage.

This module provides the Buffer class that manages terminal screen content
as a list of Rich Text objects with styling information.
"""

from __future__ import annotations

from typing import List, Optional

from rich.style import Style
from rich.text import Text, Span


class Buffer:
    """
    A buffer that stores terminal content as styled text lines.
    """

    def __init__(self, width: int, height: int) -> None:
        """Initialize buffer with given dimensions."""
        self.width = width
        self.height = height
        self.lines: List[Text] = [Text() for _ in range(height)]

    def get_content(self) -> List[Text]:
        """Get buffer content as a list of Rich Text objects."""
        return self.lines.copy()

    def set(self, x: int, y: int, text: str, style: Optional[Style] = None) -> None:
        """Set text at position, overwriting existing content."""
        if not (0 <= y < self.height):
            return

        line = self.lines[y]

        if x < len(line.plain):
            # Replace character in existing line
            new_line = line[:x] + Text(text, style) + line[x + len(text) :]
            self.lines[y] = new_line
        else:
            # Append to end of line
            if len(line.plain) == 0:
                # Starting fresh on empty line
                new_line = Text()
            else:
                new_line = line.copy()
            # Pad with spaces if needed
            if len(new_line.plain) < x:
                padding_length = x - len(new_line.plain)
                padding = Text(" " * padding_length, Style())
                # Add explicit span for padding only when extending existing content
                if not padding.spans and padding_length > 0 and len(line.plain) > 0:
                    padding.spans.append(Span(0, padding_length, Style()))
                new_line = new_line + padding
            new_line.append(text, style)
            self.lines[y] = new_line

    def insert(self, x: int, y: int, text: str, style: Optional[Style] = None) -> None:
        """Insert text at position, shifting existing content right."""
        if not (0 <= y < self.height):
            return

        line = self.lines[y]

        if x < len(line.plain):
            # Insert in middle of existing line
            inserted_text = Text(text, style)
            # Ensure explicit span for inserted text with default style
            if not inserted_text.spans and len(text) > 0 and (style is None or style == Style()):
                inserted_text.spans.append(Span(0, len(text), style or Style()))
            new_line = line[:x] + inserted_text + line[x:]
        else:
            # Append to end of line
            new_line = line.copy()
            # Pad with spaces if needed
            if len(new_line.plain) < x:
                padding_length = x - len(new_line.plain)
                padding = Text(" " * padding_length, Style())
                # Add explicit span for padding only when extending existing content
                if not padding.spans and padding_length > 0 and len(line.plain) > 0:
                    padding.spans.append(Span(0, padding_length, Style()))
                new_line = new_line + padding
            # For insert operations, ensure explicit spans for empty styles
            if style is None or style == Style():
                text_to_append = Text(text, style or Style())
                if not text_to_append.spans and len(text) > 0:
                    text_to_append.spans.append(Span(0, len(text), style or Style()))
                new_line = new_line + text_to_append
            else:
                new_line.append(text, style)

        # Truncate if line becomes too long
        if len(new_line.plain) > self.width:
            new_line = new_line[: self.width]

        self.lines[y] = new_line

    def delete(self, x: int, y: int, count: int = 1) -> None:
        """Delete characters at position."""
        if not (0 <= y < self.height):
            return

        line = self.lines[y]
        if x >= len(line.plain):
            return

        # Delete characters by reconstructing line
        end_pos = min(x + count, len(line.plain))
        new_line = line[:x] + line[end_pos:]
        self.lines[y] = new_line

    def clear_region(self, x1: int, y1: int, x2: int, y2: int, style: Optional[Style] = None) -> None:
        """Clear a rectangular region."""
        if style is None:
            style = Style()

        for y in range(max(0, y1), min(self.height, y2 + 1)):
            line = self.lines[y]

            if not line.plain or x1 >= len(line.plain):
                continue

            # Clear the specified range
            clear_start = max(0, x1)
            clear_end = min(len(line.plain), x2 + 1)

            if clear_end <= clear_start:
                continue

            # Build new line with cleared region
            cleared_text = Text(" " * (clear_end - clear_start), style)
            # Ensure the cleared region has an explicit span only for default/empty style
            if not cleared_text.spans and len(cleared_text.plain) > 0 and (style is None or style == Style()):
                cleared_text.spans.append(Span(0, len(cleared_text.plain), style or Style()))
            new_line = line[:clear_start] + cleared_text + line[clear_end:]
            self.lines[y] = new_line

    def clear_line(self, y: int, mode: int = 0, cursor_x: int = 0) -> None:
        """Clear line content."""
        if not (0 <= y < self.height):
            return

        line = self.lines[y]

        if mode == 0:  # Clear from cursor to end of line
            if cursor_x < len(line.plain):
                self.lines[y] = line[:cursor_x]
            # If cursor is at or beyond end, no need to clear
        elif mode == 1:  # Clear from beginning to cursor
            if cursor_x < len(line.plain):
                cleared_part = Text(" " * cursor_x)
                self.lines[y] = cleared_part + line[cursor_x:]
            else:
                # Clear entire line if cursor is beyond content
                self.lines[y] = Text()
        elif mode == 2:  # Clear entire line
            self.lines[y] = Text()

    def scroll_up(self, count: int) -> None:
        """Scroll content up, removing top lines and adding blank lines at bottom."""
        for _ in range(count):
            self.lines.pop(0)
            self.lines.append(Text())

    def scroll_down(self, count: int) -> None:
        """Scroll content down, removing bottom lines and adding blank lines at top."""
        for _ in range(count):
            self.lines.pop()
            self.lines.insert(0, Text())

    def resize(self, width: int, height: int) -> None:
        """Resize buffer to new dimensions."""
        # Adjust number of lines FIRST, before updating height
        if len(self.lines) < height:
            # Add new lines
            self.lines.extend([Text() for _ in range(height - len(self.lines))])
        elif len(self.lines) > height:
            # Remove excess lines
            self.lines = self.lines[:height]

        # Update dimensions AFTER lines are properly sized
        self.width = width
        self.height = height

        # Truncate lines that are too wide
        for i in range(len(self.lines)):
            if len(self.lines[i].plain) > width:
                self.lines[i] = self.lines[i][:width]
