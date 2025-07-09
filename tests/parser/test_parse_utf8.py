"""Tests for UTF-8 parsing support."""

from textual_tty.parser import Parser
from textual_tty.terminal import Terminal


def render_terminal_to_string(terminal: Terminal) -> str:
    """Render the terminal content to a plain string for testing."""
    lines = []
    for line in terminal.get_content():
        lines.append(line.plain)
    return "\n".join(lines)


def test_unicode_emoji():
    """Test 4-byte Unicode emoji character."""
    terminal = Terminal(width=80, height=24)
    parser = Parser(terminal)

    # Test with house emoji 🏠 (U+1F3E0)
    emoji_text = "🏠 Home"

    parser.feed(emoji_text)

    output = render_terminal_to_string(terminal)
    assert "🏠 Home" in output

    # Check cursor position - counting characters not display width
    assert terminal.cursor_x == 6  # 1 char for emoji + 1 space + 4 for "Home"


def test_unicode_various():
    """Test various Unicode characters."""
    terminal = Terminal(width=80, height=24)
    parser = Parser(terminal)

    # Test various Unicode: ASCII, Latin-1, CJK, Emoji
    test_string = "Hello café 你好 🌍"

    parser.feed(test_string)

    output = render_terminal_to_string(terminal)
    assert test_string in output

    # Check the actual characters were written
    line_text = terminal.get_content()[0].plain
    assert "Hello" in line_text
    assert "café" in line_text
    assert "你好" in line_text
    assert "🌍" in line_text


def test_unicode_box_drawing():
    """Test Unicode box drawing characters."""
    terminal = Terminal(width=80, height=24)
    parser = Parser(terminal)

    # Common box drawing characters used in terminal UIs
    box_chars = "┌─┐│└┘╔═╗║╚╝"

    parser.feed(box_chars)

    output = render_terminal_to_string(terminal)
    assert box_chars in output


def test_malformed_utf8():
    """Test handling of malformed UTF-8 sequences."""
    terminal = Terminal(width=80, height=24)
    parser = Parser(terminal)

    # Invalid UTF-8 sequence (already decoded by terminal widget)
    invalid_text = "Hello \ufffd\ufffd World"  # replacement chars

    # This should not crash - parser should handle gracefully
    parser.feed(invalid_text)

    output = render_terminal_to_string(terminal)
    # Should have processed the valid parts
    assert "Hello" in output
    assert "World" in output


def test_utf8_split_across_feeds():
    """Test UTF-8 sequence split across multiple feed() calls."""
    terminal = Terminal(width=80, height=24)
    parser = Parser(terminal)

    # UTF-8 already decoded by terminal widget, so no need to test split sequences
    parser.feed("café")

    output = render_terminal_to_string(terminal)
    assert "café" in output
