"""
Rich Text Caching: LRU cached conversion from tuple to Rich Text objects.

This module provides cached conversion functions to avoid expensive
Rich Text parsing operations for unchanged terminal lines.
"""

from __future__ import annotations
from functools import lru_cache
from typing import Tuple
from rich.text import Text


@lru_cache(maxsize=2048)  # Cache up to 2048 unique line representations
def tuple_to_rich(line_tuple: Tuple) -> Text:
    """Convert line tuple to Rich Text object (cached).

    Args:
        line_tuple: Tuple containing sequence like:
                   ("ansi", ansi_code, "char", char, "cursor", cursor_code, ...)

    Returns:
        Rich Text object with all formatting applied
    """
    if not line_tuple:
        return Text("")

    # Build ANSI string from tuple parts
    ansi_parts = []
    i = 0

    while i < len(line_tuple):
        part_type = line_tuple[i]

        if part_type == "ansi":
            # ANSI escape sequence
            ansi_parts.append(line_tuple[i + 1])
            i += 2
        elif part_type == "char":
            # Character
            ansi_parts.append(line_tuple[i + 1])
            i += 2
        elif part_type == "cursor":
            # Cursor escape sequence
            ansi_parts.append(line_tuple[i + 1])
            i += 2
        elif part_type == "cursor_end":
            # Cursor end sequence
            ansi_parts.append(line_tuple[i + 1])
            i += 2
        elif part_type == "reset":
            # Reset sequence
            ansi_parts.append(line_tuple[i + 1])
            i += 2
        elif part_type == "pad":
            # Padding spaces
            ansi_parts.append(line_tuple[i + 1])
            i += 2
        elif part_type == "final_reset":
            # Final reset sequence
            ansi_parts.append(line_tuple[i + 1])
            i += 2
        else:
            # Unknown part type, skip
            i += 1

    # Convert ANSI string to Rich Text
    ansi_string = "".join(ansi_parts)
    return Text.from_ansi(ansi_string)


def get_cache_info() -> dict:
    """Get cache statistics for monitoring performance."""
    info = tuple_to_rich.cache_info()
    return {
        "hits": info.hits,
        "misses": info.misses,
        "maxsize": info.maxsize,
        "currsize": info.currsize,
        "hit_rate": info.hits / (info.hits + info.misses) if (info.hits + info.misses) > 0 else 0.0,
    }


def clear_cache() -> None:
    """Clear the Rich Text cache."""
    tuple_to_rich.cache_clear()
