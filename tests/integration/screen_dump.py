#!/usr/bin/env python3
"""
Screen dump utility for testing terminal output.

Launches a terminal with the given command, waits for timeout, then captures
and outputs the ANSI sequences to stdout.
"""

import argparse
import asyncio
from bittty import Terminal


async def main():
    parser = argparse.ArgumentParser(description="Capture terminal screen output as ANSI")
    parser.add_argument("command", nargs="+", help="Command to run in terminal")
    parser.add_argument("--timeout", type=float, default=2.0, help="Timeout in seconds (default: 2.0)")
    parser.add_argument("--cols", type=int, default=80, help="Terminal width in columns (default: 80)")
    parser.add_argument("--lines", type=int, default=24, help="Terminal height in lines (default: 24)")

    args = parser.parse_args()

    # Create terminal
    terminal = Terminal(command=args.command, width=args.cols, height=args.lines)

    # Start the terminal process
    await terminal.start_process()

    # Wait for timeout
    await asyncio.sleep(args.timeout)

    # Capture and output the screen content
    ansi_output = terminal.capture_pane()
    print(ansi_output)

    # Stop the terminal
    terminal.stop_process()


if __name__ == "__main__":
    asyncio.run(main())
