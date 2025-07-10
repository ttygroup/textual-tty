import pytest
from unittest.mock import Mock
from textual_tty.parser import Parser
from textual_tty.terminal import Terminal
from rich.style import Style
from textual_tty.constants import (
    DEFAULT_TERMINAL_WIDTH,
    DEFAULT_TERMINAL_HEIGHT,
    ALT_SCREEN_BUFFER,
    ESC,
)


@pytest.fixture
def screen():
    """Return a mock Screen object with necessary attributes."""
    screen = Mock(spec=Terminal)
    screen.current_style = Style()  # Initialize with a real Style object
    screen.width = DEFAULT_TERMINAL_WIDTH
    screen.height = DEFAULT_TERMINAL_HEIGHT
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


def test_alternate_buffer_enable(screen):
    """Test CSI ? 1049 h (Enable alternate screen buffer)."""
    parser = Parser(screen)
    parser.feed(f"{ESC}[?{ALT_SCREEN_BUFFER}h")

    # Should call alternate_screen_on
    screen.alternate_screen_on.assert_called_once()


def test_alternate_buffer_disable(screen):
    """Test CSI ? 1049 l (Disable alternate screen buffer)."""
    parser = Parser(screen)
    parser.feed("\x1b[?1049l")

    # Should call alternate_screen_off
    screen.alternate_screen_off.assert_called_once()


def test_alternate_buffer_enable_disable_sequence(screen):
    """Test enabling then disabling alternate buffer."""
    parser = Parser(screen)

    # Enable
    parser.feed("\x1b[?1049h")
    screen.alternate_screen_on.assert_called_once()

    # Disable
    parser.feed("\x1b[?1049l")
    screen.alternate_screen_off.assert_called_once()


def test_alternate_buffer_with_other_modes(screen):
    """Test alternate buffer mode combined with other modes."""
    parser = Parser(screen)

    # Multiple modes at once: cursor visibility + alternate buffer
    parser.feed("\x1b[?25;1049h")

    # Both should be called
    assert screen.cursor_visible is True
    screen.alternate_screen_on.assert_called_once()


def test_alternate_buffer_mixed_set_reset(screen):
    """Test mixed set/reset operations on alternate buffer and other modes."""
    parser = Parser(screen)

    # Enable cursor + alternate buffer
    parser.feed("\x1b[?25;1049h")
    assert screen.cursor_visible is True
    screen.alternate_screen_on.assert_called_once()

    # Disable cursor, keep alternate buffer enabled
    parser.feed("\x1b[?25l")
    assert screen.cursor_visible is False

    # Disable alternate buffer
    parser.feed("\x1b[?1049l")
    screen.alternate_screen_off.assert_called_once()
