"""
Test cases for the terminal Grid data structure.

These tests validate the core functionality of the Grid class, which is the
primary data model for the terminal's screen content. The most complex logic
involves the manipulation of Rich Segments when writing to or clearing the grid,
so the tests focus heavily on these splitting and merging operations.
"""

import pytest
from collections import deque
from rich.segment import Segment
from rich.style import Style

from textual_terminal.grid import Grid

# --- Pytest Fixtures ---


@pytest.fixture
def basic_style() -> Style:
    """A basic, reusable style for tests."""
    return Style(color="white", bgcolor="black")


@pytest.fixture
def red_style() -> Style:
    """A distinct red style for testing merging logic."""
    return Style(color="red")


@pytest.fixture
def empty_grid() -> Grid:
    """Provides a standard 10x3 grid with a history of 5."""
    return Grid(width=10, height=3, history=5)


@pytest.fixture
def populated_grid(empty_grid: Grid, basic_style: Style) -> Grid:
    """Provides a grid with some simple text content."""
    g = empty_grid
    g.lines[0] = [Segment("Line 0", basic_style)]
    g.lines[1] = [Segment("Line 1", basic_style)]
    g.lines[2] = [Segment("Line 2", basic_style)]
    return g


@pytest.fixture
def multi_segment_line_grid(empty_grid: Grid, basic_style: Style, red_style: Style) -> Grid:
    """Provides a grid with a line composed of multiple segments."""
    grid = empty_grid
    grid.lines[1] = [
        Segment("Hello ", basic_style),
        Segment("World", red_style),
        Segment("!", basic_style),
    ]
    return grid


# --- Initialization Tests ---


def test_grid_init_creates_correct_dimensions_and_history(empty_grid: Grid):
    """The grid should be initialized with the correct width, height, and history size."""
    assert empty_grid.width == 10
    assert empty_grid.height == 3
    assert empty_grid.history.maxlen == 5
    assert len(empty_grid.lines) == 3
    assert isinstance(empty_grid.history, deque)


def test_grid_init_creates_empty_lines():
    """Each visible line in a new grid should be an empty list."""
    grid = Grid(width=5, height=2, history=0)
    assert grid.lines == [[], []]


# --- `set_cell` Method Tests (Core Write Logic) ---


def test_set_cell_on_empty_line_creates_new_segment(empty_grid: Grid, basic_style: Style):
    """Writing a character to an empty line should create a single segment."""
    grid = empty_grid
    grid.set_cell(0, 0, "A", basic_style)

    expected = [Segment("A", basic_style)]
    assert grid.lines[0] == expected


def test_set_cell_in_middle_of_segment_splits_correctly(empty_grid: Grid, basic_style: Style):
    """Writing into the middle of a segment should split it into three."""
    grid = empty_grid
    grid.lines[0] = [Segment("Hello", basic_style)]

    # Overwrite the 'l' at index 2 with 'X' in a different style
    new_style = Style(color="red")
    grid.set_cell(2, 0, "X", new_style)

    expected = [
        Segment("He", basic_style),
        Segment("X", new_style),
        Segment("lo", basic_style),
    ]
    assert grid.lines[0] == expected


def test_set_cell_merges_with_adjacent_segment_of_same_style(empty_grid: Grid, red_style: Style):
    """Writing a segment should merge it with neighbors if the style is identical."""
    grid = empty_grid
    grid.lines[0] = [Segment("A", red_style), Segment("C", red_style)]

    # Write 'B' with the same style between 'A' and 'C'
    grid.set_cell(1, 0, "B", red_style)

    # It should result in one single segment, not three.
    expected = [Segment("ABC", red_style)]
    assert grid.lines[0] == expected


def test_set_cell_with_wide_character_handles_width(empty_grid: Grid, basic_style: Style):
    """Writing a wide character should correctly occupy two cells and remove underlying content."""
    grid = empty_grid
    grid.lines[0] = [Segment("AB", basic_style)]

    # Overwrite 'A' with a rocket emoji (width 2)
    grid.set_cell(0, 0, "🚀", basic_style)

    # The 'B' should be gone, overwritten by the wide character.
    expected = [Segment("🚀", basic_style)]
    assert grid.lines[0] == expected
    assert Segment.get_line_length(grid.lines[0]) == 2


def test_set_cell_overwriting_second_half_of_wide_char(empty_grid: Grid, basic_style: Style):
    """Writing over the right-hand side of a wide char should split it."""
    grid = empty_grid
    grid.lines[0] = [Segment("🚀", basic_style)]  # At columns 0 and 1

    grid.set_cell(1, 0, "X", basic_style)

    # The wide char is broken. It should be replaced by a placeholder and the new char.
    expected = [Segment("?X", basic_style)]  # Or similar placeholder logic
    assert grid.lines[0] == expected


# --- `get_cell` Method Tests (Core Read Logic) ---


def test_get_cell_from_simple_line(populated_grid: Grid, basic_style: Style):
    """It should retrieve the correct character and style from a simple line."""
    char, style = populated_grid.get_cell(1, 0)
    assert char == "i"
    assert style == basic_style


def test_get_cell_from_multi_segment_line(multi_segment_line_grid: Grid, red_style: Style):
    """It should retrieve a character from the correct segment in a complex line."""
    char, style = multi_segment_line_grid.get_cell(7, 1)  # The 'r' in "World"
    assert char == "r"
    assert style == red_style


def test_get_cell_from_wide_character_returns_full_character(empty_grid: Grid, basic_style: Style):
    """Querying any column of a wide char should return the char itself."""
    grid = empty_grid
    grid.set_cell(2, 0, "🚀", basic_style)

    # Check the left side of the character
    char1, style1 = grid.get_cell(2, 0)
    assert char1 == "🚀"
    assert style1 == basic_style

    # Check the right side of the character
    char2, style2 = grid.get_cell(3, 0)
    assert char2 == "🚀"
    assert style2 == basic_style


def test_get_cell_out_of_bounds_returns_default_blank_cell(empty_grid: Grid):
    """Querying a coordinate outside the line's content should return a blank default cell."""
    char, style = empty_grid.get_cell(5, 1)
    assert char == " "
    assert style == Style()


# --- `clear_rect` Method Tests ---


def test_clear_rect_clears_a_full_line(populated_grid: Grid, basic_style: Style):
    """Clearing a full line should replace it with a single blank segment."""
    grid = populated_grid
    clear_style = Style(bgcolor="blue")

    grid.clear_rect(0, 1, 10, 1, clear_style)

    expected = [Segment("          ", clear_style)]
    assert grid.lines[1] == expected
    # Other lines should be untouched
    assert grid.lines[0] == [Segment("Line 0", basic_style)]


def test_clear_rect_in_middle_of_line_splits_and_replaces(
    multi_segment_line_grid: Grid, basic_style: Style, red_style: Style
):
    """Clearing a section in the middle of a line should correctly split and insert."""
    grid = multi_segment_line_grid
    clear_style = Style(bgcolor="green")

    # Clear "o Wor" from "Hello World!"
    grid.clear_rect(4, 1, 5, 1, clear_style)

    expected = [
        Segment("Hell", basic_style),
        Segment("     ", clear_style),
        Segment("ld", red_style),
        Segment("!", basic_style),
    ]
    assert grid.lines[1] == expected


# --- `scroll_up` Method Tests ---


def test_scroll_up_moves_top_line_to_history(populated_grid: Grid):
    """Scrolling up should move the top visible line into the history deque."""
    grid = populated_grid
    original_top_line = grid.lines[0]

    grid.scroll_up(Style(bgcolor="blue"))

    assert len(grid.history) == 1
    assert grid.history[0] == original_top_line


def test_scroll_up_adds_blank_line_at_bottom(populated_grid: Grid):
    """After scrolling, a new empty line should be added to the bottom of the visible area."""
    grid = populated_grid
    grid.scroll_up(Style(bgcolor="black"))
    assert grid.lines[-1] == []


def test_scroll_up_respects_history_limit(basic_style: Style):
    """The history deque should not grow beyond its maxlen."""
    grid = Grid(width=10, height=2, history=2)
    grid.lines[0] = [Segment("L0", basic_style)]
    grid.lines[1] = [Segment("L1", basic_style)]

    # Scroll 3 times, which is more than the history limit of 2
    grid.scroll_up(basic_style)  # History: [L0]
    grid.scroll_up(basic_style)  # History: [L0, L1]
    grid.scroll_up(basic_style)  # History: [L1, new_line]

    assert len(grid.history) == 2
    assert grid.history[0] == [Segment("L1", basic_style)]  # L0 should be gone


# --- Resizing Tests ---


def test_resize_height_decrease_pushes_lines_to_history(populated_grid: Grid):
    """Decreasing height should move lines from the top of the view to history."""
    grid = populated_grid
    original_line_0 = grid.lines[0]
    original_line_1 = grid.lines[1]

    grid.resize(width=10, height=1)

    assert grid.height == 1
    assert len(grid.lines) == 1
    assert len(grid.history) == 2
    assert grid.history[0] == original_line_0
    assert grid.history[1] == original_line_1


def test_resize_height_increase_pulls_lines_from_history(populated_grid: Grid, basic_style: Style):
    """Increasing height should pull lines from history to the top of the view."""
    grid = populated_grid
    grid.history.append([Segment("H-1", basic_style)])
    grid.history.append([Segment("H-2", basic_style)])
    original_history_count = len(grid.history)

    grid.resize(width=10, height=5)  # Increase height by 2

    assert grid.height == 5
    assert len(grid.lines) == 5
    assert len(grid.history) == original_history_count - 2
    assert grid.lines[0] == [Segment("H-1", basic_style)]
    assert grid.lines[1] == [Segment("H-2", basic_style)]


def test_resize_width_updates_width_attribute(empty_grid: Grid):
    """Resizing the width should update the internal width attribute."""
    grid = empty_grid
    grid.resize(width=20, height=3)
    assert grid.width == 20
