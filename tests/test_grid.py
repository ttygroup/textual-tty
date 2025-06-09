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
    """Writing a wide character should correctly occupy two cells."""
    grid = empty_grid
    grid.lines[0] = [Segment("AB", basic_style)]

    # Overwrite 'A' with a rocket emoji (width 2)
    grid.set_cell(0, 0, "🚀", basic_style)

    # The 'B' should be gone, overwritten by the wide character.
    expected = [Segment("🚀", basic_style)]
    assert grid.lines[0] == expected
    assert Segment.get_line_length(grid.lines[0]) == 2


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
