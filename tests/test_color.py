"""
Test cases for the terminal color handling module.
"""

import pytest
from textual.color import Color
from rich.color import Color as RichColor
from textual_terminal import color as color_module

# --- Tests for parse_color() ---


def test_parse_color_handles_standard_css_name():
    """`parse_color` should correctly parse a standard web color name."""
    expected = Color.parse("red")
    actual = color_module.parse_color("red")
    assert actual == expected


def test_parse_color_handles_hex_code():
    """`parse_color` should correctly parse a standard hexadecimal color code."""
    expected = Color.parse("#00ff00")
    actual = color_module.parse_color("#00ff00")
    assert actual == expected


def test_parse_color_handles_8bit_color_string():
    """`parse_color` should correctly parse a 'color(n)' string."""
    expected = Color.from_rich_color(RichColor.from_ansi(21))
    actual = color_module.parse_color("color(21)")
    assert actual == expected, "Should handle 8-bit color strings"


def test_parse_color_handles_specific_x11_name():
    """`parse_color` should fall back to the custom X11 name dictionary."""
    # This color is in our custom X11_NAMES list but not a standard CSS name.
    expected = Color.parse("#00bfff")  # DeepSkyBlue1
    actual = color_module.parse_color("deepskyblue1")
    assert actual == expected


def test_parse_color_is_case_insensitive_for_x11_names():
    """`parse_color` should handle case variations in X11 names."""
    expected = Color.parse("#00bfff")  # DeepSkyBlue1
    actual = color_module.parse_color("DeepSkyBlue1")
    assert actual == expected


def test_parse_color_handles_x11_names_with_spaces():
    """`parse_color` should correctly handle X11 names containing spaces."""
    expected = Color.parse("#00bfff")
    actual = color_module.parse_color("deep sky blue")
    assert actual == expected


def test_parse_color_raises_valueerror_for_invalid_name():
    """`parse_color` should raise ValueError for an unknown color name."""
    with pytest.raises(ValueError, match="Unknown color"):
        color_module.parse_color("not a real color")


# --- Tests for Palette Management ---


def test_palette_init_creates_correctly_sized_empty_list():
    """`palette_init` should return a list of 256 None values."""
    expected_size = 256
    expected_content = [None] * 256

    actual = color_module.palette_init()

    assert len(actual) == expected_size
    assert actual == expected_content


def test_palette_set_stores_rgb_tuple_at_index():
    """`palette_set` should correctly place an RGB tuple at a given index."""
    palette = color_module.palette_init()
    test_color = (255, 165, 0)  # Orange
    test_index = 21

    color_module.palette_set(palette, test_index, test_color)

    assert palette[test_index] == test_color


def test_palette_get_retrieves_set_color():
    """`palette_get` should retrieve a color that was previously set."""
    palette = color_module.palette_init()
    expected = (138, 43, 226)  # BlueViolet
    index = 100

    color_module.palette_set(palette, index, expected)
    actual = color_module.palette_get(palette, index)

    assert actual == expected


def test_palette_get_returns_none_for_unset_color():
    """`palette_get` should return None for a palette index that hasn't been set."""
    palette = color_module.palette_init()
    actual = color_module.palette_get(palette, 50)
    assert actual is None


def test_palette_clear_resets_all_entries_to_none():
    """`palette_clear` should change all set entries back to None."""
    palette = color_module.palette_init()
    color_module.palette_set(palette, 10, (255, 0, 0))
    color_module.palette_set(palette, 20, (0, 255, 0))
    color_module.palette_set(palette, 30, (0, 0, 255))
    expected = [None] * 256

    color_module.palette_clear(palette)

    assert palette == expected
