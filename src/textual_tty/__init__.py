"""textual-terminal: A terminal emulator for Textual apps."""

from .terminal import Terminal
from .widgets.textual_terminal import TextualTerminal
from .buffer import Buffer

__all__ = ["Terminal", "TextualTerminal", "Buffer"]
