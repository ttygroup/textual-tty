from textual_tty.terminal import Terminal
from rich.text import Text
from rich.style import Style


def test_scroll_up():
    screen = Terminal(width=10, height=5)
    # Fill screen with content
    for i in range(screen.height):
        screen.current_buffer.lines[i] = Text(f"Line {i}", style=Style())

    # Set scroll region to cover entire screen initially
    screen.set_scroll_region(0, screen.height - 1)

    # Scroll up by 1
    screen.scroll_up(1)
    expected_lines = [
        Text("Line 1", style=Style()),
        Text("Line 2", style=Style()),
        Text("Line 3", style=Style()),
        Text("Line 4", style=Style()),
        Text("", style=Style()),  # New blank line at the bottom
    ]
    assert [line.plain for line in screen.get_content()] == [line.plain for line in expected_lines]

    # Scroll up by 2
    screen = Terminal(width=10, height=5)
    for i in range(screen.height):
        screen.current_buffer.lines[i] = Text(f"Line {i}", style=Style())
    screen.set_scroll_region(0, screen.height - 1)
    screen.scroll_up(2)
    expected_lines = [
        Text("Line 2", style=Style()),
        Text("Line 3", style=Style()),
        Text("Line 4", style=Style()),
        Text("", style=Style()),
        Text("", style=Style()),
    ]
    assert [line.plain for line in screen.get_content()] == [line.plain for line in expected_lines]


def test_scroll_down():
    screen = Terminal(width=10, height=5)
    # Fill screen with content
    for i in range(screen.height):
        screen.current_buffer.lines[i] = Text(f"Line {i}", style=Style())

    # Set scroll region to cover entire screen initially
    screen.set_scroll_region(0, screen.height - 1)

    # Scroll down by 1
    screen.scroll_down(1)
    expected_lines = [
        Text("", style=Style()),  # New blank line at the top
        Text("Line 0", style=Style()),
        Text("Line 1", style=Style()),
        Text("Line 2", style=Style()),
        Text("Line 3", style=Style()),
    ]
    assert [line.plain for line in screen.get_content()] == [line.plain for line in expected_lines]

    # Scroll down by 2
    screen = Terminal(width=10, height=5)
    for i in range(screen.height):
        screen.current_buffer.lines[i] = Text(f"Line {i}", style=Style())
    screen.set_scroll_region(0, screen.height - 1)
    screen.scroll_down(2)
    expected_lines = [
        Text("", style=Style()),
        Text("", style=Style()),
        Text("Line 0", style=Style()),
        Text("Line 1", style=Style()),
        Text("Line 2", style=Style()),
    ]
    assert [line.plain for line in screen.get_content()] == [line.plain for line in expected_lines]


def test_set_scroll_region():
    screen = Terminal(width=10, height=10)
    screen.set_scroll_region(2, 7)
    assert screen.scroll_top == 2
    assert screen.scroll_bottom == 7

    # Test clamping
    screen.set_scroll_region(-1, 12)
    assert screen.scroll_top == 0
    assert screen.scroll_bottom == 9  # height - 1

    screen.set_scroll_region(5, 3)  # top > bottom
    assert screen.scroll_top == 5
    assert screen.scroll_bottom == 5  # clamped to top


def test_line_feed_with_scrolling():
    screen = Terminal(width=10, height=5)
    # Fill screen up to the last line
    for i in range(screen.height - 1):
        screen.current_buffer.lines[i] = Text(f"Line {i}", style=Style())
    screen.cursor_y = screen.height - 1  # Cursor on the last line

    # Set scroll region to cover entire screen
    screen.set_scroll_region(0, screen.height - 1)

    # Perform line feed, should scroll up
    screen.line_feed()

    expected_lines = [
        Text("Line 1", style=Style()),
        Text("Line 2", style=Style()),
        Text("Line 3", style=Style()),
        Text("", style=Style()),  # Line 0 scrolled off, new blank line at bottom
        Text("", style=Style()),  # Original last line is now blank
    ]
    assert [line.plain for line in screen.get_content()] == [line.plain for line in expected_lines]
    assert screen.cursor_y == screen.height - 1  # Cursor should remain on the last line
