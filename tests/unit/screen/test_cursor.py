from textual_tty.terminal import Terminal
from textual_tty.constants import DEFAULT_TERMINAL_WIDTH, DEFAULT_TERMINAL_HEIGHT


def test_set_cursor():
    screen = Terminal(width=DEFAULT_TERMINAL_WIDTH, height=DEFAULT_TERMINAL_HEIGHT)
    screen.set_cursor(10, 5)
    assert screen.cursor_x == 10
    assert screen.cursor_y == 5

    # Test out of bounds clamping
    screen.set_cursor(100, 30)
    assert screen.cursor_x == 79  # width - 1
    assert screen.cursor_y == 23  # height - 1

    screen.set_cursor(-5, -5)
    assert screen.cursor_x == 0
    assert screen.cursor_y == 0


def test_carriage_return():
    screen = Terminal(width=DEFAULT_TERMINAL_WIDTH, height=DEFAULT_TERMINAL_HEIGHT)
    screen.set_cursor(10, 5)
    screen.carriage_return()
    assert screen.cursor_x == 0
    assert screen.cursor_y == 5


def test_line_feed():
    screen = Terminal(width=DEFAULT_TERMINAL_WIDTH, height=DEFAULT_TERMINAL_HEIGHT)
    screen.set_cursor(10, 5)
    screen.line_feed()
    assert screen.cursor_x == 10
    assert screen.cursor_y == 6

    # Test line feed at bottom of screen (should scroll)
    screen.set_cursor(0, screen.height - 1)
    screen.line_feed()
    assert screen.cursor_y == screen.height - 1  # Cursor stays at bottom
    # (Scrolling content is tested in test_scroll.py)


def test_backspace():
    screen = Terminal(width=DEFAULT_TERMINAL_WIDTH, height=DEFAULT_TERMINAL_HEIGHT)
    screen.set_cursor(10, 5)
    screen.backspace()
    assert screen.cursor_x == 9
    assert screen.cursor_y == 5

    # Test backspace at beginning of line (should wrap)
    screen.set_cursor(0, 5)
    screen.backspace()
    assert screen.cursor_x == 79
    assert screen.cursor_y == 4

    # Test backspace at 0,0 (should stay at 0,0)
    screen.set_cursor(0, 0)
    screen.backspace()
    assert screen.cursor_x == 0
    assert screen.cursor_y == 0


def test_save_restore_cursor():
    screen = Terminal(width=DEFAULT_TERMINAL_WIDTH, height=DEFAULT_TERMINAL_HEIGHT)
    screen.cursor_x = 10
    screen.cursor_y = 5
    screen.save_cursor()

    screen.cursor_x = 20
    screen.cursor_y = 15

    screen.restore_cursor()
    assert screen.cursor_x == 10
    assert screen.cursor_y == 5


def test_backspace_wrap():
    screen = Terminal(width=DEFAULT_TERMINAL_WIDTH, height=DEFAULT_TERMINAL_HEIGHT)
    screen.cursor_x = 0
    screen.cursor_y = 5
    screen.backspace()
    assert screen.cursor_x == 79
    assert screen.cursor_y == 4
