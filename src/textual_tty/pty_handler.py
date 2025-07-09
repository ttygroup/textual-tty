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


class WindowsPTY:
    """Windows PTY implementation using pywinpty with ConPTY support."""

    def __init__(self, rows: int = 24, cols: int = 80):
        try:
            import winpty

            self.pty = winpty.PTY(cols, rows)
            self.rows = rows
            self.cols = cols
            self._closed = False
            self._process = None
            self.master_fd = None
        except ImportError:
            raise OSError("pywinpty not installed. Install with: pip install pywinpty")

    def read(self, size: int = 4096) -> bytes:
        """Read data from the PTY."""
        if self._closed:
            return b""
        try:
            data = self.pty.read(size)
            # Convert unicode string to bytes if necessary
            if isinstance(data, str):
                return data.encode("utf-8", errors="replace")
            return data
        except Exception:
            return b""

    def write(self, data: bytes) -> int:
        """Write data to the PTY."""
        if self._closed:
            return 0
        try:
            # Convert bytes to string if necessary
            if isinstance(data, bytes):
                data = data.decode("utf-8", errors="replace")
            self.pty.write(data)
            return len(data.encode("utf-8"))
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
                if self._process and self.pty.isalive():
                    # Try to gracefully terminate the process
                    self._process.terminate()
                self.pty.close()
            except Exception:
                pass
            self._closed = True

    @property
    def closed(self) -> bool:
        """Check if PTY is closed."""
        return self._closed or (self._process and not self.pty.isalive())

    def spawn_process(self, command: str, env: Optional[Dict[str, str]] = None) -> subprocess.Popen:
        """Spawn a process attached to this PTY."""
        if self._closed:
            raise OSError("PTY is closed")

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

        try:
            # Use winpty to spawn the process with proper PTY attachment
            self.pty.spawn(command, env=process_env)

            # Create a mock subprocess.Popen-like object for compatibility
            class WinptyProcess:
                def __init__(self, pty):
                    self.pty = pty
                    self.returncode = None

                def poll(self):
                    """Check if process is still running."""
                    if not self.pty.isalive():
                        if self.returncode is None:
                            self.returncode = self.pty.get_exitstatus()
                        return self.returncode
                    return None

                def wait(self, timeout=None):
                    """Wait for process to complete."""
                    # Simple polling implementation
                    import time

                    start_time = time.time()
                    while self.pty.isalive():
                        if timeout and (time.time() - start_time) > timeout:
                            raise subprocess.TimeoutExpired(command, timeout)
                        time.sleep(0.01)
                    self.returncode = self.pty.get_exitstatus()
                    return self.returncode

                def terminate(self):
                    """Terminate the process."""
                    # winpty doesn't have a direct terminate method
                    # We'll rely on the PTY close operation
                    pass

                def kill(self):
                    """Kill the process."""
                    # winpty doesn't have a direct kill method
                    # We'll rely on the PTY close operation
                    pass

            self._process = WinptyProcess(self.pty)
            return self._process

        except Exception:
            # Fallback to regular subprocess if winpty spawning fails
            # This provides compatibility but without PTY features
            return subprocess.Popen(
                command,
                shell=True,
                env=process_env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=False,
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
