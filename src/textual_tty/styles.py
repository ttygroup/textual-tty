"""Convert bittty cell styles to Rich styles for Textual rendering.

Cells come straight off the board's video memory as (Style, char) pairs;
mapping the Style object directly to Rich skips the old round-trip of
rendering ANSI text and having Rich parse it back. Colours resolve through
the board's palette device, so OSC 4/10/11 redefinitions render truthfully;
callers cache per Style and invalidate on `palette.generation`.
"""

from __future__ import annotations

from bittty.style import Style
from rich.color import Color as RichColor
from rich.style import Style as RichStyle


def rich_color(rgb: tuple[int, int, int] | None) -> RichColor | None:
    return None if rgb is None else RichColor.from_rgb(*rgb)


def to_rich_style(style: Style, palette) -> RichStyle:
    """Map a bittty style onto Rich; unset (None) attributes inherit."""
    return RichStyle(
        color=rich_color(palette.resolve(style.fg)),
        bgcolor=rich_color(palette.resolve(style.bg)),
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
