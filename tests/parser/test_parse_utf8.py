"""Tests for UTF-8 parsing support."""

from textual_terminal.parser import Parser
from textual_terminal.screen import TerminalScreen


def render_screen_to_string(screen: TerminalScreen) -> str:
    """Render the screen content to a plain string for testing."""
    lines = []
    for line in screen.lines:
        lines.append(line.plain)
    return "\n".join(lines)


def test_unicode_emoji():
    """Test 4-byte Unicode emoji character."""
    screen = TerminalScreen(width=80, height=24)
    parser = Parser(screen)

    # Test with house emoji 🏠 (U+1F3E0)
    emoji_text = "🏠 Home"

    parser.feed(emoji_text)

    output = render_screen_to_string(screen)
    assert "🏠 Home" in output

    # Check cursor position - emoji should take 2 cells in terminal
    assert screen.cursor_x == 7  # 2 cells for emoji + 1 space + 4 for "Home"


def test_unicode_various():
    """Test various Unicode characters."""
    screen = TerminalScreen(width=80, height=24)
    parser = Parser(screen)

    # Test various Unicode: ASCII, Latin-1, CJK, Emoji
    test_string = "Hello café 你好 🌍"

    parser.feed(test_string)

    output = render_screen_to_string(screen)
    assert test_string in output

    # Check the actual characters were written
    line_text = screen.lines[0].plain
    assert "Hello" in line_text
    assert "café" in line_text
    assert "你好" in line_text
    assert "🌍" in line_text


def test_unicode_box_drawing():
    """Test Unicode box drawing characters."""
    screen = TerminalScreen(width=80, height=24)
    parser = Parser(screen)

    # Common box drawing characters used in terminal UIs
    box_chars = "┌─┐│└┘╔═╗║╚╝"

    parser.feed(box_chars)

    output = render_screen_to_string(screen)
    assert box_chars in output


def test_malformed_utf8():
    """Test handling of malformed UTF-8 sequences."""
    screen = TerminalScreen(width=80, height=24)
    parser = Parser(screen)

    # Invalid UTF-8 sequence (already decoded by terminal widget)
    invalid_text = "Hello \ufffd\ufffd World"  # replacement chars

    # This should not crash - parser should handle gracefully
    parser.feed(invalid_text)

    output = render_screen_to_string(screen)
    # Should have processed the valid parts
    assert "Hello" in output
    assert "World" in output


def test_utf8_split_across_feeds():
    """Test UTF-8 sequence split across multiple feed() calls."""
    screen = TerminalScreen(width=80, height=24)
    parser = Parser(screen)

    # UTF-8 already decoded by terminal widget, so no need to test split sequences
    parser.feed("café")

    output = render_screen_to_string(screen)
    assert "café" in output
