import pytest
from unittest.mock import Mock
from textual_tty.parser import Parser
from textual_tty.terminal import Terminal
from rich.style import Style
from rich.color import Color


@pytest.fixture
def screen():
    """Return a mock Screen object with necessary attributes."""
    screen = Mock(spec=Terminal)
    screen.current_style = Style()  # Initialize with a real Style object
    screen.width = 80
    screen.height = 24
    screen.cursor_x = 0
    screen.cursor_y = 0
    screen.scroll_top = 0
    screen.scroll_bottom = screen.height - 1
    screen.auto_wrap = True
    screen.cursor_visible = True

    def _set_cursor(x, y):
        if x is not None:
            screen.cursor_x = x
        if y is not None:
            screen.cursor_y = y

    screen.set_cursor.side_effect = _set_cursor
    return screen


def test_sgr_reset_all_attributes(screen):
    """Test SGR 0 (Reset all attributes)."""
    parser = Parser(screen)
    # Set some attributes first
    parser.feed(b"\x1b[1;31;42m")  # Bold, red foreground, green background
    assert screen.current_style.bold is True
    assert screen.current_style.color == Color.from_ansi(1)
    assert screen.current_style.bgcolor == Color.from_ansi(2)

    parser.feed(b"\x1b[0m")  # Reset all attributes
    assert screen.current_style == Style()


def test_sgr_bold_and_not_bold(screen):
    """Test SGR 1 (Bold) and SGR 22 (Not bold)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[1m")
    assert screen.current_style.bold is True
    parser.feed(b"\x1b[22m")
    assert screen.current_style.bold is False


def test_sgr_italic_and_not_italic(screen):
    """Test SGR 3 (Italic) and SGR 23 (Not italic)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[3m")
    assert screen.current_style.italic is True
    parser.feed(b"\x1b[23m")
    assert screen.current_style.italic is False


def test_sgr_underline_and_not_underline(screen):
    """Test SGR 4 (Underline) and SGR 24 (Not underlined)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[4m")
    assert screen.current_style.underline is True
    parser.feed(b"\x1b[24m")
    assert screen.current_style.underline is False


def test_sgr_blink_and_not_blink(screen):
    """Test SGR 5 (Blink) and SGR 25 (Not blinking)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[5m")
    assert screen.current_style.blink is True
    parser.feed(b"\x1b[25m")
    assert screen.current_style.blink is False


def test_sgr_reverse_and_not_reverse(screen):
    """Test SGR 7 (Reverse) and SGR 27 (Not reversed)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[7m")
    assert screen.current_style.reverse is True
    parser.feed(b"\x1b[27m")
    assert screen.current_style.reverse is False


def test_sgr_conceal_and_not_conceal(screen):
    """Test SGR 8 (Conceal) and SGR 28 (Not concealed)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[8m")
    assert screen.current_style.conceal is True
    parser.feed(b"\x1b[28m")
    assert screen.current_style.conceal is False


def test_sgr_strikethrough_and_not_strikethrough(screen):
    """Test SGR 9 (Strikethrough) and SGR 29 (Not strikethrough)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[9m")
    assert screen.current_style.strike is True
    parser.feed(b"\x1b[29m")
    assert screen.current_style.strike is False


def test_sgr_16_color_foreground(screen):
    """Test SGR 30-37 (16-color foreground)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[31m")  # Red foreground
    assert screen.current_style.color == Color.from_ansi(1)


def test_sgr_16_color_background(screen):
    """Test SGR 40-47 (16-color background)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[44m")  # Blue background
    assert screen.current_style.bgcolor == Color.from_ansi(4)


def test_sgr_bright_16_color_foreground(screen):
    """Test SGR 90-97 (Bright 16-color foreground)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[91m")  # Bright Red foreground
    assert screen.current_style.color == Color.from_ansi(9)


def test_sgr_bright_16_color_background(screen):
    """Test SGR 100-107 (Bright 16-color background)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[104m")  # Bright Blue background
    assert screen.current_style.bgcolor == Color.from_ansi(12)


def test_sgr_256_color_foreground(screen):
    """Test SGR 38;5;N (256-color foreground)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[38;5;123m")
    assert screen.current_style.color == Color.from_ansi(123)


def test_sgr_256_color_background(screen):
    """Test SGR 48;5;N (256-color background)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[48;5;200m")
    assert screen.current_style.bgcolor == Color.from_ansi(200)


def test_sgr_truecolor_foreground(screen):
    """Test SGR 38;2;R;G;B (Truecolor foreground)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[38;2;10;20;30m")
    assert screen.current_style.color == Color.from_rgb(10, 20, 30)


def test_sgr_truecolor_background(screen):
    """Test SGR 48;2;R;G;B (Truecolor background)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[48;2;100;150;200m")
    assert screen.current_style.bgcolor == Color.from_rgb(100, 150, 200)


def test_sgr_default_foreground_color(screen):
    """Test SGR 39 (Default foreground color)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[31m")  # Set to red
    assert screen.current_style.color == Color.from_ansi(1)
    parser.feed(b"\x1b[39m")  # Reset to default
    assert screen.current_style.color == Color.default()


def test_sgr_default_background_color(screen):
    """Test SGR 49 (Default background color)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[44m")  # Set to blue
    assert screen.current_style.bgcolor == Color.from_ansi(4)
    parser.feed(b"\x1b[49m")  # Reset to default
    assert screen.current_style.bgcolor == Color.default()


def test_sgr_malformed_rgb_foreground(screen):
    """Test SGR with malformed RGB foreground sequence (missing values)."""
    parser = Parser(screen)
    # Malformed sequence: 38;2;r;g;b but missing g and b
    parser.feed(b"\x1b[38;2;100m")
    # Should not raise an error and current_style should not change to an invalid color
    assert screen.current_style.color is None


def test_sgr_malformed_rgb_background(screen):
    """Test SGR with malformed RGB background sequence (missing values)."""
    parser = Parser(screen)
    # Malformed sequence: 48;2;r;g;b but missing g and b
    parser.feed(b"\x1b[48;2;100m")
    # Should not raise an error and current_style should not change to an invalid color
    assert screen.current_style.bgcolor is None
