#!/usr/bin/env python3
"""Profile the passthrough demo running btop for performance analysis."""

import cProfile
import pstats
import subprocess
from pathlib import Path
from datetime import datetime


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


def main():
    # Create logs directory if it doesn't exist
    logs_dir = Path("./logs")
    logs_dir.mkdir(exist_ok=True)

    # Get timestamp and git info
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    git_hash = get_git_info()

    # Profile filename
    profile_file = logs_dir / f"passthrough_btop_profile_{timestamp}_{git_hash}.prof"
    txt_file = logs_dir / f"passthrough_btop_profile_{timestamp}_{git_hash}.txt"

    print("Profiling passthrough.py with btop for 10 seconds...")
    print(f"Profile will be saved to: {profile_file}")

    # Create profiler
    profiler = cProfile.Profile()

    # Start profiling
    profiler.enable()

    try:
        # Run the passthrough demo with btop using timeout
        # Use run_command.py which handles TUI apps properly
        subprocess.run(
            ["timeout", "10s", "python", "./demo/passthrough.py", "btop"], capture_output=True, text=True, timeout=12
        )

    except subprocess.TimeoutExpired:
        print("Process timed out (expected)")
    except Exception as e:
        print(f"Error running process: {e}")
    finally:
        # Stop profiling
        profiler.disable()

    # Save profile data
    profiler.dump_stats(str(profile_file))

    # Also create a text report with timestamp and git info
    import io
    import contextlib

    with open(txt_file, "w") as f:
        f.write("Passthrough + btop Performance Profile\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"Git commit: {git_hash}\n")
        f.write("Profile duration: 10 seconds\n")
        f.write("=" * 80 + "\n\n")

        # Capture stats output to string then write to file
        output = io.StringIO()
        stats = pstats.Stats(profiler)

        # First, show by cumulative time (total time including subcalls)
        f.write("TOP 50 FUNCTIONS BY CUMULATIVE TIME:\n")
        f.write("-" * 80 + "\n")
        stats.sort_stats("cumulative")
        with contextlib.redirect_stdout(output):
            stats.print_stats(50)
        f.write(output.getvalue())

        # Also show by total time (time in the function itself)
        output = io.StringIO()
        f.write("\n\nTOP 50 FUNCTIONS BY TOTAL TIME:\n")
        f.write("-" * 80 + "\n")
        stats.sort_stats("tottime")
        with contextlib.redirect_stdout(output):
            stats.print_stats(50)
        f.write(output.getvalue())

    print(f"Profile saved to: {profile_file}")
    print(f"Text report saved to: {txt_file}")
    print("\nTop 20 functions by cumulative time:")

    # Print top functions to console
    stats = pstats.Stats(profiler)
    stats.sort_stats("cumulative")
    stats.print_stats(20)

    print("\n\nTop 20 functions by total time (excluding subcalls):")
    stats.sort_stats("tottime")
    stats.print_stats(20)


if __name__ == "__main__":
    main()
