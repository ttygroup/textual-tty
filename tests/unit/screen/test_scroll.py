from textual_tty.terminal import Terminal


def test_scroll_up():
    screen = Terminal(width=10, height=5)
    # Fill screen with content
    for i in range(screen.height):
        screen.current_buffer.set(0, i, f"Line {i}")

    # Set scroll region to cover entire screen initially
    screen.set_scroll_region(0, screen.height - 1)

    # Scroll up by 1
    screen.scroll_up(1)
    expected_lines = [
        "Line 1    ",
        "Line 2    ",
        "Line 3    ",
        "Line 4    ",
        "          ",
    ]
    assert [screen.current_buffer.get_line_text(i) for i in range(screen.height)] == expected_lines

    # Scroll up by 2
    screen = Terminal(width=10, height=5)
    for i in range(screen.height):
        screen.current_buffer.set(0, i, f"Line {i}")
    screen.set_scroll_region(0, screen.height - 1)
    screen.scroll_up(2)
    expected_lines = [
        "Line 2    ",
        "Line 3    ",
        "Line 4    ",
        "          ",
        "          ",
    ]
    assert [screen.current_buffer.get_line_text(i) for i in range(screen.height)] == expected_lines


def test_scroll_down():
    screen = Terminal(width=10, height=5)
    # Fill screen with content
    for i in range(screen.height):
        screen.current_buffer.set(0, i, f"Line {i}")

    # Set scroll region to cover entire screen initially
    screen.set_scroll_region(0, screen.height - 1)

    # Scroll down by 1
    screen.scroll_down(1)
    expected_lines = [
        "          ",
        "Line 0    ",
        "Line 1    ",
        "Line 2    ",
        "Line 3    ",
    ]
    assert [screen.current_buffer.get_line_text(i) for i in range(screen.height)] == expected_lines

    # Scroll down by 2
    screen = Terminal(width=10, height=5)
    for i in range(screen.height):
        screen.current_buffer.set(0, i, f"Line {i}")
    screen.set_scroll_region(0, screen.height - 1)
    screen.scroll_down(2)
    expected_lines = [
        "          ",
        "          ",
        "Line 0    ",
        "Line 1    ",
        "Line 2    ",
    ]
    assert [screen.current_buffer.get_line_text(i) for i in range(screen.height)] == expected_lines


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
        screen.current_buffer.set(0, i, f"Line {i}")
    screen.cursor_y = screen.height - 1  # Cursor on the last line

    # Set scroll region to cover entire screen
    screen.set_scroll_region(0, screen.height - 1)

    # Perform line feed, should scroll up
    screen.line_feed()

    expected_lines = [
        "Line 1    ",
        "Line 2    ",
        "Line 3    ",
        "          ",
        "          ",
    ]
    assert [screen.current_buffer.get_line_text(i) for i in range(screen.height)] == expected_lines
    assert screen.cursor_y == screen.height - 1  # Cursor should remain on the last line
