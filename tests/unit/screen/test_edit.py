from textual_tty.terminal import Terminal
from textual_tty import constants
from textual_tty.parser import Parser


def test_write_cell_overwrite():
    screen = Terminal(width=10, height=1)
    parser = Parser(screen)
    parser = Parser(screen)
    parser.feed("\x1b[31m")  # Set red color
    parser.feed("A")
    assert screen.current_buffer.get_line_text(0) == "A         "
    assert screen.current_buffer.get_cell(0, 0) == ("\x1b[31m", "A")
    assert screen.cursor_x == 1

    parser.feed("\x1b[32m")  # Set green color
    parser.feed("B")
    assert screen.current_buffer.get_line_text(0) == "AB        "
    assert screen.current_buffer.get_cell(1, 0) == ("\x1b[32m", "B")
    assert screen.cursor_x == 2

    screen.set_cursor(0, 0)
    parser.feed("\x1b[34m")  # Set blue color
    parser.feed("C")
    assert screen.current_buffer.get_line_text(0) == "CB        "
    assert screen.current_buffer.get_cell(0, 0) == ("\x1b[34m", "C")
    assert screen.cursor_x == 1


def test_write_cell_insert_mode():
    screen = Terminal(width=10, height=1)
    parser = Parser(screen)
    parser = Parser(screen)
    parser.feed("\x1b[31m")  # Set red color
    parser.feed("A")
    parser.feed("\x1b[32m")  # Set green color
    parser.feed("B")
    screen.set_cursor(0, 0)
    screen.insert_mode = True
    parser.feed("\x1b[34m")  # Set blue color
    parser.feed("C")
    assert screen.current_buffer.get_line_text(0) == "CAB       "
    assert screen.current_buffer.get_cell(0, 0) == ("\x1b[34m", "C")
    assert screen.current_buffer.get_cell(1, 0) == ("\x1b[31m", "A")
    assert screen.current_buffer.get_cell(2, 0) == ("\x1b[32m", "B")
    assert screen.cursor_x == 1


def test_write_cell_autowrap():
    screen = Terminal(width=3, height=2)
    parser = Parser(screen)
    parser.feed("\x1b[31m")  # Set red color
    parser.feed("A")
    parser.feed("\x1b[32m")  # Set green color
    parser.feed("B")
    parser.feed("\x1b[34m")  # Set blue color
    parser.feed("C")
    assert screen.current_buffer.get_line_text(0) == "ABC"
    assert screen.cursor_x == 3
    assert screen.cursor_y == 0

    parser.feed("\x1b[33m")  # Set yellow color
    parser.feed("D")  # Should wrap
    assert screen.current_buffer.get_line_text(1) == "D  "
    assert screen.cursor_x == 1
    assert screen.cursor_y == 1


def test_clear_rect():
    screen = Terminal(width=5, height=5)
    for y in range(5):
        for x in range(5):
            screen.current_buffer.set_cell(x, y, "X", "\x1b[31m")

    screen.clear_rect(1, 1, 3, 3)

    for y in range(5):
        for x in range(5):
            if 1 <= x <= 3 and 1 <= y <= 3:
                assert screen.current_buffer.get_cell(x, y) == ("", " ")
            else:
                assert screen.current_buffer.get_cell(x, y) == ("\x1b[31m", "X")


def test_clear_screen():
    screen = Terminal(width=10, height=5)
    for y in range(5):
        for x in range(10):
            screen.current_buffer.set_cell(x, y, chr(ord("A") + y))

    screen.set_cursor(5, 2)

    # Mode 0: Clear from cursor to end of screen
    screen.clear_screen(constants.ERASE_FROM_CURSOR_TO_END)
    assert screen.current_buffer.get_line_text(0) == "AAAAAAAAAA"
    assert screen.current_buffer.get_line_text(1) == "BBBBBBBBBB"
    assert screen.current_buffer.get_line_text(2) == "CCCCC     "
    assert screen.current_buffer.get_line_text(3) == "          "
    assert screen.current_buffer.get_line_text(4) == "          "

    # Reset screen
    for y in range(5):
        for x in range(10):
            screen.current_buffer.set_cell(x, y, chr(ord("A") + y))
    screen.set_cursor(5, 2)

    # Mode 1: Clear from beginning of screen to cursor
    screen.clear_screen(constants.ERASE_FROM_START_TO_CURSOR)
    assert screen.current_buffer.get_line_text(0) == "          "
    assert screen.current_buffer.get_line_text(1) == "          "
    assert screen.current_buffer.get_line_text(2) == "      CCCC"
    assert screen.current_buffer.get_line_text(3) == "DDDDDDDDDD"
    assert screen.current_buffer.get_line_text(4) == "EEEEEEEEEE"

    # Reset screen
    for y in range(5):
        for x in range(10):
            screen.current_buffer.set_cell(x, y, chr(ord("A") + y))
    screen.set_cursor(5, 2)

    # Mode 2: Clear entire screen
    screen.clear_screen(constants.ERASE_ALL)
    for y in range(5):
        assert screen.current_buffer.get_line_text(y) == "          "


def test_clear_line():
    screen = Terminal(width=10, height=1)
    for x in range(10):
        screen.current_buffer.set_cell(x, 0, "X")
    screen.set_cursor(5, 0)

    # Mode 0: Clear from cursor to end of line
    screen.clear_line(constants.ERASE_FROM_CURSOR_TO_END)
    assert screen.current_buffer.get_line_text(0) == "XXXXX     "

    # Reset
    for x in range(10):
        screen.current_buffer.set_cell(x, 0, "X")
    screen.set_cursor(5, 0)

    # Mode 1: Clear from beginning of line to cursor
    screen.clear_line(constants.ERASE_FROM_START_TO_CURSOR)
    assert screen.current_buffer.get_line_text(0) == "      XXXX"

    # Reset
    for x in range(10):
        screen.current_buffer.set_cell(x, 0, "X")
    screen.set_cursor(5, 0)

    # Mode 2: Clear entire line
    screen.clear_line(constants.ERASE_ALL)
    assert screen.current_buffer.get_line_text(0) == "          "


def test_insert_lines():
    screen = Terminal(width=10, height=5)
    for y in range(5):
        screen.current_buffer.set(0, y, f"Line {y}")
    screen.set_cursor(0, 2)

    screen.insert_lines(1)
    assert screen.current_buffer.get_line_text(0) == "Line 0    "
    assert screen.current_buffer.get_line_text(1) == "Line 1    "
    assert screen.current_buffer.get_line_text(2) == "          "
    assert screen.current_buffer.get_line_text(3) == "Line 2    "
    assert screen.current_buffer.get_line_text(4) == "Line 3    "

    # Insert multiple lines
    screen = Terminal(width=10, height=5)
    for y in range(5):
        screen.current_buffer.set(0, y, f"Line {y}")
    screen.set_cursor(0, 1)
    screen.insert_lines(2)
    assert screen.current_buffer.get_line_text(0) == "Line 0    "
    assert screen.current_buffer.get_line_text(1) == "          "
    assert screen.current_buffer.get_line_text(2) == "          "
    assert screen.current_buffer.get_line_text(3) == "Line 1    "
    assert screen.current_buffer.get_line_text(4) == "Line 2    "


def test_delete_lines():
    screen = Terminal(width=10, height=5)
    for y in range(5):
        screen.current_buffer.set(0, y, f"Line {y}")
    screen.set_cursor(0, 1)

    screen.delete_lines(1)
    assert screen.current_buffer.get_line_text(0) == "Line 0    "
    assert screen.current_buffer.get_line_text(1) == "Line 2    "
    assert screen.current_buffer.get_line_text(2) == "Line 3    "
    assert screen.current_buffer.get_line_text(3) == "Line 4    "
    assert screen.current_buffer.get_line_text(4) == "          "

    # Delete multiple lines
    screen = Terminal(width=10, height=5)
    for y in range(5):
        screen.current_buffer.set(0, y, f"Line {y}")
    screen.set_cursor(0, 0)
    screen.delete_lines(2)
    assert screen.current_buffer.get_line_text(0) == "Line 2    "
    assert screen.current_buffer.get_line_text(1) == "Line 3    "
    assert screen.current_buffer.get_line_text(2) == "Line 4    "
    assert screen.current_buffer.get_line_text(3) == "          "
    assert screen.current_buffer.get_line_text(4) == "          "


def test_insert_characters():
    screen = Terminal(width=10, height=1)
    screen.current_buffer.set(0, 0, "ABCDEFGHIJ")
    screen.set_cursor(2, 0)

    screen.insert_characters(3)
    assert screen.current_buffer.get_line_text(0) == "AB   CDEFG"


def test_delete_characters():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.set(0, 0, "12345")
    screen.cursor_x = 2
    screen.cursor_y = 0
    screen.delete_characters(2)
    assert screen.current_buffer.get_line_text(0) == "125       "
