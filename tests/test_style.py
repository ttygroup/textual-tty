"""Tests for ANSI style merging functionality."""

from textual_tty.style import (
    merge_ansi_styles,
    get_background,
    extract_fg_color,
    extract_bg_color,
    has_pattern,
    BOLD_PATTERNS,
    FG_RED_PATTERNS,
)


def test_merge_empty_styles():
    """Test merging with empty styles."""
    assert merge_ansi_styles("", "") == ""
    assert merge_ansi_styles("", "\033[31m") == "\033[31m"
    assert merge_ansi_styles("\033[31m", "") == "\033[31m"


def test_merge_reset_overrides_all():
    """Test that reset (SGR 0) overrides everything."""
    assert merge_ansi_styles("\033[31;1m", "\033[0m") == "\033[0m"
    assert merge_ansi_styles("\033[31;1m", "\033[m") == "\033[m"


def test_merge_simple_attributes():
    """Test merging simple text attributes."""
    # Bold + red = red bold (colors come first)
    assert merge_ansi_styles("\033[1m", "\033[31m") == "\033[31;1m"

    # Red + bold = red bold
    assert merge_ansi_styles("\033[31m", "\033[1m") == "\033[31;1m"

    # Multiple attributes
    assert merge_ansi_styles("\033[31;1m", "\033[4m") == "\033[31;1;4m"


def test_merge_color_override():
    """Test that new colors override old colors."""
    # Red + green = green (foreground override)
    assert merge_ansi_styles("\033[31m", "\033[32m") == "\033[32m"

    # Red bg + blue bg = blue bg (background override)
    assert merge_ansi_styles("\033[41m", "\033[44m") == "\033[44m"

    # Red fg + blue bg = red fg, blue bg
    assert merge_ansi_styles("\033[31m", "\033[44m") == "\033[31;44m"


def test_merge_attribute_removal():
    """Test removing attributes with NOT codes."""
    # Bold + not bold = no bold
    assert merge_ansi_styles("\033[1m", "\033[22m") == "\033[22m"

    # Bold + red + not bold = red only
    assert merge_ansi_styles("\033[1;31m", "\033[22m") == "\033[31;22m"


def test_extract_fg_color():
    """Test extracting foreground color."""
    assert extract_fg_color("\033[31m") == "31"
    assert extract_fg_color("\033[1;31m") == "31"
    assert extract_fg_color("\033[31;1m") == "31"
    assert extract_fg_color("\033[91m") == "91"  # Bright red
    assert extract_fg_color("\033[1m") == ""  # No color


def test_extract_bg_color():
    """Test extracting background color."""
    assert extract_bg_color("\033[41m") == "41"
    assert extract_bg_color("\033[1;41m") == "41"
    assert extract_bg_color("\033[41;1m") == "41"
    assert extract_bg_color("\033[101m") == "101"  # Bright red bg
    assert extract_bg_color("\033[1m") == ""  # No color


def test_get_background():
    """Test getting just the background color."""
    assert get_background("\033[41m") == "\033[41m"
    assert get_background("\033[31;41m") == "\033[41m"
    assert get_background("\033[1;31;41m") == "\033[41m"
    assert get_background("\033[31m") == ""  # No background
    assert get_background("") == ""


def test_has_pattern():
    """Test pattern detection."""
    assert has_pattern("\033[1m", BOLD_PATTERNS) is True
    assert has_pattern("\033[1;31m", BOLD_PATTERNS) is True
    assert has_pattern("\033[31;1m", BOLD_PATTERNS) is True
    assert has_pattern("\033[31m", BOLD_PATTERNS) is False

    assert has_pattern("\033[31m", FG_RED_PATTERNS) is True
    assert has_pattern("\033[1;31;44m", FG_RED_PATTERNS) is True
    assert has_pattern("\033[32m", FG_RED_PATTERNS) is False


def test_complex_merge_scenarios():
    """Test complex real-world merge scenarios."""
    # Terminal sets red text
    style1 = merge_ansi_styles("", "\033[31m")
    assert style1 == "\033[31m"

    # Then sets bold
    style2 = merge_ansi_styles(style1, "\033[1m")
    assert style2 == "\033[31;1m"

    # Then sets blue background
    style3 = merge_ansi_styles(style2, "\033[44m")
    assert style3 == "\033[31;44;1m"

    # Then changes to green text (overrides red)
    style4 = merge_ansi_styles(style3, "\033[32m")
    assert style4 == "\033[32;44;1m"

    # Then resets everything
    style5 = merge_ansi_styles(style4, "\033[0m")
    assert style5 == "\033[0m"


def test_cache_effectiveness():
    """Test that caching works (same inputs return same object)."""
    # These should hit the cache
    result1 = merge_ansi_styles("\033[31m", "\033[1m")
    result2 = merge_ansi_styles("\033[31m", "\033[1m")
    assert result1 is result2  # Same object from cache

    bg1 = get_background("\033[31;41m")
    bg2 = get_background("\033[31;41m")
    assert bg1 is bg2  # Same object from cache
