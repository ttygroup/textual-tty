#!/usr/bin/env python3
"""
Quantize demo - renders terminal output line by line to the host terminal.

This demo shows how the terminal emulator works by rendering only changed lines,
making the rendering process visible.
"""

import argparse
import asyncio
import sys
import os
import signal
import shutil
from textual_tty.terminal import Terminal


class QuantizeDemo:
    def __init__(self, command, fps=60):
        self.command = command
        self.fps = fps
        self.frame_time = 1.0 / fps
        self.terminal = None
        self.previous_lines = {}
        self.running = True

    async def run(self):
        # Get terminal size
        cols, lines = shutil.get_terminal_size((80, 24))

        # Create terminal
        self.terminal = Terminal(command=self.command, width=cols, height=lines)

        # Enable mouse tracking in host terminal
        sys.stdout.write("\033[?1003h")  # Enable mouse reporting
        sys.stdout.write("\033[?25l")  # Hide cursor
        sys.stdout.flush()

        # Clear screen
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

        # Set up signal handlers
        signal.signal(signal.SIGWINCH, self.handle_resize)
        signal.signal(signal.SIGINT, self.handle_interrupt)

        # Start terminal process
        await self.terminal.start_process()

        # Set up stdin forwarding
        loop = asyncio.get_event_loop()
        loop.add_reader(sys.stdin.fileno(), self.forward_stdin)

        # Main render loop
        try:
            while self.running and self.terminal.process and self.terminal.process.poll() is None:
                await self.render_frame()
                await asyncio.sleep(self.frame_time)
        finally:
            # Cleanup
            loop.remove_reader(sys.stdin.fileno())
            sys.stdout.write("\033[?1003l")  # Disable mouse reporting
            sys.stdout.write("\033[?25h")  # Show cursor
            sys.stdout.write("\033[0m")  # Reset attributes
            sys.stdout.flush()

            if self.terminal:
                self.terminal.stop_process()

    async def render_frame(self):
        """Render only changed lines."""
        for y in range(self.terminal.height):
            # Get current line with all formatting
            current_line = self.terminal.current_buffer.get_line(
                y,
                width=self.terminal.width,
                cursor_x=self.terminal.cursor_x,
                cursor_y=self.terminal.cursor_y,
                show_cursor=self.terminal.cursor_visible,
                mouse_x=self.terminal.mouse_x,
                mouse_y=self.terminal.mouse_y,
                show_mouse=self.terminal.show_mouse,
            )

            # Check if line changed
            if self.previous_lines.get(y) != current_line:
                # Move cursor to line position
                sys.stdout.write(f"\033[{y + 1};1H")
                # Write the line
                sys.stdout.write(current_line)
                sys.stdout.flush()

                # Store for next comparison
                self.previous_lines[y] = current_line

    def forward_stdin(self):
        """Forward stdin to the terminal."""
        try:
            data = os.read(sys.stdin.fileno(), 1024)
            if self.terminal and self.terminal.pty:
                self.terminal.pty.write(data)
        except OSError:
            pass

    def handle_resize(self, signum, frame):
        """Handle terminal resize."""
        cols, lines = shutil.get_terminal_size((80, 24))
        if self.terminal:
            self.terminal.resize(lines, cols)
            # Clear and force full redraw
            sys.stdout.write("\033[2J\033[H")
            self.previous_lines.clear()

    def handle_interrupt(self, signum, frame):
        """Handle Ctrl+C."""
        self.running = False


async def main():
    parser = argparse.ArgumentParser(description="Quantize terminal rendering demo")
    parser.add_argument("command", nargs="*", default=["/bin/bash"], help="Command to run (default: /bin/bash)")
    parser.add_argument("--fps", type=int, default=60, help="Frames per second (default: 60)")

    args = parser.parse_args()

    # Join command parts
    command = args.command if len(args.command) > 0 else ["/bin/bash"]

    demo = QuantizeDemo(command=command, fps=args.fps)
    await demo.run()


if __name__ == "__main__":
    # Set up raw mode for stdin
    import termios
    import tty

    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        asyncio.run(main())
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
