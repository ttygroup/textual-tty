from textual_tty.terminal import Terminal
from textual_tty.constants import (
    ERASE_FROM_CURSOR_TO_END,
    ERASE_FROM_START_TO_CURSOR,
    ERASE_ALL,
)


def test_clear_rect():
    screen = Terminal(width=10, height=5)
    for y in range(5):
        for x in range(10):
            screen.current_buffer.set_cell(x, y, "X")

    screen.clear_rect(2, 1, 5, 3)
    for y in range(5):
        for x in range(10):
            if 1 <= y <= 3 and 2 <= x <= 5:
                assert screen.current_buffer.get_cell(x, y) == ("", " ")
            else:
                assert screen.current_buffer.get_cell(x, y) == ("", "X")


def test_write_cell_no_auto_wrap():
    screen = Terminal(width=5, height=5)
    screen.auto_wrap = False
    screen.cursor_x = 4
    screen.cursor_y = 0
    screen.write_text("a")
    assert screen.cursor_x == 4
    screen.write_text("b")
    assert screen.cursor_x == 4
    assert screen.current_buffer.get_line_text(0) == "    b"


def test_write_cell_clip_at_width():
    screen = Terminal(width=5, height=5)
    screen.auto_wrap = False
    screen.cursor_x = 5  # Set cursor beyond width
    screen.cursor_y = 0
    screen.write_text("X")
    assert screen.cursor_x == 4  # Should be clamped to width - 1
    assert screen.current_buffer.get_line_text(0) == "    X"


def test_delete_characters_from_middle_of_line():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.set(0, 0, "123456789")
    screen.cursor_x = 2
    screen.cursor_y = 0
    screen.delete_characters(3)
    assert screen.current_buffer.get_line_text(0) == "126789    "


def test_delete_characters_at_end_of_line_no_effect():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.set(0, 0, "abc")
    screen.cursor_x = 3
    screen.cursor_y = 0
    screen.delete_characters(1)
    assert screen.current_buffer.get_line_text(0) == "abc       "


def test_delete_characters_beyond_end_of_line():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.set(0, 0, "12345")
    screen.cursor_x = 2
    screen.cursor_y = 0
    screen.delete_characters(10)  # Attempt to delete more than available
    assert screen.current_buffer.get_line_text(0) == "12        "


def test_delete_characters_from_empty_line():
    screen = Terminal(width=10, height=5)
    screen.cursor_x = 0
    screen.cursor_y = 0
    screen.delete_characters(5)
    assert screen.current_buffer.get_line_text(0) == "          "


def test_delete_last_character_on_line():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.set(0, 0, "abcde")
    screen.cursor_x = 4
    screen.cursor_y = 0
    screen.delete_characters(1)
    assert screen.current_buffer.get_line_text(0) == "abcd      "


def test_write_cell_overwrite_at_end_of_line():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.set(0, 0, "abc")
    screen.cursor_x = 3
    screen.cursor_y = 0
    screen.write_text("X")
    assert screen.current_buffer.get_line_text(0) == "abcX      "


def test_write_cell_overwrite_empty_line():
    screen = Terminal(width=10, height=5)
    screen.cursor_x = 0
    screen.cursor_y = 0
    screen.write_text("A")
    assert screen.current_buffer.get_line_text(0) == "A         "


def test_insert_characters_at_end_of_line():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.set(0, 0, "12345")
    screen.cursor_x = 5
    screen.cursor_y = 0
    screen.insert_characters(2)
    assert screen.current_buffer.get_line_text(0) == "12345     "


def test_clear_line_invalid_cursor():
    screen = Terminal(width=10, height=5)
    screen.cursor_y = 10  # Invalid cursor position
    screen.clear_line(ERASE_FROM_CURSOR_TO_END)
    # Should not raise an error and do nothing


def test_clear_screen_invalid_cursor():
    screen = Terminal(width=10, height=5)
    screen.cursor_y = 10  # Invalid cursor position
    screen.clear_screen(0)
    # Should not raise an error but still clear the screen below
    assert all(c == " " for c in screen.current_buffer.get_line_text(4))


def test_write_cell_invalid_cursor():
    screen = Terminal(width=10, height=5)
    screen.cursor_y = 10  # Invalid cursor position
    screen.write_text("a")
    # Should not raise an error and do nothing


def test_insert_characters_invalid_cursor():
    screen = Terminal(width=10, height=5)
    screen.cursor_y = 10  # Invalid cursor position
    screen.insert_characters(1)
    # Should not raise an error and do nothing


def test_delete_characters_invalid_cursor():
    screen = Terminal(width=10, height=5)
    screen.cursor_y = 10  # Invalid cursor position
    screen.delete_characters(1)
    # Should not raise an error and do nothing


def test_write_cell_overwrite_with_style():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.set(0, 0, "12345")
    screen.cursor_x = 2
    screen.cursor_y = 0
    screen.parser.current_ansi_sequence = "\x1b[31m"
    screen.write_text("X")
    assert screen.current_buffer.get_cell(2, 0) == ("\x1b[31m", "X")


def test_write_cell_insert_with_style():
    screen = Terminal(width=10, height=5)
    screen.insert_mode = True
    screen.current_buffer.set(0, 0, "12345")
    screen.cursor_x = 2
    screen.cursor_y = 0
    screen.parser.current_ansi_sequence = "\x1b[31m"
    screen.write_text("X")
    assert screen.current_buffer.get_line_text(0) == "12X345    "
    assert screen.current_buffer.get_cell(2, 0) == ("\x1b[31m", "X")


def test_write_cell_insert_at_end_of_line():
    screen = Terminal(width=10, height=5)
    screen.insert_mode = True
    screen.current_buffer.set(0, 0, "123")
    screen.cursor_x = 5
    screen.cursor_y = 0
    screen.parser.current_ansi_sequence = "\x1b[31m"
    screen.write_text("X")
    assert screen.current_buffer.get_line_text(0) == "123  X    "
    assert screen.current_buffer.get_cell(5, 0) == ("\x1b[31m", "X")


def test_write_cell_overwrite_at_start_of_line():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.set(0, 0, "12345")
    screen.cursor_x = 0
    screen.cursor_y = 0
    screen.parser.current_ansi_sequence = "\x1b[31m"
    screen.write_text("X")
    assert screen.current_buffer.get_line_text(0) == "X2345     "
    assert screen.current_buffer.get_cell(0, 0) == ("\x1b[31m", "X")


def test_write_cell_insert_and_truncate():
    screen = Terminal(width=5, height=5)
    screen.insert_mode = True
    screen.current_buffer.set(0, 0, "12345")
    screen.cursor_x = 2
    screen.cursor_y = 0
    screen.parser.current_ansi_sequence = "\x1b[31m"
    screen.write_text("X")
    assert screen.current_buffer.get_line_text(0) == "12X34"
    assert screen.current_buffer.get_cell(2, 0) == ("\x1b[31m", "X")


def test_clear_rect_with_style():
    screen = Terminal(width=10, height=5)
    for y in range(5):
        for x in range(10):
            screen.current_buffer.set_cell(x, y, "X", f"\x1b[{31+y}m")

    screen.clear_rect(2, 1, 5, 3, "\x1b[33m")
    for y in range(5):
        for x in range(10):
            if 1 <= y <= 3 and 2 <= x <= 5:
                assert screen.current_buffer.get_cell(x, y) == ("\x1b[33m", " ")
            else:
                assert screen.current_buffer.get_cell(x, y) == (f"\x1b[{31+y}m", "X")


def test_write_cell_overwrite_at_start_of_line_with_style():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.set(0, 0, "12345")
    screen.cursor_x = 0
    screen.cursor_y = 0
    screen.parser.current_ansi_sequence = "\x1b[31m"
    screen.write_text("X")
    assert screen.current_buffer.get_line_text(0) == "X2345     "
    assert screen.current_buffer.get_cell(0, 0) == ("\x1b[31m", "X")


def test_write_cell_overwrite_middle_of_line_with_style():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.set(0, 0, "0123456789")
    screen.cursor_x = 5
    screen.cursor_y = 0
    screen.parser.current_ansi_sequence = "\x1b[31m"
    screen.write_text("X")
    assert screen.current_buffer.get_line_text(0) == "01234X6789"
    assert screen.current_buffer.get_cell(5, 0) == ("\x1b[31m", "X")


def test_write_cell_insert_middle_of_line_with_style():
    screen = Terminal(width=10, height=5)
    screen.insert_mode = True
    screen.current_buffer.set(0, 0, "0123456789")
    screen.cursor_x = 5
    screen.cursor_y = 0
    screen.parser.current_ansi_sequence = "\x1b[31m"
    screen.write_text("X")
    assert screen.current_buffer.get_line_text(0) == "01234X5678"
    assert screen.current_buffer.get_cell(5, 0) == ("\x1b[31m", "X")


def test_write_cell_insert_at_start_of_line_with_style():
    screen = Terminal(width=10, height=5)
    screen.insert_mode = True
    screen.current_buffer.set(0, 0, "0123456789")
    screen.cursor_x = 0
    screen.cursor_y = 0
    screen.parser.current_ansi_sequence = "\x1b[31m"
    screen.write_text("X")
    assert screen.current_buffer.get_line_text(0) == "X012345678"
    assert screen.current_buffer.get_cell(0, 0) == ("\x1b[31m", "X")


def test_write_cell_insert_at_end_of_line_with_style():
    screen = Terminal(width=10, height=5)
    screen.insert_mode = True
    screen.current_buffer.set(0, 0, "012345678")
    screen.cursor_x = 9
    screen.cursor_y = 0
    screen.parser.current_ansi_sequence = "\x1b[31m"
    screen.write_text("X")
    assert screen.current_buffer.get_line_text(0) == "012345678X"
    assert screen.current_buffer.get_cell(9, 0) == ("\x1b[31m", "X")


def test_write_cell_insert_into_empty_line_with_style():
    screen = Terminal(width=10, height=5)
    screen.insert_mode = True
    screen.cursor_x = 0
    screen.cursor_y = 0
    screen.parser.current_ansi_sequence = "\x1b[31m"
    screen.write_text("X")
    assert screen.current_buffer.get_line_text(0) == "X         "
    assert screen.current_buffer.get_cell(0, 0) == ("\x1b[31m", "X")


def test_write_cell_overwrite_into_empty_line_with_style():
    screen = Terminal(width=10, height=5)
    screen.cursor_x = 0
    screen.cursor_y = 0
    screen.parser.current_ansi_sequence = "\x1b[31m"
    screen.write_text("X")
    assert screen.current_buffer.get_line_text(0) == "X         "
    assert screen.current_buffer.get_cell(0, 0) == ("\x1b[31m", "X")


def test_write_cell_overwrite_beyond_end_of_line_with_style():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.set(0, 0, "abc")
    screen.cursor_x = 5
    screen.cursor_y = 0
    screen.parser.current_ansi_sequence = "\x1b[31m"
    screen.write_text("X")
    assert screen.current_buffer.get_line_text(0) == "abc  X    "
    assert screen.current_buffer.get_cell(5, 0) == ("\x1b[31m", "X")


def test_write_cell_insert_beyond_end_of_line_with_style():
    screen = Terminal(width=10, height=5)
    screen.insert_mode = True
    screen.current_buffer.set(0, 0, "abc")
    screen.cursor_x = 5
    screen.cursor_y = 0
    screen.parser.current_ansi_sequence = "\x1b[31m"
    screen.write_text("X")
    assert screen.current_buffer.get_line_text(0) == "abc  X    "
    assert screen.current_buffer.get_cell(5, 0) == ("\x1b[31m", "X")


def test_clear_line_from_cursor_to_end():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.set(0, 0, "0123456789")
    screen.cursor_x = 5
    screen.cursor_y = 0
    screen.clear_line(ERASE_FROM_CURSOR_TO_END)
    assert screen.current_buffer.get_line_text(0) == "01234     "


def test_clear_line_from_beginning_to_cursor():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.set(0, 0, "0123456789")
    screen.cursor_x = 5
    screen.cursor_y = 0
    screen.clear_line(ERASE_FROM_START_TO_CURSOR)
    assert screen.current_buffer.get_line_text(0) == "     56789"


def test_clear_line_entire_line():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.set(0, 0, "0123456789")
    screen.cursor_y = 0
    screen.clear_line(ERASE_ALL)
    assert screen.current_buffer.get_line_text(0) == "          "


def test_clear_line_with_mixed_styles():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.set(0, 0, "ABCDEFGHI")
    screen.cursor_x = 3
    screen.cursor_y = 0
    screen.clear_line(0)  # Clear from cursor to end
    assert screen.current_buffer.get_line_text(0) == "ABC       "

    screen.current_buffer.set(0, 1, "ABCDEFGHI")
    screen.cursor_x = 3
    screen.cursor_y = 1
    screen.clear_line(1)  # Clear from beginning to cursor
    assert screen.current_buffer.get_line_text(1) == "   DEFGHI  "
