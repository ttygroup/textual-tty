#!/usr/bin/env python3
"""Profile btop running directly in passthrough mode."""

import cProfile
import pstats
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import subprocess

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from textual.app import App, ComposeResult
from textual_tty.widgets import TextualTerminal


def get_git_info():
    """Get current git commit hash and check for uncommitted changes."""
    try:
        # Get short commit hash
        result = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True)
        commit_hash = result.stdout.strip()

        # Check for uncommitted changes
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
        has_changes = bool(result.stdout.strip())

        if has_changes:
            commit_hash += "+local_changes"

        return commit_hash
    except subprocess.CalledProcessError:
        return "unknown"


class PassthroughApp(App):
    """Full-screen terminal application."""

    CSS = """
    Screen {
        layout: vertical;
        padding: 0;
        margin: 0;
    }

    TextualTerminal {
        width: 100%;
        height: 100%;
        border: none;
        margin: 0;
        padding: 0;
    }
    """

    def compose(self) -> ComposeResult:
        """Create the terminal widget."""
        terminal = TextualTerminal(command=["btop"])
        terminal.show_mouse = True
        yield terminal

    def on_textual_terminal_process_exited(self, message) -> None:
        """Handle terminal process exit."""
        self.exit(message.exit_code)


async def run_with_timeout():
    """Run the app with a timeout."""
    app = PassthroughApp()

    # Schedule app exit after 10 seconds
    async def exit_after_delay():
        await asyncio.sleep(10)
        app.exit()

    # Run both the app and the timer
    app_task = asyncio.create_task(app.run_async())
    timer_task = asyncio.create_task(exit_after_delay())

    # Wait for either to complete (app will exit when timer fires)
    done, pending = await asyncio.wait([app_task, timer_task], return_when=asyncio.FIRST_COMPLETED)

    # Cancel any remaining tasks
    for task in pending:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


def main():
    # Create logs directory if it doesn't exist
    logs_dir = Path("./logs")
    logs_dir.mkdir(exist_ok=True)

    # Get timestamp and git info
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    git_hash = get_git_info()

    # Profile filename
    profile_file = logs_dir / f"btop_direct_profile_{timestamp}_{git_hash}.prof"
    txt_file = logs_dir / f"btop_direct_profile_{timestamp}_{git_hash}.txt"

    print("Profiling btop in passthrough mode for 10 seconds...")
    print(f"Profile will be saved to: {profile_file}")

    # Create profiler
    profiler = cProfile.Profile()

    # Start profiling
    profiler.enable()

    try:
        # Run the app with asyncio
        asyncio.run(run_with_timeout())

    except Exception as e:
        print(f"Error running app: {e}")
    finally:
        # Stop profiling
        profiler.disable()

    # Save profile data
    profiler.dump_stats(str(profile_file))

    # Also create a text report
    import io
    import contextlib

    with open(txt_file, "w") as f:
        f.write("btop Direct Performance Profile\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"Git commit: {git_hash}\n")
        f.write("Profile duration: 10 seconds\n")
        f.write("=" * 80 + "\n\n")

        # Capture stats output
        output = io.StringIO()
        stats = pstats.Stats(profiler)

        # Show by cumulative time
        f.write("TOP 100 FUNCTIONS BY CUMULATIVE TIME:\n")
        f.write("-" * 80 + "\n")
        stats.sort_stats("cumulative")
        with contextlib.redirect_stdout(output):
            stats.print_stats(100)
        f.write(output.getvalue())

        # Show by total time
        output = io.StringIO()
        f.write("\n\nTOP 100 FUNCTIONS BY TOTAL TIME:\n")
        f.write("-" * 80 + "\n")
        stats.sort_stats("tottime")
        with contextlib.redirect_stdout(output):
            stats.print_stats(100)
        f.write(output.getvalue())

        # Show callers for hot functions
        output = io.StringIO()
        f.write("\n\nCALLERS OF HOT FUNCTIONS:\n")
        f.write("-" * 80 + "\n")
        stats.sort_stats("tottime")
        with contextlib.redirect_stdout(output):
            stats.print_callers(20)
        f.write(output.getvalue())

    print(f"Profile saved to: {profile_file}")
    print(f"Text report saved to: {txt_file}")
    print("\nTop 30 functions by cumulative time:")

    # Print top functions to console
    stats = pstats.Stats(profiler)
    stats.sort_stats("cumulative")
    stats.print_stats(30)

    print("\n\nTop 30 functions by total time (excluding subcalls):")
    stats.sort_stats("tottime")
    stats.print_stats(30)


if __name__ == "__main__":
    main()
