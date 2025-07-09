from rich.style import Style
from rich.text import Text, Span

from textual_tty.terminal import Terminal


def test_clear_rect():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.lines = [
        Text("0123456789", spans=[Span(0, 10, Style(color="red"))]),
        Text("0123456789", spans=[Span(0, 10, Style(color="green"))]),
        Text("0123456789", spans=[Span(0, 10, Style(color="blue"))]),
        Text("0123456789", spans=[Span(0, 10, Style(color="yellow"))]),
        Text("0123456789", spans=[Span(0, 10, Style(color="magenta"))]),
    ]
    screen.clear_rect(2, 1, 5, 3)
    expected_lines = [
        Text("0123456789", spans=[Span(0, 10, Style(color="red"))]),
        Text(
            "01    6789",
            spans=[Span(0, 2, Style(color="green")), Span(2, 6, Style()), Span(6, 10, Style(color="green"))],
        ),
        Text(
            "01    6789", spans=[Span(0, 2, Style(color="blue")), Span(2, 6, Style()), Span(6, 10, Style(color="blue"))]
        ),
        Text(
            "01    6789",
            spans=[Span(0, 2, Style(color="yellow")), Span(2, 6, Style()), Span(6, 10, Style(color="yellow"))],
        ),
        Text("0123456789", spans=[Span(0, 10, Style(color="magenta"))]),
    ]
    for i in range(5):
        assert screen.current_buffer.lines[i] == expected_lines[i]


def test_write_cell_no_auto_wrap():
    screen = Terminal(width=5, height=5)
    screen.auto_wrap = False
    screen.cursor_x = 4
    screen.cursor_y = 0
    screen.current_style = Style(color="red")
    screen.write_text("a")
    assert screen.cursor_x == 4
    screen.current_style = Style(color="blue")
    screen.write_text("b")
    assert screen.cursor_x == 4
    expected_line = Text("    b", spans=[Span(4, 5, Style(color="blue"))])
    assert screen.current_buffer.lines[0] == expected_line


def test_write_cell_clip_at_width():
    screen = Terminal(width=5, height=5)
    screen.auto_wrap = False
    screen.cursor_x = 5  # Set cursor beyond width
    screen.cursor_y = 0
    screen.current_style = Style(color="red")
    screen.write_text("X")
    assert screen.cursor_x == 4  # Should be clamped to width - 1
    expected_line = Text("    X", spans=[Span(4, 5, Style(color="red"))])
    assert screen.current_buffer.lines[0] == expected_line


def test_delete_characters_from_middle_of_line():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.lines[0] = Text("123456789", spans=[Span(0, 9, Style(color="blue"))])
    screen.cursor_x = 2
    screen.cursor_y = 0
    screen.delete_characters(3)
    expected_line = Text("126789", spans=[Span(0, 2, Style(color="blue")), Span(2, 6, Style(color="blue"))])
    assert screen.current_buffer.lines[0] == expected_line


def test_delete_characters_at_end_of_line_no_effect():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.lines[0] = Text("abc", spans=[Span(0, 3, Style(color="blue"))])
    screen.cursor_x = 3
    screen.cursor_y = 0
    screen.delete_characters(1)
    expected_line = Text("abc", spans=[Span(0, 3, Style(color="blue"))])
    assert screen.current_buffer.lines[0] == expected_line


def test_delete_characters_beyond_end_of_line():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.lines[0] = Text("12345", spans=[Span(0, 5, Style(color="blue"))])
    screen.cursor_x = 2
    screen.cursor_y = 0
    screen.delete_characters(10)  # Attempt to delete more than available
    expected_line = Text("12", spans=[Span(0, 2, Style(color="blue"))])
    assert screen.current_buffer.lines[0] == expected_line


def test_delete_characters_from_empty_line():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.lines[0] = Text("", spans=[Span(0, 0, Style(color="blue"))])
    screen.cursor_x = 0
    screen.cursor_y = 0
    screen.delete_characters(5)
    expected_line = Text("", spans=[Span(0, 0, Style(color="blue"))])
    assert screen.current_buffer.lines[0] == expected_line


def test_delete_last_character_on_line():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.lines[0] = Text("abcde", spans=[Span(0, 5, Style(color="blue"))])
    screen.cursor_x = 4
    screen.cursor_y = 0
    screen.delete_characters(1)
    expected_line = Text("abcd", spans=[Span(0, 4, Style(color="blue"))])
    assert screen.current_buffer.lines[0] == expected_line


def test_write_cell_overwrite_at_end_of_line():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.lines[0] = Text("abc", spans=[Span(0, 3, Style(color="blue"))])
    screen.cursor_x = 3
    screen.cursor_y = 0
    screen.current_style = Style(color="red")
    screen.write_text("X")
    expected_line = Text("abcX", spans=[Span(0, 3, Style(color="blue")), Span(3, 4, Style(color="red"))])
    assert screen.current_buffer.lines[0] == expected_line


def test_write_cell_overwrite_empty_line():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.lines[0] = Text("", spans=[Span(0, 0, Style(color="blue"))])
    screen.cursor_x = 0
    screen.cursor_y = 0
    screen.current_style = Style(color="green")
    screen.write_text("A")
    expected_line = Text("A", spans=[Span(0, 1, Style(color="green"))])
    assert screen.current_buffer.lines[0] == expected_line


def test_insert_characters_at_end_of_line():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.lines[0] = Text("12345", spans=[Span(0, 5, Style(color="magenta"))])
    screen.cursor_x = 5
    screen.cursor_y = 0
    screen.insert_characters(2)
    expected_line = Text("12345  ", spans=[Span(0, 5, Style(color="magenta")), Span(5, 7, Style())])
    assert screen.current_buffer.lines[0] == expected_line


def test_clear_line_invalid_cursor():
    screen = Terminal(width=10, height=5)
    screen.cursor_y = 10  # Invalid cursor position
    screen.clear_line(0)
    # Should not raise an error and do nothing


def test_clear_screen_invalid_cursor():
    screen = Terminal(width=10, height=5)
    screen.cursor_y = 10  # Invalid cursor position
    screen.clear_screen(0)
    # Should not raise an error but still clear the screen below
    assert all(line.plain == "" for line in screen.current_buffer.lines)


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
    screen.current_buffer.lines[0] = Text("12345", spans=[Span(0, 5, Style(color="blue"))])
    screen.cursor_x = 2
    screen.cursor_y = 0
    style = Style(color="red")
    screen.current_style = style
    screen.write_text("X")
    expected_line = Text(
        "12X45", spans=[Span(0, 2, Style(color="blue")), Span(2, 3, style), Span(3, 5, Style(color="blue"))]
    )
    assert screen.current_buffer.lines[0] == expected_line


def test_write_cell_insert_with_style():
    screen = Terminal(width=10, height=5)
    screen.insert_mode = True
    screen.current_buffer.lines[0] = Text("12345", spans=[Span(0, 5, Style(color="blue"))])
    screen.cursor_x = 2
    screen.cursor_y = 0
    style = Style(color="red")
    screen.current_style = style
    screen.write_text("X")
    expected_line = Text(
        "12X345", spans=[Span(0, 2, Style(color="blue")), Span(2, 3, style), Span(3, 6, Style(color="blue"))]
    )
    assert screen.current_buffer.lines[0] == expected_line


def test_write_cell_insert_at_end_of_line():
    screen = Terminal(width=10, height=5)
    screen.insert_mode = True
    screen.current_buffer.lines[0] = Text("123", spans=[Span(0, 3, Style(color="blue"))])
    screen.cursor_x = 5
    screen.cursor_y = 0
    screen.current_style = Style(color="red")
    screen.write_text("X")
    expected_line = Text(
        "123  X", spans=[Span(0, 3, Style(color="blue")), Span(3, 5, Style()), Span(5, 6, Style(color="red"))]
    )
    assert screen.current_buffer.lines[0] == expected_line


def test_write_cell_overwrite_at_start_of_line():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.lines[0] = Text("12345", spans=[Span(0, 5, Style(color="blue"))])
    screen.cursor_x = 0
    screen.cursor_y = 0
    screen.current_style = Style(color="red")
    screen.write_text("X")
    expected_line = Text("X2345", spans=[Span(0, 1, Style(color="red")), Span(1, 5, Style(color="blue"))])
    assert screen.current_buffer.lines[0] == expected_line


def test_write_cell_insert_and_truncate():
    screen = Terminal(width=5, height=5)
    screen.insert_mode = True
    screen.current_buffer.lines[0] = Text("12345", spans=[Span(0, 5, Style(color="blue"))])
    screen.cursor_x = 2
    screen.cursor_y = 0
    screen.current_style = Style(color="red")
    screen.write_text("X")
    expected_line = Text(
        "12X34",
        spans=[Span(0, 2, Style(color="blue")), Span(2, 3, Style(color="red")), Span(3, 5, Style(color="blue"))],
    )
    assert screen.current_buffer.lines[0] == expected_line


def test_clear_rect_with_style():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.lines = [
        Text("0123456789", spans=[Span(0, 10, Style(color="red"))]),
        Text("0123456789", spans=[Span(0, 10, Style(color="green"))]),
        Text("0123456789", spans=[Span(0, 10, Style(color="blue"))]),
        Text("0123456789", spans=[Span(0, 10, Style(color="yellow"))]),
        Text("0123456789", spans=[Span(0, 10, Style(color="magenta"))]),
    ]
    style = Style(color="red")
    screen.clear_rect(2, 1, 5, 3, style)
    expected_lines = [
        Text("0123456789", spans=[Span(0, 10, Style(color="red"))]),
        Text(
            "01    6789", spans=[Span(0, 2, Style(color="green")), Span(2, 6, style), Span(6, 10, Style(color="green"))]
        ),
        Text(
            "01    6789", spans=[Span(0, 2, Style(color="blue")), Span(2, 6, style), Span(6, 10, Style(color="blue"))]
        ),
        Text(
            "01    6789",
            spans=[Span(0, 2, Style(color="yellow")), Span(2, 6, style), Span(6, 10, Style(color="yellow"))],
        ),
        Text("0123456789", spans=[Span(0, 10, Style(color="magenta"))]),
    ]
    for i in range(5):
        assert screen.current_buffer.lines[i] == expected_lines[i]


def test_write_cell_overwrite_at_start_of_line_with_style():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.lines[0] = Text("12345", spans=[Span(0, 5, Style(color="blue"))])
    screen.cursor_x = 0
    screen.cursor_y = 0
    style = Style(color="red")
    screen.current_style = style
    screen.write_text("X")
    expected_line = Text("X2345", spans=[Span(0, 1, style), Span(1, 5, Style(color="blue"))])
    assert screen.current_buffer.lines[0] == expected_line


def test_write_cell_overwrite_middle_of_line_with_style():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.lines[0] = Text("0123456789", spans=[Span(0, 10, Style(color="blue"))])
    screen.cursor_x = 5
    screen.cursor_y = 0
    style = Style(color="red")
    screen.current_style = style
    screen.write_text("X")
    expected_line = Text(
        "01234X6789", spans=[Span(0, 5, Style(color="blue")), Span(5, 6, style), Span(6, 10, Style(color="blue"))]
    )
    assert screen.current_buffer.lines[0] == expected_line


def test_write_cell_insert_middle_of_line_with_style():
    screen = Terminal(width=10, height=5)
    screen.insert_mode = True
    screen.current_buffer.lines[0] = Text("0123456789", spans=[Span(0, 10, Style(color="blue"))])
    screen.cursor_x = 5
    screen.cursor_y = 0
    style = Style(color="red")
    screen.current_style = style
    screen.write_text("X")
    expected_line = Text(
        "01234X5678", spans=[Span(0, 5, Style(color="blue")), Span(5, 6, style), Span(6, 10, Style(color="blue"))]
    )
    assert screen.current_buffer.lines[0] == expected_line


def test_write_cell_insert_at_start_of_line_with_style():
    screen = Terminal(width=10, height=5)
    screen.insert_mode = True
    screen.current_buffer.lines[0] = Text("0123456789", spans=[Span(0, 10, Style(color="blue"))])
    screen.cursor_x = 0
    screen.cursor_y = 0
    style = Style(color="red")
    screen.current_style = style
    screen.write_text("X")
    expected_line = Text("X012345678", spans=[Span(0, 1, style), Span(1, 10, Style(color="blue"))])
    assert screen.current_buffer.lines[0] == expected_line


def test_write_cell_insert_at_end_of_line_with_style():
    screen = Terminal(width=10, height=5)
    screen.insert_mode = True
    screen.current_buffer.lines[0] = Text("012345678", spans=[Span(0, 9, Style(color="blue"))])
    screen.cursor_x = 9
    screen.cursor_y = 0
    style = Style(color="red")
    screen.current_style = style
    screen.write_text("X")
    expected_line = Text("012345678X", spans=[Span(0, 9, Style(color="blue")), Span(9, 10, style)])
    assert screen.current_buffer.lines[0] == expected_line


def test_write_cell_insert_into_empty_line_with_style():
    screen = Terminal(width=10, height=5)
    screen.insert_mode = True
    screen.cursor_x = 0
    screen.cursor_y = 0
    style = Style(color="red")
    screen.current_style = style
    screen.write_text("X")
    expected_line = Text("X", spans=[Span(0, 1, style)])
    assert screen.current_buffer.lines[0] == expected_line


def test_write_cell_overwrite_into_empty_line_with_style():
    screen = Terminal(width=10, height=5)
    screen.cursor_x = 0
    screen.cursor_y = 0
    style = Style(color="red")
    screen.current_style = style
    screen.write_text("X")
    expected_line = Text("X", spans=[Span(0, 1, style)])
    assert screen.current_buffer.lines[0] == expected_line


def test_write_cell_overwrite_beyond_end_of_line_with_style():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.lines[0] = Text("abc", spans=[Span(0, 3, Style(color="blue"))])
    screen.cursor_x = 5
    screen.cursor_y = 0
    style = Style(color="red")
    screen.current_style = style
    screen.write_text("X")
    expected_line = Text("abc  X", spans=[Span(0, 3, Style(color="blue")), Span(3, 5, Style()), Span(5, 6, style)])
    assert screen.current_buffer.lines[0] == expected_line


def test_write_cell_insert_beyond_end_of_line_with_style():
    screen = Terminal(width=10, height=5)
    screen.insert_mode = True
    screen.current_buffer.lines[0] = Text("abc", spans=[Span(0, 3, Style(color="blue"))])
    screen.cursor_x = 5
    screen.cursor_y = 0
    style = Style(color="red")
    screen.current_style = style
    screen.write_text("X")
    expected_line = Text("abc  X", spans=[Span(0, 3, Style(color="blue")), Span(3, 5, Style()), Span(5, 6, style)])
    assert screen.current_buffer.lines[0] == expected_line


def test_clear_line_from_cursor_to_end():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.lines[0] = Text("0123456789", spans=[Span(0, 10, Style(color="red"))])
    screen.cursor_x = 5
    screen.cursor_y = 0
    screen.clear_line(0)
    expected_line = Text("01234", spans=[Span(0, 5, Style(color="red"))])
    assert screen.current_buffer.lines[0] == expected_line


def test_clear_line_from_beginning_to_cursor():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.lines[0] = Text("0123456789", spans=[Span(0, 10, Style(color="red"))])
    screen.cursor_x = 5
    screen.cursor_y = 0
    screen.clear_line(1)
    expected_line = Text("     56789", spans=[Span(5, 10, Style(color="red"))])
    assert screen.current_buffer.lines[0] == expected_line


def test_clear_line_entire_line():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.lines[0] = Text("0123456789", spans=[Span(0, 10, Style(color="red"))])
    screen.cursor_y = 0
    screen.clear_line(2)
    expected_line = Text("")
    assert screen.current_buffer.lines[0] == expected_line


def test_clear_line_with_mixed_styles():
    screen = Terminal(width=10, height=5)
    screen.current_buffer.lines[0] = Text.assemble(
        ("ABC", Style(color="red")), ("DEF", Style(color="green")), ("GHI", Style(color="blue"))
    )
    screen.cursor_x = 3
    screen.cursor_y = 0
    screen.clear_line(0)  # Clear from cursor to end
    expected_line = Text("ABC", spans=[Span(0, 3, Style(color="red"))])
    assert screen.current_buffer.lines[0] == expected_line

    screen.current_buffer.lines[1] = Text.assemble(
        ("ABC", Style(color="red")), ("DEF", Style(color="green")), ("GHI", Style(color="blue"))
    )
    screen.cursor_x = 3
    screen.cursor_y = 1
    screen.clear_line(1)  # Clear from beginning to cursor
    expected_line = Text("   DEFGHI", spans=[Span(3, 6, Style(color="green")), Span(6, 9, Style(color="blue"))])
    assert screen.current_buffer.lines[1] == expected_line
