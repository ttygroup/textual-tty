"""Tests for keypad and device status sequences."""

from textual_tty.parser import Parser
from textual_tty.terminal import Terminal


def test_csi_p_device_status():
    """Test CSI p sequence (device status query)."""
    screen = Terminal(width=80, height=24)
    parser = Parser(screen)

    # CSI p is a device status query - should be consumed without error
    parser.feed("\x1b[p")

    # Should not appear in screen content and should not crash
    assert screen.cursor_x == 0
    assert screen.cursor_y == 0


def test_esc_greater_than_keypad_numeric_mode():
    """Test ESC > sequence (DECKPNM - keypad numeric mode)."""
    screen = Terminal(width=80, height=24)
    parser = Parser(screen)

    # ESC > sets keypad to numeric mode - should be consumed without error
    parser.feed("\x1b>")

    # Should not appear in screen content and should not crash
    assert screen.cursor_x == 0
    assert screen.cursor_y == 0


def test_keypad_sequences_with_text():
    """Test keypad sequences followed by regular text."""
    screen = Terminal(width=80, height=24)
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


def test_csi_cursor_save_restore():
    """Test CSI s/u cursor save/restore sequences."""
    screen = Terminal(width=80, height=24)
    parser = Parser(screen)

    # Move cursor and save position
    parser.feed("\x1b[10;20H")  # Move to row 10, col 20
    parser.feed("\x1b[s")  # Save cursor

    # Move cursor elsewhere
    parser.feed("\x1b[5;5H")  # Move to row 5, col 5
    assert screen.cursor_x == 4  # 0-based
    assert screen.cursor_y == 4  # 0-based

    # Restore cursor
    parser.feed("\x1b[u")  # Restore cursor
    assert screen.cursor_x == 19  # 0-based (was col 20)
    assert screen.cursor_y == 9  # 0-based (was row 10)


def test_csi_privacy_message():
    """Test CSI ^ sequence (Privacy Message)."""
    screen = Terminal(width=80, height=24)
    parser = Parser(screen)

    # CSI ^ with parameter should be consumed
    parser.feed("\x1b[38^")

    # Should not appear in screen content and should not crash
    assert screen.cursor_x == 0
    assert screen.cursor_y == 0
