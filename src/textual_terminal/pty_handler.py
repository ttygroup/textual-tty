"""
Platform-specific PTY handling.

This module provides a unified interface for creating and managing PTYs
across different platforms (Unix/Linux/macOS vs Windows).
"""

from __future__ import annotations

import os
import sys
import subprocess
from typing import Tuple, Optional, Dict, Any


def create_pty() -> Tuple[int, int]:
    """Create a new PTY (master, slave) pair.
    
    Returns:
        Tuple of (master_fd, slave_fd)
    
    Raises:
        OSError: If PTY creation fails
    """
    if sys.platform == "win32":
        # Windows requires pywinpty
        try:
            import winpty
            # Create a winpty PTY
            pty = winpty.PTY(80, 24)
            return pty.master, pty.slave
        except ImportError:
            raise OSError(
                "pywinpty not installed. Install with: pip install textual-terminal[windows]"
            )
    else:
        # Unix/Linux/macOS - use built-in pty module
        import pty
        return pty.openpty()


def spawn_process(
    command: str,
    slave_fd: int,
    env: Optional[Dict[str, str]] = None,
    **kwargs: Any
) -> subprocess.Popen:
    """Spawn a process attached to a PTY.
    
    Args:
        command: Command to run
        slave_fd: Slave file descriptor from create_pty()
        env: Environment variables
        **kwargs: Additional arguments for subprocess.Popen
        
    Returns:
        The spawned process
    """
    if sys.platform == "win32":
        # Windows PTY handling is different
        # This is a simplified version - real implementation would need
        # to handle ConPTY or WinPTY specifics
        return subprocess.Popen(
            command,
            shell=True,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            env=env,
            **kwargs
        )
    else:
        # Unix/Linux/macOS
        return subprocess.Popen(
            command,
            shell=True,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            start_new_session=True,
            env=env,
            **kwargs
        )


def set_terminal_size(fd: int, rows: int, cols: int) -> None:
    """Set the terminal window size.
    
    Args:
        fd: File descriptor (usually slave_fd)
        rows: Number of rows
        cols: Number of columns
    """
    if sys.platform == "win32":
        # Windows uses different API
        # This would need to be implemented with pywinpty
        pass
    else:
        # Unix/Linux/macOS
        try:
            import termios
            import struct
            import fcntl
            
            winsize = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)
        except (ImportError, OSError):
            pass


def read_pty(fd: int, size: int = 4096) -> bytes:
    """Read from a PTY file descriptor.
    
    Args:
        fd: File descriptor to read from
        size: Maximum number of bytes to read
        
    Returns:
        Bytes read from the PTY
    """
    if sys.platform == "win32":
        # Windows might need special handling
        try:
            return os.read(fd, size)
        except OSError:
            return b""
    else:
        # Unix/Linux/macOS
        try:
            # Set non-blocking mode
            import fcntl
            flags = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
            
            return os.read(fd, size)
        except (OSError, BlockingIOError):
            return b""


def write_pty(fd: int, data: bytes) -> int:
    """Write to a PTY file descriptor.
    
    Args:
        fd: File descriptor to write to
        data: Data to write
        
    Returns:
        Number of bytes written
    """
    try:
        return os.write(fd, data)
    except OSError:
        return 0