#!/usr/bin/env python3
"""Demo application runner."""

import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from textual_terminal.demo import main

if __name__ == "__main__":
    main()
