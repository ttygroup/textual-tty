from rich.style import Style
from rich.text import Text

from textual_terminal.screen import TerminalScreen


def test_clear_rect():
    screen = TerminalScreen(width=10, height=5)
    screen.lines = [
        Text("0123456789"),
        Text("0123456789"),
        Text("0123456789"),
        Text("0123456789"),
        Text("0123456789"),
    ]
    screen.clear_rect(2, 1, 5, 3)
    assert screen.lines[0].plain == "0123456789"
    assert screen.lines[1].plain == "01    6789"
    assert screen.lines[2].plain == "01    6789"
    assert screen.lines[3].plain == "01    6789"
    assert screen.lines[4].plain == "0123456789"


def test_write_cell_no_auto_wrap():
    screen = TerminalScreen(width=5, height=5)
    screen.auto_wrap = False
    screen.cursor_x = 4
    screen.cursor_y = 0
    screen.write_cell("a")
    assert screen.cursor_x == 4
    screen.write_cell("b")
    assert screen.cursor_x == 4
    assert screen.lines[0].plain == "    b"


def test_delete_characters_at_end_of_line():
    screen = TerminalScreen(width=10, height=5)
    screen.lines[0] = Text("12345")
    screen.cursor_x = 5
    screen.cursor_y = 0
    screen.delete_characters(1)
    assert screen.lines[0].plain == "12345"


def test_insert_characters_at_end_of_line():
    screen = TerminalScreen(width=10, height=5)
    screen.lines[0] = Text("12345")
    screen.cursor_x = 5
    screen.cursor_y = 0
    screen.insert_characters(2)
    assert screen.lines[0].plain == "12345  "


def test_clear_line_invalid_cursor():
    screen = TerminalScreen(width=10, height=5)
    screen.cursor_y = 10  # Invalid cursor position
    screen.clear_line(0)
    # Should not raise an error and do nothing


def test_clear_screen_invalid_cursor():
    screen = TerminalScreen(width=10, height=5)
    screen.cursor_y = 10  # Invalid cursor position
    screen.clear_screen(0)
    # Should not raise an error but still clear the screen below
    assert all(line.plain == "" for line in screen.lines)


def test_write_cell_invalid_cursor():
    screen = TerminalScreen(width=10, height=5)
    screen.cursor_y = 10  # Invalid cursor position
    screen.write_cell("a")
    # Should not raise an error and do nothing


def test_insert_characters_invalid_cursor():
    screen = TerminalScreen(width=10, height=5)
    screen.cursor_y = 10  # Invalid cursor position
    screen.insert_characters(1)
    # Should not raise an error and do nothing


def test_delete_characters_invalid_cursor():
    screen = TerminalScreen(width=10, height=5)
    screen.cursor_y = 10  # Invalid cursor position
    screen.delete_characters(1)
    # Should not raise an error and do nothing


def test_write_cell_overwrite_with_style():
    screen = TerminalScreen(width=10, height=5)
    screen.lines[0] = Text("12345")
    screen.cursor_x = 2
    screen.cursor_y = 0
    style = Style(color="red")
    screen.write_cell("X", style)
    assert screen.lines[0].plain == "12X45"


def test_write_cell_insert_with_style():
    screen = TerminalScreen(width=10, height=5)
    screen.insert_mode = True
    screen.lines[0] = Text("12345")
    screen.cursor_x = 2
    screen.cursor_y = 0
    style = Style(color="red")
    screen.write_cell("X", style)
    assert screen.lines[0].plain == "12X345"


def test_write_cell_insert_at_end_of_line():
    screen = TerminalScreen(width=10, height=5)
    screen.insert_mode = True
    screen.lines[0] = Text("123")
    screen.cursor_x = 5
    screen.cursor_y = 0
    screen.write_cell("X")
    assert screen.lines[0].plain == "123  X"
