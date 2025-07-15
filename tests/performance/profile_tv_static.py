#!/usr/bin/env python3
"""Profile the tv-static demo and save results."""

import cProfile
import pstats
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

def get_git_info():
    """Get current git commit hash and check for uncommitted changes."""
    try:
        # Get short commit hash
        result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                              capture_output=True, text=True, check=True)
        commit_hash = result.stdout.strip()
        
        # Check for uncommitted changes
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, check=True)
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
    profile_file = logs_dir / f"tv_static_profile_{timestamp}_{git_hash}.prof"
    txt_file = logs_dir / f"tv_static_profile_{timestamp}_{git_hash}.txt"
    
    print(f"Profiling tv-static for 20 seconds...")
    print(f"Profile will be saved to: {profile_file}")
    
    # Create profiler
    profiler = cProfile.Profile()
    
    # Start profiling
    profiler.enable()
    
    try:
        # Run the tv-static demo with timeout
        result = subprocess.run([
            "timeout", "20s", 
            "python", "./tests/performance/run_command.py", 
            "./demo/scripts/tv-static"
        ], capture_output=True, text=True, timeout=25)
        
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
    
    with open(txt_file, 'w') as f:
        f.write(f"TV-Static Performance Profile\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"Git commit: {git_hash}\n")
        f.write(f"Profile duration: 20 seconds\n")
        f.write("=" * 80 + "\n\n")
        
        # Capture stats output to string then write to file
        output = io.StringIO()
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        with contextlib.redirect_stdout(output):
            stats.print_stats(50)  # Top 50 functions
        f.write(output.getvalue())
    
    print(f"Profile saved to: {profile_file}")
    print(f"Text report saved to: {txt_file}")
    print("\nTop 20 functions by cumulative time:")
    
    # Print top functions to console
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)

if __name__ == "__main__":
    main()