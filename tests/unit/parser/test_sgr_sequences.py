import pytest
from unittest.mock import Mock
from textual_tty.parser import Parser
from textual_tty.terminal import Terminal
from textual_tty.constants import (
    DEFAULT_TERMINAL_WIDTH,
    DEFAULT_TERMINAL_HEIGHT,
    ESC,
    SGR_RESET,
    SGR_BOLD,
    SGR_NOT_BOLD_NOR_FAINT,
    SGR_ITALIC,
    SGR_NOT_ITALIC,
    SGR_UNDERLINE,
    SGR_NOT_UNDERLINED,
    SGR_BLINK,
    SGR_NOT_BLINKING,
    SGR_REVERSE,
    SGR_NOT_REVERSED,
    SGR_CONCEAL,
    SGR_NOT_CONCEALED,
    SGR_STRIKE,
    SGR_NOT_STRIKETHROUGH,
)


@pytest.fixture
def screen():
    """Return a mock Screen object with necessary attributes."""
    screen = Mock(spec=Terminal)
    screen.width = DEFAULT_TERMINAL_WIDTH
    screen.height = DEFAULT_TERMINAL_HEIGHT
    screen.cursor_x = 0
    screen.cursor_y = 0
    return screen


def test_sgr_reset_all_attributes():
    """Test SGR 0 (Reset all attributes)."""
    terminal = Terminal()
    parser = Parser(terminal)
    parser.feed(f"{ESC}[{SGR_RESET}m")
    assert parser.current_ansi_sequence == f"{ESC}[{SGR_RESET}m"


def test_sgr_bold_and_not_bold():
    """Test SGR 1 (Bold) and SGR 22 (Not bold)."""
    terminal = Terminal()
    parser = Parser(terminal)
    parser.feed(f"{ESC}[{SGR_BOLD}m")
    assert parser.current_ansi_sequence == f"{ESC}[{SGR_BOLD}m"
    parser.feed(f"{ESC}[{SGR_NOT_BOLD_NOR_FAINT}m")
    assert parser.current_ansi_sequence == f"{ESC}[{SGR_NOT_BOLD_NOR_FAINT}m"


def test_sgr_italic_and_not_italic():
    """Test SGR 3 (Italic) and SGR 23 (Not italic)."""
    terminal = Terminal()
    parser = Parser(terminal)
    parser.feed(f"{ESC}[{SGR_ITALIC}m")
    assert parser.current_ansi_sequence == f"{ESC}[{SGR_ITALIC}m"
    parser.feed(f"{ESC}[{SGR_NOT_ITALIC}m")
    assert parser.current_ansi_sequence == f"{ESC}[{SGR_NOT_ITALIC}m"


def test_sgr_underline_and_not_underline():
    """Test SGR 4 (Underline) and SGR 24 (Not underlined)."""
    terminal = Terminal()
    parser = Parser(terminal)
    parser.feed(f"{ESC}[{SGR_UNDERLINE}m")
    assert parser.current_ansi_sequence == f"{ESC}[{SGR_UNDERLINE}m"
    parser.feed(f"{ESC}[{SGR_NOT_UNDERLINED}m")
    assert parser.current_ansi_sequence == f"{ESC}[{SGR_NOT_UNDERLINED}m"


def test_sgr_blink_and_not_blink():
    """Test SGR 5 (Blink) and SGR 25 (Not blinking)."""
    terminal = Terminal()
    parser = Parser(terminal)
    parser.feed(f"{ESC}[{SGR_BLINK}m")
    assert parser.current_ansi_sequence == f"{ESC}[{SGR_BLINK}m"
    parser.feed(f"{ESC}[{SGR_NOT_BLINKING}m")
    assert parser.current_ansi_sequence == f"{ESC}[{SGR_NOT_BLINKING}m"


def test_sgr_reverse_and_not_reverse():
    """Test SGR 7 (Reverse) and SGR 27 (Not reversed)."""
    terminal = Terminal()
    parser = Parser(terminal)
    parser.feed(f"{ESC}[{SGR_REVERSE}m")
    assert parser.current_ansi_sequence == f"{ESC}[{SGR_REVERSE}m"
    parser.feed(f"{ESC}[{SGR_NOT_REVERSED}m")
    assert parser.current_ansi_sequence == f"{ESC}[{SGR_NOT_REVERSED}m"


def test_sgr_conceal_and_not_conceal():
    """Test SGR 8 (Conceal) and SGR 28 (Not concealed)."""
    terminal = Terminal()
    parser = Parser(terminal)
    parser.feed(f"{ESC}[{SGR_CONCEAL}m")
    assert parser.current_ansi_sequence == f"{ESC}[{SGR_CONCEAL}m"
    parser.feed(f"{ESC}[{SGR_NOT_CONCEALED}m")
    assert parser.current_ansi_sequence == f"{ESC}[{SGR_NOT_CONCEALED}m"


def test_sgr_strikethrough_and_not_strikethrough():
    """Test SGR 9 (Strikethrough) and SGR 29 (Not strikethrough)."""
    terminal = Terminal()
    parser = Parser(terminal)
    parser.feed(f"{ESC}[{SGR_STRIKE}m")
    assert parser.current_ansi_sequence == f"{ESC}[{SGR_STRIKE}m"
    parser.feed(f"{ESC}[{SGR_NOT_STRIKETHROUGH}m")
    assert parser.current_ansi_sequence == f"{ESC}[{SGR_NOT_STRIKETHROUGH}m"


def test_sgr_16_color_foreground():
    """Test SGR 30-37 (16-color foreground)."""
    terminal = Terminal()
    parser = Parser(terminal)
    parser.feed(f"{ESC}[31m")  # Red foreground
    assert parser.current_ansi_sequence == f"{ESC}[31m"


def test_sgr_16_color_background():
    """Test SGR 40-47 (16-color background)."""
    terminal = Terminal()
    parser = Parser(terminal)
    parser.feed(f"{ESC}[44m")  # Blue background
    assert parser.current_ansi_sequence == f"{ESC}[44m"


def test_sgr_bright_16_color_foreground():
    """Test SGR 90-97 (Bright 16-color foreground)."""
    terminal = Terminal()
    parser = Parser(terminal)
    parser.feed(f"{ESC}[91m")  # Bright Red foreground
    assert parser.current_ansi_sequence == f"{ESC}[91m"


def test_sgr_bright_16_color_background():
    """Test SGR 100-107 (Bright 16-color background)."""
    terminal = Terminal()
    parser = Parser(terminal)
    parser.feed(f"{ESC}[104m")  # Bright Blue background
    assert parser.current_ansi_sequence == f"{ESC}[104m"


def test_sgr_256_color_foreground():
    """Test SGR 38;5;N (256-color foreground)."""
    terminal = Terminal()
    parser = Parser(terminal)
    parser.feed(f"{ESC}[38;5;123m")
    assert parser.current_ansi_sequence == f"{ESC}[38;5;123m"


def test_sgr_256_color_background():
    """Test SGR 48;5;N (256-color background)."""
    terminal = Terminal()
    parser = Parser(terminal)
    parser.feed(f"{ESC}[48;5;200m")
    assert parser.current_ansi_sequence == f"{ESC}[48;5;200m"


def test_sgr_truecolor_foreground():
    """Test SGR 38;2;R;G;B (Truecolor foreground)."""
    terminal = Terminal()
    parser = Parser(terminal)
    parser.feed(f"{ESC}[38;2;10;20;30m")
    assert parser.current_ansi_sequence == f"{ESC}[38;2;10;20;30m"


def test_sgr_truecolor_background():
    """Test SGR 48;2;R;G;B (Truecolor background)."""
    terminal = Terminal()
    parser = Parser(terminal)
    parser.feed(f"{ESC}[48;2;100;150;200m")
    assert parser.current_ansi_sequence == f"{ESC}[48;2;100;150;200m"


def test_sgr_default_foreground_color():
    """Test SGR 39 (Default foreground color)."""
    terminal = Terminal()
    parser = Parser(terminal)
    parser.feed(f"{ESC}[39m")
    assert parser.current_ansi_sequence == f"{ESC}[39m"


def test_sgr_default_background_color():
    """Test SGR 49 (Default background color)."""
    terminal = Terminal()
    parser = Parser(terminal)
    parser.feed(f"{ESC}[49m")
    assert parser.current_ansi_sequence == f"{ESC}[49m"


def test_sgr_malformed_rgb_foreground():
    """Test SGR with malformed RGB foreground sequence (missing values)."""
    terminal = Terminal()
    parser = Parser(terminal)
    parser.feed(f"{ESC}[38;2;100m")
    assert parser.current_ansi_sequence == f"{ESC}[38;2;100m"


def test_sgr_malformed_rgb_background():
    """Test SGR with malformed RGB background sequence (missing values)."""
    terminal = Terminal()
    parser = Parser(terminal)
    parser.feed(f"{ESC}[48;2;100m")
    assert parser.current_ansi_sequence == f"{ESC}[48;2;100m"
