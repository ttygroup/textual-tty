"""textual-terminal: A terminal emulator for Textual apps."""

from bittty import Terminal, Buffer
from .widgets.textual_terminal import TextualTerminal

__all__ = ["Terminal", "TextualTerminal", "Buffer"]
