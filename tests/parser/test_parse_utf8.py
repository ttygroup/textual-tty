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
    emoji_bytes = "🏠 Home".encode("utf-8")

    parser.feed(emoji_bytes)

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
    unicode_bytes = test_string.encode("utf-8")

    parser.feed(unicode_bytes)

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
    box_bytes = box_chars.encode("utf-8")

    parser.feed(box_bytes)

    output = render_screen_to_string(screen)
    assert box_chars in output


def test_malformed_utf8():
    """Test handling of malformed UTF-8 sequences."""
    screen = TerminalScreen(width=80, height=24)
    parser = Parser(screen)

    # Invalid UTF-8 sequence
    invalid_bytes = b"Hello \xff\xfe World"

    # This should not crash - parser should handle gracefully
    parser.feed(invalid_bytes)

    output = render_screen_to_string(screen)
    # Should have processed the valid parts
    assert "Hello" in output
    assert "World" in output


def test_utf8_split_across_feeds():
    """Test UTF-8 sequence split across multiple feed() calls."""
    screen = TerminalScreen(width=80, height=24)
    parser = Parser(screen)

    # UTF-8 for "café" split in the middle of 'é' (C3 A9)
    parser.feed(b"caf\xc3")  # First part ending with first byte of é
    parser.feed(b"\xa9")  # Second byte of é

    output = render_screen_to_string(screen)
    assert "café" in output
