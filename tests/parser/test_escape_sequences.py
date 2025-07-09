import pytest
from unittest.mock import Mock
from textual_tty.parser import Parser
from textual_tty.terminal import Terminal


@pytest.fixture
def screen():
    """Return a mock Screen object."""
    screen = Mock(spec=Terminal)
    screen.current_style = Mock()  # Mock the Style object
    screen.width = 80  # Set a default width for tab tests
    screen.height = 24  # Set a default height for scroll tests
    screen.scroll_top = 0  # Set default scroll region top
    screen.scroll_bottom = screen.height - 1  # Set default scroll region bottom
    return screen


def test_bell_character(screen):
    """Test that the BEL character (0x07) is handled (does nothing visible)."""
    parser = Parser(screen)
    parser.feed("\x07")
    # BEL typically just makes a sound, no screen changes, so no screen methods should be called.
    screen.write_text.assert_not_called()
    screen.backspace.assert_not_called()
    screen.line_feed.assert_not_called()
    screen.carriage_return.assert_not_called()


def test_escape_to_csi_entry(screen):
    """Test transition from ESCAPE to CSI_ENTRY state."""
    parser = Parser(screen)
    parser.feed("\x1b[")  # ESC then [
    assert parser.current_state == "CSI_ENTRY"


def test_ris_reset_terminal(screen):
    """Test RIS (Reset to Initial State) sequence."""
    parser = Parser(screen)
    parser.feed("\x1bc")  # ESC then c
    screen.clear_screen.assert_called_once_with(2)
    screen.set_cursor.assert_called_once_with(0, 0)
    assert parser.current_state == "GROUND"


def test_ind_index(screen):
    """Test IND (Index) sequence."""
    parser = Parser(screen)
    parser.feed("\x1bD")  # ESC then D
    screen.line_feed.assert_called_once()
    assert parser.current_state == "GROUND"


def test_ri_reverse_index_no_scroll(screen):
    """Test RI (Reverse Index) sequence without scrolling."""
    parser = Parser(screen)
    screen.cursor_y = 5
    screen.scroll_top = 0
    parser.feed("\x1bM")  # ESC then M
    assert screen.cursor_y == 4
    screen.scroll_down.assert_not_called()
    assert parser.current_state == "GROUND"


def test_ri_reverse_index_with_scroll(screen):
    """Test RI (Reverse Index) sequence with scrolling."""
    parser = Parser(screen)
    screen.cursor_y = 0  # At the top of the scroll region
    screen.scroll_top = 0
    parser.feed("\x1bM")  # ESC then M
    screen.scroll_down.assert_called_once_with(1)
    assert parser.current_state == "GROUND"


def test_desc_save_cursor(screen):
    """Test DECSC (Save Cursor) sequence."""
    parser = Parser(screen)
    parser.feed("\x1b7")  # ESC then 7
    screen.save_cursor.assert_called_once()
    assert parser.current_state == "GROUND"


def test_decrc_restore_cursor(screen):
    """Test DECRC (Restore Cursor) sequence."""
    parser = Parser(screen)
    parser.feed("\x1b8")  # ESC then 8
    screen.restore_cursor.assert_called_once()
    assert parser.current_state == "GROUND"
