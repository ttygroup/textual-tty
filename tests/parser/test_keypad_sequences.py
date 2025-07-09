"""Tests for keypad and device status sequences."""

from textual_terminal.parser import Parser
from textual_terminal.screen import TerminalScreen


def test_csi_p_device_status():
    """Test CSI p sequence (device status query)."""
    screen = TerminalScreen(width=80, height=24)
    parser = Parser(screen)

    # CSI p is a device status query - should be consumed without error
    parser.feed("\x1b[p")

    # Should not appear in screen content and should not crash
    assert screen.cursor_x == 0
    assert screen.cursor_y == 0


def test_esc_greater_than_keypad_numeric_mode():
    """Test ESC > sequence (DECKPNM - keypad numeric mode)."""
    screen = TerminalScreen(width=80, height=24)
    parser = Parser(screen)

    # ESC > sets keypad to numeric mode - should be consumed without error
    parser.feed("\x1b>")

    # Should not appear in screen content and should not crash
    assert screen.cursor_x == 0
    assert screen.cursor_y == 0


def test_keypad_sequences_with_text():
    """Test keypad sequences followed by regular text."""
    screen = TerminalScreen(width=80, height=24)
    parser = Parser(screen)

    # Send keypad sequences followed by text
    parser.feed("\x1b[p\x1b>Hello")

    # Only the text should appear
    assert screen.lines[0][0].char == "H"
    assert screen.lines[0][1].char == "e"
    assert screen.lines[0][2].char == "l"
    assert screen.lines[0][3].char == "l"
    assert screen.lines[0][4].char == "o"
    assert screen.cursor_x == 5
    assert screen.cursor_y == 0
