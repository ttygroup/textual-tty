from textual_terminal.screen import TerminalScreen
from rich.text import Text


def test_write_cell_overwrite():
    screen = TerminalScreen(width=10, height=1)
    screen.write_cell("A")
    assert screen.lines[0].plain == "A"
    assert screen.cursor_x == 1

    screen.write_cell("B")
    assert screen.lines[0].plain == "AB"
    assert screen.cursor_x == 2

    screen.set_cursor(0, 0)
    screen.write_cell("C")
    assert screen.lines[0].plain == "CB"
    assert screen.cursor_x == 1


def test_write_cell_insert_mode():
    screen = TerminalScreen(width=10, height=1)
    screen.write_cell("A")
    screen.write_cell("B")
    screen.set_cursor(0, 0)
    screen.insert_mode = True
    screen.write_cell("C")
    assert screen.lines[0].plain == "CAB"
    assert screen.cursor_x == 1


def test_write_cell_autowrap():
    screen = TerminalScreen(width=3, height=2)
    screen.write_cell("A")
    screen.write_cell("B")
    screen.write_cell("C")
    assert screen.lines[0].plain == "ABC"
    assert screen.cursor_x == 3  # Cursor is at the end of the line
    assert screen.cursor_y == 0

    screen.write_cell("D")  # Should wrap
    assert screen.lines[0].plain == "ABC"
    assert screen.lines[1].plain == "D"
    assert screen.cursor_x == 1
    assert screen.cursor_y == 1


def test_clear_rect():
    screen = TerminalScreen(width=5, height=5)
    for y in range(5):
        screen.lines[y] = Text("ABCDE")

    screen.clear_rect(1, 1, 3, 3)  # Clear a 3x3 rectangle in the middle

    expected_lines = [
        Text("ABCDE"),
        Text("A   E"),
        Text("A   E"),
        Text("A   E"),
        Text("ABCDE"),
    ]
    for i in range(5):
        assert screen.lines[i].plain == expected_lines[i].plain


def test_clear_screen():
    screen = TerminalScreen(width=10, height=5)
    for y in range(5):
        screen.lines[y] = Text(f"Line {y}")
    screen.set_cursor(5, 2)  # Cursor at Line 2, char 5

    # Mode 0: Clear from cursor to end of screen
    screen.clear_screen(0)
    assert screen.lines[0].plain == "Line 0"
    assert screen.lines[1].plain == "Line 1"
    assert screen.lines[2].plain == "Line "  # Line 2 cleared from cursor
    assert screen.lines[3].plain == ""
    assert screen.lines[4].plain == ""

    # Reset screen
    for y in range(5):
        screen.lines[y] = Text(f"Line {y}")
    screen.set_cursor(5, 2)

    # Mode 1: Clear from beginning of screen to cursor
    screen.clear_screen(1)
    assert screen.lines[0].plain == ""
    assert screen.lines[1].plain == ""
    assert screen.lines[2].plain == "     2"  # Line 2 cleared to cursor
    assert screen.lines[3].plain == "Line 3"
    assert screen.lines[4].plain == "Line 4"

    # Reset screen
    for y in range(5):
        screen.lines[y] = Text(f"Line {y}")
    screen.set_cursor(5, 2)

    # Mode 2: Clear entire screen
    screen.clear_screen(2)
    for y in range(5):
        assert screen.lines[y].plain == ""


def test_clear_line():
    screen = TerminalScreen(width=10, height=1)
    screen.lines[0] = Text("ABCDEFGHIJ")
    screen.set_cursor(5, 0)

    # Mode 0: Clear from cursor to end of line
    screen.clear_line(0)
    assert screen.lines[0].plain == "ABCDE"

    # Reset
    screen.lines[0] = Text("ABCDEFGHIJ")
    screen.set_cursor(5, 0)

    # Mode 1: Clear from beginning of line to cursor
    screen.clear_line(1)
    assert screen.lines[0].plain == "     FGHIJ"

    # Reset
    screen.lines[0] = Text("ABCDEFGHIJ")
    screen.set_cursor(5, 0)

    # Mode 2: Clear entire line
    screen.clear_line(2)
    assert screen.lines[0].plain == ""


def test_insert_lines():
    screen = TerminalScreen(width=10, height=5)
    for y in range(5):
        screen.lines[y] = Text(f"Line {y}")
    screen.set_cursor(0, 2)  # Insert at line 2

    screen.insert_lines(1)
    expected_lines = [
        Text("Line 0"),
        Text("Line 1"),
        Text(""),  # Inserted blank line
        Text("Line 2"),
        Text("Line 3"),
    ]
    for i in range(5):
        assert screen.lines[i].plain == expected_lines[i].plain

    # Insert multiple lines
    screen = TerminalScreen(width=10, height=5)
    for y in range(5):
        screen.lines[y] = Text(f"Line {y}")
    screen.set_cursor(0, 1)
    screen.insert_lines(2)
    expected_lines = [
        Text("Line 0"),
        Text(""),
        Text(""),
        Text("Line 1"),
        Text("Line 2"),
    ]
    for i in range(5):
        assert screen.lines[i].plain == expected_lines[i].plain


def test_delete_lines():
    screen = TerminalScreen(width=10, height=5)
    for y in range(5):
        screen.lines[y] = Text(f"Line {y}")
    screen.set_cursor(0, 1)  # Delete from line 1

    screen.delete_lines(1)
    expected_lines = [
        Text("Line 0"),
        Text("Line 2"),
        Text("Line 3"),
        Text("Line 4"),
        Text(""),  # New blank line at bottom
    ]
    for i in range(5):
        assert screen.lines[i].plain == expected_lines[i].plain

    # Delete multiple lines
    screen = TerminalScreen(width=10, height=5)
    for y in range(5):
        screen.lines[y] = Text(f"Line {y}")
    screen.set_cursor(0, 0)
    screen.delete_lines(2)
    expected_lines = [
        Text("Line 2"),
        Text("Line 3"),
        Text("Line 4"),
        Text(""),
        Text(""),
    ]
    for i in range(5):
        assert screen.lines[i].plain == expected_lines[i].plain


def test_insert_characters():
    screen = TerminalScreen(width=10, height=1)
    screen.lines[0] = Text("ABCDEFGHIJ")
    screen.set_cursor(2, 0)  # Insert at C

    screen.insert_characters(3)
    assert screen.lines[0].plain == "AB   CDEFG"


def test_delete_characters():
    screen = TerminalScreen(width=10, height=1)
    screen.lines[0] = Text("ABCDEFGHIJ")
    screen.set_cursor(2, 0)  # Delete from C

    screen.delete_characters(3)
    assert screen.lines[0].plain == "ABFGHIJ"
