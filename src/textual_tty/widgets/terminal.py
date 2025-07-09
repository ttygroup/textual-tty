"""
Terminal widget for Textual applications.

This module provides the main Terminal widget that can be embedded in Textual apps
to provide terminal emulation capabilities.
"""

from __future__ import annotations

from typing import Any

from ..textual_terminal import TextualTerminal


class Terminal(TextualTerminal):
    """A terminal emulator widget that can run shell commands."""

    def __init__(
        self,
        command: str = "/bin/bash",
        width: int = 80,
        height: int = 24,
        **kwargs: Any,
    ) -> None:
        """Initialize the terminal widget."""
        super().__init__(command=command, width=width, height=height, **kwargs)
