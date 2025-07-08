import pytest
from unittest.mock import Mock
from textual_terminal.parser import Parser
from textual_terminal.screen import TerminalScreen
from rich.style import Style


@pytest.fixture
def screen():
    """Return a mock Screen object with necessary attributes."""
    screen = Mock(spec=TerminalScreen)
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


def test_csi_sgr_malformed_rgb_foreground(screen):
    """Test SGR with malformed RGB foreground sequence (missing values)."""
    parser = Parser(screen)
    # Malformed sequence: 38;2;r;g;b but missing g and b
    parser.feed(b"\x1b[38;2;100m")
    # Should not raise an error and current_style should not change to an invalid color
    assert screen.current_style.color is None


def test_csi_sgr_malformed_rgb_background(screen):
    """Test SGR with malformed RGB background sequence (missing values)."""
    parser = Parser(screen)
    # Malformed sequence: 48;2;r;g;b but missing g and b
    parser.feed(b"\x1b[48;2;100m")
    # Should not raise an error and current_style should not change to an invalid color
    assert screen.current_style.bgcolor is None


def test_csi_sm_rm_private_autowrap(screen):
    """Test CSI ? 7 h (Set Auto-wrap Mode) and CSI ? 7 l (Reset Auto-wrap Mode)."""
    parser = Parser(screen)

    # Set auto-wrap mode
    parser.feed(b"\x1b[?7h")
    assert screen.auto_wrap is True

    # Reset auto-wrap mode
    parser.feed(b"\x1b[?7l")
    assert screen.auto_wrap is False


def test_csi_sm_rm_private_cursor_visibility(screen):
    """Test CSI ? 25 h (Show Cursor) and CSI ? 25 l (Hide Cursor)."""
    parser = Parser(screen)

    # Hide cursor
    parser.feed(b"\x1b[?25l")
    assert screen.cursor_visible is False

    # Show cursor
    parser.feed(b"\x1b[?25h")
    assert screen.cursor_visible is True


def test_parse_byte_csi_intermediate_transition(screen):
    """Test _parse_byte transitions with intermediate characters."""
    parser = Parser(screen)
    parser.feed(b"\x1b[?1h")  # ESC [ ? 1 h (CSI with intermediate '?')
    assert parser.current_state == "GROUND"
    assert parser.parsed_params == [1]
    assert parser.intermediate_chars == ["?"]

    parser.reset()
    parser.feed(b"\x1b[>1c")  # ESC [ > 1 c (CSI with intermediate '>')
    assert parser.current_state == "GROUND"
    assert parser.parsed_params == [1]
    assert parser.intermediate_chars == [">"]


def test_parser_reset_method(screen):
    """Test the reset method of the parser."""
    parser = Parser(screen)
    # Change some state
    parser.current_state = "ESCAPE"
    parser.intermediate_chars.append("?")
    parser.param_buffer = "123"
    parser.parsed_params.append(123)
    parser.string_buffer = "test"

    parser.reset()

    assert parser.current_state == "GROUND"
    assert not parser.intermediate_chars
    assert not parser.param_buffer
    assert not parser.parsed_params
    assert not parser.string_buffer
