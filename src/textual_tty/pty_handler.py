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

from . import constants
from .log import measure_performance


class PTYSocket(Protocol):
    """Protocol for PTY socket-like interface."""

    def read(self, size: int = constants.DEFAULT_PTY_BUFFER_SIZE) -> bytes:
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

    def __init__(self, rows: int = constants.DEFAULT_TERMINAL_HEIGHT, cols: int = constants.DEFAULT_TERMINAL_WIDTH):
        import pty

        self.master_fd, self.slave_fd = pty.openpty()
        self.rows = rows
        self.cols = cols
        self._closed = False
        self.resize(rows, cols)

    @measure_performance("UnixPTY")
    def read(self, size: int = constants.DEFAULT_PTY_BUFFER_SIZE) -> bytes:
        """Read data from the PTY."""
        if self._closed:
            return b""
        try:
            return os.read(self.master_fd, size)
        except OSError as e:
            if e.errno in (constants.EBADF, constants.EINVAL):
                self._closed = True
                raise
            return b""

    @measure_performance("UnixPTY")
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
                # Don't set LINES/COLUMNS - let process discover size via ioctl
                # Setting these prevents ncurses from responding to SIGWINCH properly
            }
        )

        # Ensure UTF-8 locale if not already set
        if "LANG" not in process_env or "UTF-8" not in process_env.get("LANG", ""):
            process_env["LANG"] = "en_US.UTF-8"
        if "LC_ALL" not in process_env:
            process_env["LC_ALL"] = process_env.get("LANG", "en_US.UTF-8")

        def preexec_fn():
            """Set up the child process to use PTY as controlling terminal."""
            import termios
            import fcntl

            # Create new session and become process group leader
            os.setsid()

            # Make the PTY the controlling terminal
            fcntl.ioctl(0, termios.TIOCSCTTY, 0)

        process = subprocess.Popen(
            command,
            shell=True,
            stdin=self.slave_fd,
            stdout=self.slave_fd,
            stderr=self.slave_fd,
            preexec_fn=preexec_fn,
            env=process_env,
        )

        # Close slave fd in parent (child has its own copy)
        os.close(self.slave_fd)
        self.slave_fd = None

        return process


class WinptyProcessWrapper:
    """Wrapper to provide subprocess.Popen-like interface for winpty PTY."""

    def __init__(self, pty):
        self.pty = pty
        self._returncode = None

    def poll(self):
        """Check if process is still running."""
        if self.pty.isalive():
            return None
        else:
            if self._returncode is None:
                self._returncode = constants.DEFAULT_EXIT_CODE
            return self._returncode

    def wait(self):
        """Wait for process to complete."""
        while self.pty.isalive():
            import time

            time.sleep(constants.PTY_POLL_INTERVAL)
        return self.poll()

    def terminate(self):
        """Terminate the process."""
        self.pty.close()

    def kill(self):
        """Kill the process."""
        self.pty.close()

    @property
    def returncode(self):
        """Get the return code."""
        return self.poll()


class WindowsPTY:
    """Windows PTY implementation using pywinpty."""

    def __init__(self, rows: int = constants.DEFAULT_TERMINAL_HEIGHT, cols: int = constants.DEFAULT_TERMINAL_WIDTH):
        try:
            import winpty

            self.pty = winpty.PTY(cols, rows)
            self.rows = rows
            self.cols = cols
            self._closed = False
        except ImportError:
            raise OSError("pywinpty not installed. Install with: pip install textual-terminal[windows]")

    @measure_performance("WindowsPTY")
    def read(self, size: int = constants.DEFAULT_PTY_BUFFER_SIZE) -> bytes:
        """Read data from the PTY."""
        if self._closed:
            return b""
        try:
            return self.pty.read(size)
        except Exception:
            return b""

    @measure_performance("WindowsPTY")
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
        if self._closed:
            raise OSError("PTY is closed")

        # Set environment variables for the process
        if env:
            for key, value in env.items():
                os.environ[key] = value

        # Add terminal environment variables
        os.environ.update(
            {
                "TERM": "xterm-256color",
                # Don't set LINES/COLUMNS - let process discover size via ioctl
                # Setting these prevents ncurses from responding to SIGWINCH properly
            }
        )

        # Use winpty to spawn the process attached to the PTY
        # Convert command to bytes as required by winpty
        if isinstance(command, str):
            # For shell commands, use cmd.exe
            if command.strip().startswith(("cmd", "powershell", "pwsh")):
                command_bytes = command.encode("utf-8")
            else:
                command_bytes = f'cmd.exe /c "{command}"'.encode("utf-8")
        else:
            command_bytes = command

        self.pty.spawn(command_bytes)

        # Return a process-like object that provides compatibility with subprocess.Popen
        return WinptyProcessWrapper(self.pty)


def create_pty(
    rows: int = constants.DEFAULT_TERMINAL_HEIGHT, cols: int = constants.DEFAULT_TERMINAL_WIDTH
) -> PTYSocket:
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
