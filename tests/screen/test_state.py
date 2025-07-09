from textual_tty.terminal import Terminal
from rich.text import Text


def test_resize():
    screen = Terminal(width=80, height=24)
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
    screen = Terminal(width=80, height=24)
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
    screen = Terminal(width=10, height=5)
    screen.alignment_test()

    expected_char = "E"
    for y in range(screen.height):
        line = screen.current_buffer.lines[y]
        assert len(line.plain) == screen.width
        assert all(char == expected_char for char in line.plain)


def test_alternate_screen_on_off_restores_lines():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.lines[0] = Text("Hello")
    screen.alternate_screen_on()
    assert screen.current_buffer.lines[0].plain == ""
    screen.alternate_screen_off()
    assert screen.current_buffer.lines[0].plain == "Hello"


def test_set_and_clear_modes():
    screen = Terminal(width=80, height=24)

    # Test setting a private mode
    screen.set_mode(7, private=True)
    assert screen.auto_wrap

    # Test clearing a private mode
    screen.clear_mode(7, private=True)
    assert not screen.auto_wrap

    # Test setting a non-private mode
    screen.set_mode(4, private=False)
    assert screen.insert_mode

    # Test clearing a non-private mode
    screen.clear_mode(4, private=False)
    assert not screen.insert_mode

    # Test an unknown mode
    screen.set_mode(999, private=True)
    # No attribute should be set
    assert not hasattr(screen, "unknown_mode")
