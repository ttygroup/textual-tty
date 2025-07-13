"""Tests for keypad mode and device control sequences."""

from textual_tty.parser import Parser
from textual_tty.terminal import Terminal
from textual_tty.constants import ESC, DECKPAM_APPLICATION_KEYPAD


def render_terminal_to_string(terminal: Terminal) -> str:
    """Render the terminal content to a plain string for testing."""
    return "\n".join(render_lines_to_string(terminal.get_content()))


def render_lines_to_string(lines: list[list[tuple[str, str]]]) -> list[str]:
    """Render a list of lines to a list of strings for testing."""
    output = []
    for line in lines:
        output.append("".join(char for _, char in line))
    return output


def test_keypad_application_mode():
    """Test ESC = (DECKPAM) - Application Keypad Mode."""
    terminal = Terminal(width=80, height=24)
    parser = Parser(terminal)

    # Initially should be in normal keypad mode
    assert not terminal.application_keypad

    # Send DECKPAM sequence
    parser.feed(f"{ESC}=")

    # Should now be in application keypad mode
    assert terminal.application_keypad


def test_keypad_normal_mode():
    """Test ESC > (DECKPNM) - Normal Keypad Mode."""
    terminal = Terminal(width=80, height=24)
    parser = Parser(terminal)

    # Start in application mode
    terminal.set_mode(DECKPAM_APPLICATION_KEYPAD, True)  # Application keypad mode
    assert terminal.application_keypad

    # Send DECKPNM sequence
    parser.feed("\x1b>")

    # Should now be in normal keypad mode
    assert not terminal.application_keypad


def test_device_control_string():
    """Test ESC P...ESC \\ (DCS) - Device Control String."""
    terminal = Terminal(width=80, height=24)
    parser = Parser(terminal)

    # Send a DCS sequence (should be ignored but not crash)
    parser.feed("\x1bPsome device control data\x1b\\")

    # Should not affect terminal content
    output = render_terminal_to_string(terminal)
    assert "some device control data" not in output

    # Parser should be back in GROUND state
    parser.feed("Hello")
    output = render_terminal_to_string(terminal)
    assert "Hello" in output


def test_device_control_string_with_bel():
    """Test DCS terminated with BEL instead of ST."""
    terminal = Terminal(width=80, height=24)
    parser = Parser(terminal)

    # Send a DCS sequence terminated with BEL
    parser.feed("\x1bPdevice data\x07")

    # Should not affect terminal content
    output = render_terminal_to_string(terminal)
    assert "device data" not in output

    # Parser should be back in GROUND state
    parser.feed("World")
    output = render_terminal_to_string(terminal)
    assert "World" in output


def test_string_terminator():
    """Test ESC \\ (ST) - String Terminator."""
    terminal = Terminal(width=80, height=24)
    parser = Parser(terminal)

    # ST should be consumed but not affect output
    parser.feed("\x1b\\")
    parser.feed("Text")

    output = render_terminal_to_string(terminal)
    assert "Text" in output


def test_keypad_mode_sequences_with_text():
    """Test keypad sequences followed by regular text."""
    terminal = Terminal(width=80, height=24)
    parser = Parser(terminal)

    # Test sequence: DECKPAM, text, DECKPNM, more text
    parser.feed("\x1b=Hello\x1b> World")

    # Check mode was set and text was written
    assert not terminal.application_keypad  # Should end in normal mode
    output = render_terminal_to_string(terminal)
    assert "Hello World" in output


def test_dcs_with_complex_content():
    """Test DCS with more complex control characters inside."""
    terminal = Terminal(width=80, height=24)
    parser = Parser(terminal)

    # DCS with various characters including CSI-like sequences
    parser.feed("\x1bP1;2;3;test[31mdata\x1b\\")

    # Should not affect terminal (DCS is ignored)
    output = render_terminal_to_string(terminal)
    assert "test" not in output
    assert "data" not in output

    # Parser should handle normal text afterwards
    parser.feed("Normal text")
    output = render_terminal_to_string(terminal)
    assert "Normal text" in output
