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
        call("H", screen.current_style),
        call("e", screen.current_style),
        call("l", screen.current_style),
        call("l", screen.current_style),
        call("o", screen.current_style),
        call(",", screen.current_style),
        call(" ", screen.current_style),
        call("W", screen.current_style),
        call("o", screen.current_style),
        call("r", screen.current_style),
        call("l", screen.current_style),
        call("d", screen.current_style),
        call("!", screen.current_style),
    ]
    screen.write_text.assert_has_calls(calls)


def test_empty_feed(screen):
    """Test that feeding empty bytes doesn't break the parser."""
    parser = Parser(screen)
    parser.feed("")
    screen.write_text.assert_not_called()
