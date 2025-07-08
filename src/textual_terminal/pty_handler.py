"""
Cross-platform PTY (Pseudo Terminal) interface.

This module provides a unified PTY interface that works across Unix/Linux/macOS
and Windows, providing a socket-like object for terminal communication.
"""

from __future__ import annotations

import os
import sys
import subprocess
from typing import Optional, Dict, Protocol


class PTYSocket(Protocol):
    """Protocol for PTY socket-like interface."""

    def read(self, size: int = 4096) -> bytes:
        """Read data from the PTY."""
        ...

    def write(self, data: bytes) -> int:
        """Write data to the PTY."""
        ...

    def resize(self, rows: int, cols: int) -> None:
        """Resize the terminal."""
        ...

    def close(self) -> None:
        """Close the PTY."""
        ...

    @property
    def closed(self) -> bool:
        """Check if PTY is closed."""
        ...


class UnixPTY:
    """Unix/Linux/macOS PTY implementation."""

    def __init__(self, rows: int = 24, cols: int = 80):
        import pty

        self.master_fd, self.slave_fd = pty.openpty()
        self.rows = rows
        self.cols = cols
        self._closed = False
        self.resize(rows, cols)

    def read(self, size: int = 4096) -> bytes:
        """Read data from the PTY."""
        if self._closed:
            return b""
        try:
            return os.read(self.master_fd, size)
        except OSError as e:
            if e.errno in (9, 22):  # EBADF or EINVAL - fd is closed
                self._closed = True
                raise
            return b""

    def write(self, data: bytes) -> int:
        """Write data to the PTY."""
        if self._closed:
            return 0
        try:
            return os.write(self.master_fd, data)
        except OSError:
            return 0

    def resize(self, rows: int, cols: int) -> None:
        """Resize the terminal using TIOCSWINSZ ioctl."""
        self.rows = rows
        self.cols = cols
        if self._closed:
            return

        try:
            import termios
            import struct
            import fcntl

            winsize = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, winsize)
        except (ImportError, OSError):
            pass

    def close(self) -> None:
        """Close the PTY file descriptors."""
        if not self._closed:
            try:
                if self.master_fd and isinstance(self.master_fd, int):
                    os.close(self.master_fd)
            except OSError:
                pass
            try:
                if self.slave_fd and isinstance(self.slave_fd, int):
                    os.close(self.slave_fd)
            except OSError:
                pass
            self._closed = True

    @property
    def closed(self) -> bool:
        """Check if PTY is closed."""
        return self._closed

    def spawn_process(self, command: str, env: Optional[Dict[str, str]] = None) -> subprocess.Popen:
        """Spawn a process attached to this PTY."""
        process_env = dict(os.environ)
        if env:
            process_env.update(env)

        # Add terminal environment variables
        process_env.update(
            {
                "TERM": "xterm-256color",
                "LINES": str(self.rows),
                "COLUMNS": str(self.cols),
            }
        )

        # Ensure UTF-8 locale if not already set
        if "LANG" not in process_env or "UTF-8" not in process_env.get("LANG", ""):
            process_env["LANG"] = "en_US.UTF-8"
        if "LC_ALL" not in process_env:
            process_env["LC_ALL"] = process_env.get("LANG", "en_US.UTF-8")

        process = subprocess.Popen(
            command,
            shell=True,
            stdin=self.slave_fd,
            stdout=self.slave_fd,
            stderr=self.slave_fd,
            start_new_session=True,
            env=process_env,
        )

        # Close slave fd in parent (child has its own copy)
        os.close(self.slave_fd)
        self.slave_fd = None

        return process


class WindowsPTY:
    """Windows PTY implementation using pywinpty."""

    def __init__(self, rows: int = 24, cols: int = 80):
        try:
            import winpty

            self.pty = winpty.PTY(cols, rows)
            self.rows = rows
            self.cols = cols
            self._closed = False
        except ImportError:
            raise OSError("pywinpty not installed. Install with: pip install textual-terminal[windows]")

    def read(self, size: int = 4096) -> bytes:
        """Read data from the PTY."""
        if self._closed:
            return b""
        try:
            return self.pty.read(size)
        except Exception:
            return b""

    def write(self, data: bytes) -> int:
        """Write data to the PTY."""
        if self._closed:
            return 0
        try:
            return self.pty.write(data)
        except Exception:
            return 0

    def resize(self, rows: int, cols: int) -> None:
        """Resize the terminal."""
        self.rows = rows
        self.cols = cols
        if not self._closed:
            try:
                self.pty.set_size(cols, rows)
            except Exception:
                pass

    def close(self) -> None:
        """Close the PTY."""
        if not self._closed:
            try:
                self.pty.close()
            except Exception:
                pass
            self._closed = True

    @property
    def closed(self) -> bool:
        """Check if PTY is closed."""
        return self._closed

    def spawn_process(self, command: str, env: Optional[Dict[str, str]] = None) -> subprocess.Popen:
        """Spawn a process attached to this PTY."""
        process_env = dict(os.environ)
        if env:
            process_env.update(env)

        # Add terminal environment variables
        process_env.update(
            {
                "TERM": "xterm-256color",
                "LINES": str(self.rows),
                "COLUMNS": str(self.cols),
            }
        )

        # Ensure UTF-8 locale if not already set
        if "LANG" not in process_env or "UTF-8" not in process_env.get("LANG", ""):
            process_env["LANG"] = "en_US.UTF-8"
        if "LC_ALL" not in process_env:
            process_env["LC_ALL"] = process_env.get("LANG", "en_US.UTF-8")

        # Windows subprocess handling is different
        return subprocess.Popen(
            command,
            shell=True,
            env=process_env,
        )


def create_pty(rows: int = 24, cols: int = 80) -> PTYSocket:
    """Create a platform-appropriate PTY socket.

    Args:
        rows: Terminal height in characters
        cols: Terminal width in characters

    Returns:
        PTY socket object with read/write/resize interface
    """
    if sys.platform == "win32":
        return WindowsPTY(rows, cols)
    else:
        return UnixPTY(rows, cols)
