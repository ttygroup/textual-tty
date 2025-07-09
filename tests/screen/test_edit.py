from textual_tty.screen import TerminalScreen
from rich.text import Text, Span
from rich.style import Style


def _compare_text_with_spans(text1: Text, text2: Text):
    assert text1.plain == text2.plain
    assert len(text1.spans) == len(text2.spans)

    # Sort spans before comparison to ignore order differences
    sorted_spans1 = sorted(text1.spans, key=lambda s: (s.start, s.end, str(s.style)))
    sorted_spans2 = sorted(text2.spans, key=lambda s: (s.start, s.end, str(s.style)))

    for i in range(len(sorted_spans1)):
        assert sorted_spans1[i].start == sorted_spans2[i].start
        assert sorted_spans1[i].end == sorted_spans2[i].end
        assert sorted_spans1[i].style == sorted_spans2[i].style


def _compare_text_with_spans(text1: Text, text2: Text):
    assert text1.plain == text2.plain
    assert len(text1.spans) == len(text2.spans)

    # Sort spans before comparison to ignore order differences
    sorted_spans1 = sorted(text1.spans, key=lambda s: (s.start, s.end, str(s.style)))
    sorted_spans2 = sorted(text2.spans, key=lambda s: (s.start, s.end, str(s.style)))

    for i in range(len(sorted_spans1)):
        assert sorted_spans1[i].start == sorted_spans2[i].start
        assert sorted_spans1[i].end == sorted_spans2[i].end
        assert sorted_spans1[i].style == sorted_spans2[i].style


def _compare_text_with_spans(text1: Text, text2: Text):
    assert text1.plain == text2.plain
    assert len(text1.spans) == len(text2.spans)

    # Sort spans before comparison to ignore order differences
    sorted_spans1 = sorted(text1.spans, key=lambda s: (s.start, s.end, str(s.style)))
    sorted_spans2 = sorted(text2.spans, key=lambda s: (s.start, s.end, str(s.style)))

    for i in range(len(sorted_spans1)):
        assert sorted_spans1[i].start == sorted_spans2[i].start
        assert sorted_spans1[i].end == sorted_spans2[i].end
        assert sorted_spans1[i].style == sorted_spans2[i].style


def _compare_text_with_spans(text1: Text, text2: Text):
    assert text1.plain == text2.plain
    assert len(text1.spans) == len(text2.spans)

    # Sort spans before comparison to ignore order differences
    sorted_spans1 = sorted(text1.spans, key=lambda s: (s.start, s.end, str(s.style)))
    sorted_spans2 = sorted(text2.spans, key=lambda s: (s.start, s.end, str(s.style)))

    for i in range(len(sorted_spans1)):
        assert sorted_spans1[i].start == sorted_spans2[i].start
        assert sorted_spans1[i].end == sorted_spans2[i].end
        assert sorted_spans1[i].style == sorted_spans2[i].style


def test_write_cell_overwrite():
    screen = TerminalScreen(width=10, height=1)
    screen.write_cell("A", style=Style(color="red"))
    expected_line_1 = Text("A", spans=[Span(0, 1, Style(color="red"))])
    assert screen.lines[0] == expected_line_1
    assert screen.cursor_x == 1

    screen.write_cell("B", style=Style(color="green"))
    expected_line_2 = Text("AB", spans=[Span(0, 1, Style(color="red")), Span(1, 2, Style(color="green"))])
    assert screen.lines[0] == expected_line_2
    assert screen.cursor_x == 2

    screen.set_cursor(0, 0)
    screen.write_cell("C", style=Style(color="blue"))
    expected_line_3 = Text("CB", spans=[Span(0, 1, Style(color="blue")), Span(1, 2, Style(color="green"))])
    assert screen.lines[0] == expected_line_3
    assert screen.cursor_x == 1


def test_write_cell_insert_mode():
    screen = TerminalScreen(width=10, height=1)
    screen.write_cell("A", style=Style(color="red"))
    screen.write_cell("B", style=Style(color="green"))
    screen.set_cursor(0, 0)
    screen.insert_mode = True
    screen.write_cell("C", style=Style(color="blue"))
    expected_line = Text(
        "CAB",
        spans=[
            Span(0, 1, Style(color="blue")),
            Span(1, 2, Style(color="red")),
            Span(2, 3, Style(color="green")),
        ],
    )
    _compare_text_with_spans(screen.lines[0], expected_line)
    assert screen.cursor_x == 1


def test_write_cell_autowrap():
    screen = TerminalScreen(width=3, height=2)
    screen.write_cell("A", style=Style(color="red"))
    screen.write_cell("B", style=Style(color="green"))
    screen.write_cell("C", style=Style(color="blue"))
    expected_line_0 = Text(
        "ABC",
        spans=[
            Span(0, 1, Style(color="red")),
            Span(1, 2, Style(color="green")),
            Span(2, 3, Style(color="blue")),
        ],
    )
    _compare_text_with_spans(screen.lines[0], expected_line_0)
    assert screen.cursor_x == 3  # Cursor is at the end of the line
    assert screen.cursor_y == 0

    screen.write_cell("D", style=Style(color="yellow"))  # Should wrap
    expected_line_1 = Text("D", spans=[Span(0, 1, Style(color="yellow"))])
    _compare_text_with_spans(screen.lines[0], expected_line_0)
    _compare_text_with_spans(screen.lines[1], expected_line_1)
    assert screen.cursor_x == 1
    assert screen.cursor_y == 1


def test_clear_rect():
    screen = TerminalScreen(width=5, height=5)
    for y in range(5):
        screen.lines[y] = Text("ABCDE", spans=[Span(0, 5, Style(color="red"))])

    screen.clear_rect(1, 1, 3, 3)  # Clear a 3x3 rectangle in the middle

    expected_lines = [
        Text("ABCDE", spans=[Span(0, 5, Style(color="red"))]),
        Text("A   E", spans=[Span(0, 1, Style(color="red")), Span(1, 4, Style()), Span(4, 5, Style(color="red"))]),
        Text("A   E", spans=[Span(0, 1, Style(color="red")), Span(1, 4, Style()), Span(4, 5, Style(color="red"))]),
        Text("A   E", spans=[Span(0, 1, Style(color="red")), Span(1, 4, Style()), Span(4, 5, Style(color="red"))]),
        Text("ABCDE", spans=[Span(0, 5, Style(color="red"))]),
    ]
    for i in range(5):
        _compare_text_with_spans(screen.lines[i], expected_lines[i])


def test_clear_screen():
    screen = TerminalScreen(width=10, height=5)
    for y in range(5):
        screen.lines[y] = Text(f"Line {y}", spans=[Span(0, 6, Style(color="red"))])
    screen.set_cursor(5, 2)  # Cursor at Line 2, char 5

    # Mode 0: Clear from cursor to end of screen
    screen.clear_screen(0)
    assert screen.lines[0] == Text("Line 0", spans=[Span(0, 6, Style(color="red"))])
    assert screen.lines[1] == Text("Line 1", spans=[Span(0, 6, Style(color="red"))])
    assert screen.lines[2] == Text("Line      ", spans=[Span(0, 5, Style(color="red"))])
    _compare_text_with_spans(screen.lines[3], Text(""))
    _compare_text_with_spans(screen.lines[4], Text(""))

    # Reset screen
    for y in range(5):
        screen.lines[y] = Text(f"Line {y}", spans=[Span(0, 6, Style(color="red"))])
    screen.set_cursor(5, 2)

    # Mode 1: Clear from beginning of screen to cursor
    screen.clear_screen(1)
    _compare_text_with_spans(screen.lines[0], Text(""))
    _compare_text_with_spans(screen.lines[1], Text(""))
    _compare_text_with_spans(
        screen.lines[2], Text("     2", spans=[Span(5, 6, Style(color="red"))])
    )  # Line 2 cleared to cursor
    _compare_text_with_spans(screen.lines[3], Text("Line 3", spans=[Span(0, 6, Style(color="red"))]))
    _compare_text_with_spans(screen.lines[4], Text("Line 4", spans=[Span(0, 6, Style(color="red"))]))

    # Reset screen
    for y in range(5):
        screen.lines[y] = Text(f"Line {y}", spans=[Span(0, 6, Style(color="red"))])
    screen.set_cursor(5, 2)

    # Mode 2: Clear entire screen
    screen.clear_screen(2)
    for y in range(5):
        _compare_text_with_spans(screen.lines[y], Text(""))


def test_clear_line():
    screen = TerminalScreen(width=10, height=1)
    screen.lines[0] = Text("ABCDEFGHIJ", spans=[Span(0, 10, Style(color="red"))])
    screen.set_cursor(5, 0)

    # Mode 0: Clear from cursor to end of line
    screen.clear_line(0)
    expected_line_0 = Text("ABCDE     ", spans=[Span(0, 5, Style(color="red")), Span(5, 10, Style())])
    _compare_text_with_spans(screen.lines[0], expected_line_0)

    # Reset
    screen.lines[0] = Text("ABCDEFGHIJ", spans=[Span(0, 10, Style(color="red"))])
    screen.set_cursor(5, 0)

    # Mode 1: Clear from beginning of line to cursor
    screen.clear_line(1)
    expected_line_1 = Text("     FGHIJ", spans=[Span(0, 5, Style()), Span(5, 10, Style(color="red"))])
    _compare_text_with_spans(screen.lines[0], expected_line_1)

    # Reset
    screen.lines[0] = Text("ABCDEFGHIJ", spans=[Span(0, 10, Style(color="red"))])
    screen.set_cursor(5, 0)

    # Mode 2: Clear entire line
    screen.clear_line(2)
    expected_line_2 = Text("          ", spans=[Span(0, 10, Style())])
    _compare_text_with_spans(screen.lines[0], expected_line_2)


def test_insert_lines():
    screen = TerminalScreen(width=10, height=5)
    for y in range(5):
        screen.lines[y] = Text(f"Line {y}", spans=[Span(0, 6, Style(color="red"))])
    screen.set_cursor(0, 2)  # Insert at line 2

    screen.insert_lines(1)
    expected_lines = [
        Text("Line 0", spans=[Span(0, 6, Style(color="red"))]),
        Text("Line 1", spans=[Span(0, 6, Style(color="red"))]),
        Text(""),  # Inserted blank line
        Text("Line 2", spans=[Span(0, 6, Style(color="red"))]),
        Text("Line 3", spans=[Span(0, 6, Style(color="red"))]),
    ]
    for i in range(5):
        _compare_text_with_spans(screen.lines[i], expected_lines[i])

    # Insert multiple lines
    screen = TerminalScreen(width=10, height=5)
    for y in range(5):
        screen.lines[y] = Text(f"Line {y}", spans=[Span(0, 6, Style(color="red"))])
    screen.set_cursor(0, 1)
    screen.insert_lines(2)
    expected_lines = [
        Text("Line 0", spans=[Span(0, 6, Style(color="red"))]),
        Text(""),
        Text(""),
        Text("Line 1", spans=[Span(0, 6, Style(color="red"))]),
        Text("Line 2", spans=[Span(0, 6, Style(color="red"))]),
    ]
    for i in range(5):
        _compare_text_with_spans(screen.lines[i], expected_lines[i])


def test_delete_lines():
    screen = TerminalScreen(width=10, height=5)
    for y in range(5):
        screen.lines[y] = Text(f"Line {y}", spans=[Span(0, 6, Style(color="red"))])
    screen.set_cursor(0, 1)  # Delete from line 1

    screen.delete_lines(1)
    expected_lines = [
        Text("Line 0", spans=[Span(0, 6, Style(color="red"))]),
        Text("Line 2", spans=[Span(0, 6, Style(color="red"))]),
        Text("Line 3", spans=[Span(0, 6, Style(color="red"))]),
        Text("Line 4", spans=[Span(0, 6, Style(color="red"))]),
        Text(""),  # New blank line at bottom
    ]
    for i in range(5):
        _compare_text_with_spans(screen.lines[i], expected_lines[i])

    # Delete multiple lines
    screen = TerminalScreen(width=10, height=5)
    for y in range(5):
        screen.lines[y] = Text(f"Line {y}", spans=[Span(0, 6, Style(color="red"))])
    screen.set_cursor(0, 0)
    screen.delete_lines(2)
    expected_lines = [
        Text("Line 2", spans=[Span(0, 6, Style(color="red"))]),
        Text("Line 3", spans=[Span(0, 6, Style(color="red"))]),
        Text("Line 4", spans=[Span(0, 6, Style(color="red"))]),
        Text(""),
        Text(""),
    ]
    for i in range(5):
        _compare_text_with_spans(screen.lines[i], expected_lines[i])


def test_insert_characters():
    screen = TerminalScreen(width=10, height=1)
    screen.lines[0] = Text("ABCDEFGHIJ", spans=[Span(0, 10, Style(color="red"))])
    screen.set_cursor(2, 0)  # Insert at C

    screen.insert_characters(3)
    expected_line = Text(
        "AB   CDEFGHIJ",
        spans=[
            Span(0, 2, Style(color="red")),
            Span(2, 5, Style()),
            Span(5, 13, Style(color="red")),
        ],
    )
    _compare_text_with_spans(screen.lines[0], expected_line)


def test_delete_characters():
    screen = TerminalScreen(width=10, height=5)
    screen.lines[0] = Text("12345", spans=[Span(0, 5, Style(color="red"))])
    screen.cursor_x = 2
    screen.cursor_y = 0
    screen.delete_characters(2)
    expected_line = Text(
        "125",
        spans=[
            Span(0, 2, Style(color="red")),
            Span(2, 3, Style(color="red")),
        ],
    )
    _compare_text_with_spans(screen.lines[0], expected_line)
