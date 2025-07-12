"""
Integration tests comparing terminal output with reference tmux dumps.
"""

import pytest
from pathlib import Path
from textual.app import App
from textual_tty import Terminal


def get_ansi_files():
    """Get all .ansi files in the test directory."""
    test_dir = Path(__file__).parent
    return list(test_dir.glob("*.ansi"))


@pytest.mark.parametrize("ansi_file", get_ansi_files())
def test_terminal_output_matches_reference(ansi_file):
    """Test that terminal output matches tmux reference dump."""

    class TestApp(App):
        def compose(self):
            return Terminal(command=["cat", str(ansi_file)])

    app = TestApp()

    # Run app headless and capture output
    with app.run_test() as pilot:
        # Wait for terminal to process the cat command
        pilot.pause(0.5)

        # Get the terminal widget
        terminal = app.query_one(Terminal)

        # Capture the rendered output using tmux capture format
        captured_output = terminal.capture_pane()

        # Read expected output
        expected_output = ansi_file.read_text()

        # Compare outputs
        assert captured_output == expected_output, f"Output mismatch for {ansi_file.name}"
