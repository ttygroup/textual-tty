from textual_terminal.screen import TerminalScreen


def test_resize():
    screen = TerminalScreen(width=80, height=24)
    screen.cursor_x = 70
    screen.cursor_y = 20

    screen.resize(100, 30)
    assert screen.width == 100
    assert screen.height == 30
    assert screen.cursor_x == 70  # Cursor should remain if within bounds
    assert screen.cursor_y == 20
    assert screen.scroll_bottom == 29  # Should adjust to new height

    screen.resize(50, 10)
    assert screen.width == 50
    assert screen.height == 10
    assert screen.cursor_x == 49  # Cursor should clamp to new width
    assert screen.cursor_y == 9  # Cursor should clamp to new height
    assert screen.scroll_bottom == 9


def test_alternate_screen_switching():
    screen = TerminalScreen(width=80, height=24)
    assert not screen.in_alt_screen
    assert screen.current_console == screen.main_console

    screen.alternate_screen_on()
    assert screen.in_alt_screen
    assert screen.current_console == screen.alt_console

    # Calling again should do nothing
    screen.alternate_screen_on()
    assert screen.in_alt_screen
    assert screen.current_console == screen.alt_console

    screen.alternate_screen_off()
    assert not screen.in_alt_screen
    assert screen.current_console == screen.main_console

    # Calling again should do nothing
    screen.alternate_screen_off()
    assert not screen.in_alt_screen
    assert screen.current_console == screen.main_console


def test_alignment_test():
    screen = TerminalScreen(width=10, height=5)
    screen.alignment_test()

    expected_char = "E"
    for y in range(screen.height):
        line = screen.lines[y]
        assert len(line.plain) == screen.width
        assert all(char == expected_char for char in line.plain)
