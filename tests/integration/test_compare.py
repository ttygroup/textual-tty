"""
Integration tests comparing terminal output with reference tmux dumps.
"""

import asyncio
import pytest
from pathlib import Path
from bittty import Terminal


def get_ansi_files():
    """Get all .ansi files in the test directory."""
    test_dir = Path(__file__).parent / "compare"
    return list(test_dir.glob("*.ansi"))

@pytest.mark.skip
@pytest.mark.parametrize("ansi_file", get_ansi_files())
async def test_terminal_output_matches_reference(ansi_file):
    """Test that terminal output matches tmux reference dump."""

    # Create terminal
    terminal = Terminal(command=["cat", str(ansi_file)], width=80, height=24)

    try:
        # Start the terminal process
        await terminal.start_process()

        # Wait for the process to exit, with a timeout.
        if terminal.process:
            loop = asyncio.get_running_loop()
            wait_future = loop.run_in_executor(None, terminal.process.wait)
            try:
                await asyncio.wait_for(wait_future, timeout=2.0)
            except asyncio.TimeoutError:
                pytest.fail(f"Process for {ansi_file.name} timed out.")

        # Give the PTY reader a moment to process the final output
        await asyncio.sleep(0.1)

        # Capture the rendered output using tmux capture format
        captured_output = terminal.capture_pane()

        # Read expected output
        expected_output = ansi_file.read_text()

        # Compare outputs
        assert captured_output == expected_output, f"Output mismatch for {ansi_file.name}"

    finally:
        # Stop the terminal
        terminal.stop_process()
