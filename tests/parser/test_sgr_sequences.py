import pytest
from unittest.mock import Mock
from textual_terminal.parser import Parser
from textual_terminal.screen import TerminalScreen
from rich.style import Style


@pytest.fixture
def screen():
    """Return a mock Screen object with necessary attributes."""
    screen = Mock(spec=TerminalScreen)
    screen.current_style = Style()  # Initialize with a default Style object
    screen.width = 80
    screen.height = 24
    screen.cursor_x = 0
    screen.cursor_y = 0
    screen.scroll_top = 0
    screen.scroll_bottom = screen.height - 1
    return screen


def test_sgr_reset(screen):
    """Test SGR 0 (reset all attributes)."""
    parser = Parser(screen)
    screen.current_style = Style(bold=True, color="red", bgcolor="blue")
    parser.feed(b"\x1b[0m")
    assert screen.current_style == Style()


def test_sgr_bold(screen):
    """Test SGR 1 (bold)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[1m")
    assert screen.current_style.bold is True


def test_sgr_dim(screen):
    """Test SGR 2 (dim)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[2m")
    assert screen.current_style.dim is True


def test_sgr_italic(screen):
    """Test SGR 3 (italic)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[3m")
    assert screen.current_style.italic is True


def test_sgr_underline(screen):
    """Test SGR 4 (underline)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[4m")
    assert screen.current_style.underline is True


def test_sgr_blink(screen):
    """Test SGR 5 (blink)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[5m")
    assert screen.current_style.blink is True


def test_sgr_reverse(screen):
    """Test SGR 7 (reverse)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[7m")
    assert screen.current_style.reverse is True


def test_sgr_hidden(screen):
    """Test SGR 8 (hidden)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[8m")
    assert screen.current_style.hidden is True


def test_sgr_strike(screen):
    """Test SGR 9 (strikethrough)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[9m")
    assert screen.current_style.strike is True


def test_sgr_foreground_color_ansi(screen):
    """Test SGR 30-37 (ANSI foreground colors)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[31m")  # Red foreground
    assert screen.current_style.color == "ansi_1"


def test_sgr_background_color_ansi(screen):
    """Test SGR 40-47 (ANSI background colors)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[42m")  # Green background
    assert screen.current_style.bgcolor == "ansi_2"


def test_sgr_foreground_color_256(screen):
    """Test SGR 38;5;N (256-color foreground)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[38;5;201m")  # Orchid foreground
    assert screen.current_style.color == "ansi_201"


def test_sgr_background_color_256(screen):
    """Test SGR 48;5;N (256-color background)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[48;5;123m")  # Light blue background
    assert screen.current_style.bgcolor == "ansi_123"


def test_sgr_foreground_color_rgb(screen):
    """Test SGR 38;2;R;G;B (Truecolor foreground)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[38;2;255;0;0m")  # Red foreground
    assert screen.current_style.color == "#ff0000"


def test_sgr_background_color_rgb(screen):
    """Test SGR 48;2;R;G;B (Truecolor background)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[48;2;0;255;0m")  # Green background
    assert screen.current_style.bgcolor == "#00ff00"


def test_sgr_reset_foreground(screen):
    """Test SGR 39 (reset foreground color)."""
    parser = Parser(screen)
    screen.current_style = Style(color="red")
    parser.feed(b"\x1b[39m")
    assert screen.current_style.color is None


def test_sgr_reset_background(screen):
    """Test SGR 49 (reset background color)."""
    parser = Parser(screen)
    screen.current_style = Style(bgcolor="blue")
    parser.feed(b"\x1b[49m")
    assert screen.current_style.bgcolor is None


def test_sgr_multiple_params(screen):
    """Test SGR with multiple parameters in one sequence."""
    parser = Parser(screen)
    parser.feed(b"\x1b[1;4;32;44m")  # Bold, Underline, Green FG, Blue BG
    assert screen.current_style.bold is True
    assert screen.current_style.underline is True
    assert screen.current_style.color == "ansi_2"
    assert screen.current_style.bgcolor == "ansi_4"


def test_sgr_bright_foreground_color_ansi(screen):
    """Test SGR 90-97 (Bright ANSI foreground colors)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[91m")  # Bright Red foreground
    assert screen.current_style.color == "ansi_9"


def test_sgr_bright_background_color_ansi(screen):
    """Test SGR 100-107 (Bright ANSI background colors)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[103m")  # Bright Yellow background
    assert screen.current_style.bgcolor == "ansi_11"


def test_sgr_disable_bold(screen):
    """Test SGR 22 (disable bold/dim)."""
    parser = Parser(screen)
    screen.current_style = Style(bold=True, dim=True)
    parser.feed(b"\x1b[22m")
    assert screen.current_style.bold is False
    assert screen.current_style.dim is False


def test_sgr_disable_italic(screen):
    """Test SGR 23 (disable italic)."""
    parser = Parser(screen)
    screen.current_style = Style(italic=True)
    parser.feed(b"\x1b[23m")
    assert screen.current_style.italic is False


def test_sgr_disable_underline(screen):
    """Test SGR 24 (disable underline)."""
    parser = Parser(screen)
    screen.current_style = Style(underline=True)
    parser.feed(b"\x1b[24m")
    assert screen.current_style.underline is False


def test_sgr_disable_blink(screen):
    """Test SGR 25 (disable blink)."""
    parser = Parser(screen)
    screen.current_style = Style(blink=True)
    parser.feed(b"\x1b[25m")
    assert screen.current_style.blink is False


def test_sgr_disable_reverse(screen):
    """Test SGR 27 (disable reverse)."""
    parser = Parser(screen)
    screen.current_style = Style(reverse=True)
    parser.feed(b"\x1b[27m")
    assert screen.current_style.reverse is False


def test_sgr_disable_hidden(screen):
    """Test SGR 28 (disable hidden)."""
    parser = Parser(screen)
    screen.current_style = Style(hidden=True)
    parser.feed(b"\x1b[28m")
    assert screen.current_style.hidden is False


def test_sgr_disable_strike(screen):
    """Test SGR 29 (disable strikethrough)."""
    parser = Parser(screen)
    screen.current_style = Style(strike=True)
    parser.feed(b"\x1b[29m")
    assert screen.current_style.strike is False


def test_sgr_malformed_256_color(screen):
    """Test SGR 38;5; with missing color code."""
    parser = Parser(screen)
    screen.current_style = Style(color="red")
    parser.feed(b"\x1b[38;5;m")  # Malformed: missing color code
    assert screen.current_style.color == "red"  # Should not change


def test_sgr_malformed_rgb_color(screen):
    """Test SGR 38;2;R;G;B with missing components."""
    parser = Parser(screen)
    screen.current_style = Style(color="red")
    parser.feed(b"\x1b[38;2;255;0;m")  # Malformed: missing blue component
    assert screen.current_style.color == "red"  # Should not change


def test_sgr_empty_params_resets(screen):
    """Test SGR with no parameters (should default to 0)."""
    parser = Parser(screen)
    screen.current_style = Style(bold=True, color="red")
    parser.feed(b"\x1b[m")
    assert screen.current_style == Style()
