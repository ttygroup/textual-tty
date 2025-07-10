"""Tests for scroll region functionality."""

from textual_tty.terminal import Terminal
from rich.text import Text
from rich.style import Style


def test_scroll_up_within_region():
    """Test scrolling up within a constrained scroll region."""
    screen = Terminal(width=10, height=10)

    # Fill screen with numbered lines
    for i in range(10):
        screen.current_buffer.lines[i] = Text(f"Line {i}", style=Style())

    # Set scroll region to middle of screen (rows 3-7, 0-based)
    screen.set_scroll_region(3, 7)

    # Scroll up by 1 within the region
    screen.scroll_up(1)

    # Lines 0-2 should be unchanged
    assert screen.current_buffer.lines[0].plain == "Line 0"
    assert screen.current_buffer.lines[1].plain == "Line 1"
    assert screen.current_buffer.lines[2].plain == "Line 2"

    # Lines 3-7 should have scrolled up
    assert screen.current_buffer.lines[3].plain == "Line 4"
    assert screen.current_buffer.lines[4].plain == "Line 5"
    assert screen.current_buffer.lines[5].plain == "Line 6"
    assert screen.current_buffer.lines[6].plain == "Line 7"
    assert screen.current_buffer.lines[7].plain == ""  # New blank line

    # Lines 8-9 should be unchanged
    assert screen.current_buffer.lines[8].plain == "Line 8"
    assert screen.current_buffer.lines[9].plain == "Line 9"


def test_scroll_down_within_region():
    """Test scrolling down within a constrained scroll region."""
    screen = Terminal(width=10, height=10)

    # Fill screen with numbered lines
    for i in range(10):
        screen.current_buffer.lines[i] = Text(f"Line {i}", style=Style())

    # Set scroll region to middle of screen (rows 3-7, 0-based)
    screen.set_scroll_region(3, 7)

    # Scroll down by 1 within the region
    screen.scroll_down(1)

    # Lines 0-2 should be unchanged
    assert screen.current_buffer.lines[0].plain == "Line 0"
    assert screen.current_buffer.lines[1].plain == "Line 1"
    assert screen.current_buffer.lines[2].plain == "Line 2"

    # Lines 3-7 should have scrolled down
    assert screen.current_buffer.lines[3].plain == ""  # New blank line
    assert screen.current_buffer.lines[4].plain == "Line 3"
    assert screen.current_buffer.lines[5].plain == "Line 4"
    assert screen.current_buffer.lines[6].plain == "Line 5"
    assert screen.current_buffer.lines[7].plain == "Line 6"

    # Lines 8-9 should be unchanged
    assert screen.current_buffer.lines[8].plain == "Line 8"
    assert screen.current_buffer.lines[9].plain == "Line 9"


def test_line_feed_at_bottom_of_scroll_region():
    """Test line feed when cursor is at bottom of scroll region."""
    screen = Terminal(width=10, height=10)

    # Fill screen with numbered lines
    for i in range(10):
        screen.current_buffer.lines[i] = Text(f"Line {i}", style=Style())

    # Set scroll region to rows 2-5 (0-based)
    screen.set_scroll_region(2, 5)

    # Place cursor at bottom of scroll region
    screen.cursor_y = 5

    # Line feed should trigger scroll within region
    screen.line_feed()

    # Lines outside region should be unchanged
    assert screen.current_buffer.lines[0].plain == "Line 0"
    assert screen.current_buffer.lines[1].plain == "Line 1"
    assert screen.current_buffer.lines[6].plain == "Line 6"
    assert screen.current_buffer.lines[7].plain == "Line 7"
    assert screen.current_buffer.lines[8].plain == "Line 8"
    assert screen.current_buffer.lines[9].plain == "Line 9"

    # Lines within region should have scrolled up
    assert screen.current_buffer.lines[2].plain == "Line 3"
    assert screen.current_buffer.lines[3].plain == "Line 4"
    assert screen.current_buffer.lines[4].plain == "Line 5"
    assert screen.current_buffer.lines[5].plain == ""  # New blank line


def test_multiple_scroll_regions():
    """Test changing scroll regions and scrolling."""
    screen = Terminal(width=10, height=10)

    # Fill screen with numbered lines
    for i in range(10):
        screen.current_buffer.lines[i] = Text(f"Line {i}", style=Style())

    # Set first scroll region (top half)
    screen.set_scroll_region(0, 4)
    screen.scroll_up(1)

    # Top half should be scrolled
    assert screen.current_buffer.lines[0].plain == "Line 1"
    assert screen.current_buffer.lines[4].plain == ""

    # Bottom half should be unchanged
    assert screen.current_buffer.lines[5].plain == "Line 5"
    assert screen.current_buffer.lines[9].plain == "Line 9"

    # Change scroll region to bottom half
    screen.set_scroll_region(5, 9)
    screen.scroll_up(1)

    # Top half should remain as it was
    assert screen.current_buffer.lines[0].plain == "Line 1"
    assert screen.current_buffer.lines[4].plain == ""

    # Bottom half should now be scrolled
    assert screen.current_buffer.lines[5].plain == "Line 6"
    assert screen.current_buffer.lines[9].plain == ""


def test_reset_scroll_region():
    """Test resetting scroll region with CSI r."""
    screen = Terminal(width=10, height=10)

    # Set a custom scroll region
    screen.set_scroll_region(3, 6)
    assert screen.scroll_top == 3
    assert screen.scroll_bottom == 6

    # Reset should restore full screen
    screen.set_scroll_region(0, 9)  # This is what CSI r with no params should do
    assert screen.scroll_top == 0
    assert screen.scroll_bottom == 9
