"""
Rich Text Caching: LRU cached conversion from ANSI strings to Rich Text objects.

This module provides cached conversion functions to avoid expensive
Rich Text parsing operations for unchanged terminal lines.
"""

from __future__ import annotations
from functools import lru_cache
from rich.text import Text


@lru_cache(maxsize=2048)  # Cache up to 2048 unique line representations
def ansi_to_rich(ansi_string: str) -> Text:
    """Convert ANSI string to Rich Text object (cached).

    Args:
        ansi_string: ANSI escape sequence string from terminal

    Returns:
        Rich Text object with all formatting applied
    """
    return Text.from_ansi(ansi_string)


def get_cache_info() -> dict:
    """Get cache statistics for monitoring performance."""
    info = ansi_to_rich.cache_info()
    return {
        "hits": info.hits,
        "misses": info.misses,
        "maxsize": info.maxsize,
        "currsize": info.currsize,
        "hit_rate": info.hits / (info.hits + info.misses) if (info.hits + info.misses) > 0 else 0.0,
    }


def clear_cache() -> None:
    """Clear the Rich Text cache."""
    ansi_to_rich.cache_clear()
