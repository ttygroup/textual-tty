"""Convert bittty cell styles to Rich styles for Textual rendering.

Cells come straight off the board's video memory as (Style, char) pairs;
mapping the Style object directly to Rich skips the old round-trip of
rendering ANSI text and having Rich parse it back.
"""

from __future__ import annotations

from functools import lru_cache

from bittty.style import Color, Style
from rich.color import Color as RichColor
from rich.style import Style as RichStyle


def _rich_color(color: Color | None) -> RichColor | None:
    if color is None or color.mode == "default":
        return None
    if color.mode == "indexed":
        return RichColor.from_ansi(color.value)
    r, g, b = color.value
    return RichColor.from_rgb(r, g, b)


@lru_cache(maxsize=4096)
def to_rich_style(style: Style) -> RichStyle:
    """Map a bittty style onto Rich; unset (None) attributes inherit."""
    return RichStyle(
        color=_rich_color(style.fg),
        bgcolor=_rich_color(style.bg),
        bold=style.bold,
        dim=style.dim,
        italic=style.italic,
        underline=style.underline,
        underline2=True if style.underline_style == "double" else None,
        blink=style.blink,
        reverse=style.reverse,
        conceal=style.conceal,
        strike=style.strike,
        overline=style.overline,
        frame=style.framed,
        encircle=style.encircled,
        link=style.hyperlink,
    )
