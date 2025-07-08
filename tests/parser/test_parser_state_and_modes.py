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


def test_parse_byte_ht_wraps_cursor(screen):
    """Test that HT character (0x09) wraps cursor_x if it exceeds screen width."""
    parser = Parser(screen)
    screen.cursor_x = screen.width - 5  # 5 characters before end
    parser.feed(b"\x09")
    assert screen.cursor_x == screen.width - 1  # Should cap at screen width - 1


def test_parse_byte_unknown_escape_sequence(screen):
    """Test that an unknown escape sequence returns to GROUND state."""
    parser = Parser(screen)
    parser.feed(b"\x1bX")  # ESC then an unknown char 'X'
    assert parser.current_state == "GROUND"


def test_parse_byte_invalid_csi_entry(screen):
    """Test that an invalid byte in CSI_ENTRY returns to GROUND state."""
    parser = Parser(screen)
    parser.feed(b"\x1b[\x01")  # ESC [ then an invalid byte (STX)
    assert parser.current_state == "GROUND"


def test_parse_byte_invalid_csi_param(screen):
    """Test that an invalid byte in CSI_PARAM returns to GROUND state."""
    parser = Parser(screen)
    parser.feed(b"\x1b[1;\x01")  # ESC [ 1 ; then an invalid byte (STX)
    assert parser.current_state == "GROUND"


def test_parse_byte_invalid_csi_intermediate(screen):
    """Test that an invalid byte in CSI_INTERMEDIATE returns to GROUND state."""
    parser = Parser(screen)
    parser.feed(b"\x1b[?1\x01")  # ESC [ ? 1 then an invalid byte (STX)
    assert parser.current_state == "GROUND"


def test_parse_byte_csi_entry_intermediate_general(screen):
    """Test CSI_ENTRY with general intermediate characters."""
    parser = Parser(screen)
    parser.feed(b"\x1b[!p")  # ESC [ ! p (CSI with intermediate '!')
    assert parser.current_state == "GROUND"
    assert parser.intermediate_chars == ["!"]
    assert parser.parsed_params == []


def test_parse_byte_csi_param_intermediate(screen):
    """Test CSI_PARAM with intermediate characters."""
    parser = Parser(screen)
    parser.feed(b"\x1b[1;!p")  # ESC [ 1 ; ! p
    assert parser.current_state == "GROUND"
    assert parser.parsed_params == [1]
    assert parser.intermediate_chars == ["!"]  # ; is a parameter separator, ! is intermediate


def test_parse_byte_csi_intermediate_param_final(screen):
    """Test CSI_INTERMEDIATE with parameter and final byte."""
    parser = Parser(screen)
    parser.feed(b"\x1b[?1;2@")  # ESC [ ? 1 ; 2 @
    assert parser.current_state == "GROUND"
    assert parser.parsed_params == [1, 2]
    assert parser.intermediate_chars == ["?"]


def test_split_params_value_error_sub_param(screen):
    """Test _split_params with ValueError in sub-parameter parsing."""
    parser = Parser(screen)
    parser._split_params("38:X")  # Malformed sub-parameter
    assert parser.parsed_params == [0]


def test_split_params_value_error_main_param(screen):
    """Test _split_params with ValueError in main parameter parsing."""
    parser = Parser(screen)
    parser._split_params("X")  # Malformed main parameter
    assert parser.parsed_params == [0]


def test_csi_dispatch_sm_rm_basic_modes(screen):
    """Test _csi_dispatch_sm_rm for basic public modes."""
    parser = Parser(screen)

    # Test auto-wrap mode (public mode 7)
    parser.feed(b"\x1b[7h")  # Set auto-wrap
    assert screen.auto_wrap is True
    parser.feed(b"\x1b[7l")  # Reset auto-wrap
    assert screen.auto_wrap is False

    # Test cursor visibility (public mode 25)
    parser.feed(b"\x1b[25l")  # Hide cursor
    assert screen.cursor_visible is False
    parser.feed(b"\x1b[25h")  # Show cursor
    assert screen.cursor_visible is True
