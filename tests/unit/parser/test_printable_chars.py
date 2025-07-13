import pytest
from unittest.mock import Mock, call
from textual_tty.parser import Parser
from textual_tty.terminal import Terminal


@pytest.fixture
def screen():
    """Return a mock Screen object."""
    screen = Mock(spec=Terminal)
    screen.current_style = Mock()
    return screen


def test_printable_characters(screen):
    """Test that printable characters are written to the screen."""
    parser = Parser(screen)
    parser.feed("Hello, World!")

    calls = [
        call("H", ""),
        call("e", ""),
        call("l", ""),
        call("l", ""),
        call("o", ""),
        call(",", ""),
        call(" ", ""),
        call("W", ""),
        call("o", ""),
        call("r", ""),
        call("l", ""),
        call("d", ""),
        call("!"),
    ]
    screen.write_text.assert_has_calls(calls)


def test_empty_feed(screen):
    """Test that feeding empty bytes doesn't break the parser."""
    parser = Parser(screen)
    parser.feed("")
    screen.write_text.assert_not_called()
