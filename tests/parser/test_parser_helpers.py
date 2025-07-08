
import pytest
from unittest.mock import Mock
from textual_terminal.parser import Parser
from textual_terminal.screen import Screen
from rich.style import Style

@pytest.fixture
def parser_and_screen():
    screen = Mock(spec=Screen)
    screen.current_style = Mock(spec=Style) # Mock the Style object
    parser = Parser(screen)
    return parser, screen

def test_clear_buffers(parser_and_screen):
    """Test that _clear resets all internal buffers."""
    parser, _ = parser_and_screen
    # Populate buffers to ensure they are cleared
    parser.intermediate_chars = ["?"]
    parser.param_buffer = "1;2"
    parser.parsed_params = [1, 2]
    parser.string_buffer = "test_string"

    parser._clear()

    assert parser.intermediate_chars == []
    assert parser.param_buffer == ""
    assert parser.parsed_params == []
    assert parser.string_buffer == ""

def test_split_params_empty_string(parser_and_screen):
    """Test _split_params with an empty string."""
    parser, _ = parser_and_screen
    parser._split_params("")
    assert parser.parsed_params == []

def test_split_params_single_param(parser_and_screen):
    """Test _split_params with a single parameter."""
    parser, _ = parser_and_screen
    parser._split_params("123")
    assert parser.parsed_params == [123]

def test_split_params_multiple_params(parser_and_screen):
    """Test _split_params with multiple parameters separated by semicolon."""
    parser, _ = parser_and_screen
    parser._split_params("1;2;3")
    assert parser.parsed_params == [1, 2, 3]

def test_split_params_with_sub_params(parser_and_screen):
    """Test _split_params with sub-parameters separated by colon."""
    parser, _ = parser_and_screen
    parser._split_params("38:5:21")
    assert parser.parsed_params == [38]

def test_split_params_with_empty_parts(parser_and_screen):
    """Test _split_params with empty parts (e.g., double semicolons)."""
    parser, _ = parser_and_screen
    parser._split_params("1;;3")
    assert parser.parsed_params == [1, 0, 3]

def test_get_param_valid_index(parser_and_screen):
    """Test _get_param with a valid index."""
    parser, _ = parser_and_screen
    parser.parsed_params = [10, 20, 30]
    assert parser._get_param(1, 0) == 20

def test_get_param_out_of_bounds_index(parser_and_screen):
    """Test _get_param with an out-of-bounds index, expecting default."""
    parser, _ = parser_and_screen
    parser.parsed_params = [10, 20, 30]
    assert parser._get_param(5, 99) == 99

def test_get_param_empty_params(parser_and_screen):
    """Test _get_param when parsed_params is empty."""
    parser, _ = parser_and_screen
    parser.parsed_params = []
    assert parser._get_param(0, 50) == 50

def test_reset_terminal(parser_and_screen):
    """Test that _reset_terminal calls screen methods and resets style."""
    parser, screen = parser_and_screen
    parser._reset_terminal()
    screen.clear_screen.assert_called_once_with(2)
    screen.set_cursor.assert_called_once_with(0, 0)
    assert isinstance(parser.screen.current_style, Style)
