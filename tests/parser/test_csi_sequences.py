import pytest
from unittest.mock import Mock
from textual_terminal.parser import Parser
from textual_terminal.screen import Screen


@pytest.fixture
def screen():
    """Return a mock Screen object with necessary attributes."""
    screen = Mock(spec=Screen)
    screen.current_style = Mock()  # Mock the Style object
    screen.width = 80
    screen.height = 24
    screen.cursor_x = 0
    screen.cursor_y = 0
    screen.scroll_top = 0
    screen.scroll_bottom = screen.height - 1

    def _set_cursor(x, y):
        if x is not None:
            screen.cursor_x = x
        if y is not None:
            screen.cursor_y = y

    screen.set_cursor.side_effect = _set_cursor
    return screen


def test_csi_cup_cursor_position(screen):
    """Test CSI H (CUP - Cursor Position) with parameters."""
    parser = Parser(screen)
    parser.feed(b"\x1b[10;20H")  # ESC[10;20H -> move to row 10, col 20
    screen.set_cursor.assert_called_once_with(19, 9)  # 0-based


def test_csi_cup_cursor_position_no_params(screen):
    """Test CSI H (CUP) with no parameters (defaults to 1;1)."""
    parser = Parser(screen)
    parser.feed(b"\x1b[H")  # ESC[H -> move to row 1, col 1
    screen.set_cursor.assert_called_once_with(0, 0)  # 0-based


def test_csi_cuu_cursor_up(screen):
    """Test CSI A (CUU - Cursor Up) with parameter."""
    parser = Parser(screen)
    screen.cursor_y = 10
    parser.feed(b"\x1b[5A")  # ESC[5A -> move up 5 rows
    assert screen.cursor_y == 5


def test_csi_cuu_cursor_up_no_param(screen):
    """Test CSI A (CUU) with no parameter (defaults to 1)."""
    parser = Parser(screen)
    screen.cursor_y = 10
    parser.feed(b"\x1b[A")  # ESC[A -> move up 1 row
    assert screen.cursor_y == 9


def test_csi_cud_cursor_down(screen):
    """Test CSI B (CUD - Cursor Down) with parameter."""
    parser = Parser(screen)
    screen.cursor_y = 10
    parser.feed(b"\x1b[5B")  # ESC[5B -> move down 5 rows
    assert screen.cursor_y == 15


def test_csi_cuf_cursor_forward(screen):
    """Test CSI C (CUF - Cursor Forward) with parameter."""
    parser = Parser(screen)
    screen.cursor_x = 10
    parser.feed(b"\x1b[5C")  # ESC[5C -> move forward 5 columns
    assert screen.cursor_x == 15


def test_csi_cub_cursor_backward(screen):
    """Test CSI D (CUB - Cursor Backward) with parameter."""
    parser = Parser(screen)
    screen.cursor_x = 10
    parser.feed(b"\x1b[5D")  # ESC[5D -> move backward 5 columns
    assert screen.cursor_x == 5


def test_csi_ed_erase_in_display(screen):
    """Test CSI J (ED - Erase in Display) with parameter."""
    parser = Parser(screen)
    parser.feed(b"\x1b[2J")  # ESC[2J -> clear entire screen
    screen.clear_screen.assert_called_once_with(2)


def test_csi_el_erase_in_line(screen):
    """Test CSI K (EL - Erase in Line) with parameter."""
    parser = Parser(screen)
    parser.feed(b"\x1b[1K")  # ESC[1K -> clear from beginning of line to cursor
    screen.clear_line.assert_called_once_with(1)


def test_csi_ich_insert_characters(screen):
    """Test CSI @ (ICH - Insert Characters) with parameter."""
    parser = Parser(screen)
    parser.feed(b"\x1b[5@")  # ESC[5@ -> insert 5 characters
    screen.insert_characters.assert_called_once_with(5)


def test_csi_dch_delete_characters(screen):
    """Test CSI P (DCH - Delete Characters) with parameter."""
    parser = Parser(screen)
    parser.feed(b"\x1b[3P")  # ESC[3P -> delete 3 characters
    screen.delete_characters.assert_called_once_with(3)


def test_csi_il_insert_lines(screen):
    """Test CSI L (IL - Insert Lines) with parameter."""
    parser = Parser(screen)
    parser.feed(b"\x1b[2L")  # ESC[2L -> insert 2 lines
    screen.insert_lines.assert_called_once_with(2)


def test_csi_dl_delete_lines(screen):
    """Test CSI M (DL - Delete Lines) with parameter."""
    parser = Parser(screen)
    parser.feed(b"\x1b[4M")  # ESC[4M -> delete 4 lines
    screen.delete_lines.assert_called_once_with(4)


def test_csi_su_scroll_up(screen):
    """Test CSI S (SU - Scroll Up) with parameter."""
    parser = Parser(screen)
    parser.feed(b"\x1b[3S")  # ESC[3S -> scroll up 3 lines
    screen.scroll_up.assert_called_once_with(3)


def test_csi_sd_scroll_down(screen):
    """Test CSI T (SD - Scroll Down) with parameter."""
    parser = Parser(screen)
    parser.feed(b"\x1b[2T")  # ESC[2T -> scroll down 2 lines
    screen.scroll_down.assert_called_once_with(2)


def test_csi_decstbm_set_scroll_region(screen):
    """Test CSI r (DECSTBM - Set Top and Bottom Margins) with parameters."""
    parser = Parser(screen)
    parser.feed(b"\x1b[5;15r")  # ESC[5;15r -> set scroll region from row 5 to 15
    screen.set_scroll_region.assert_called_once_with(4, 14)  # 0-based


def test_csi_cha_cursor_horizontal_absolute(screen):
    """Test CSI G (CHA - Cursor Horizontal Absolute) with parameter."""
    parser = Parser(screen)
    parser.feed(b"\x1b[10G")  # ESC[10G -> move cursor to column 10
    assert screen.cursor_x == 9  # 0-based


def test_csi_vpa_vertical_position_absolute(screen):
    """Test CSI d (VPA - Vertical Position Absolute) with parameter."""
    parser = Parser(screen)
    parser.feed(b"\x1b[5d")  # ESC[5d -> move cursor to row 5
    assert screen.cursor_y == 4  # 0-based
