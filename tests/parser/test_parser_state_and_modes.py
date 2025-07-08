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
