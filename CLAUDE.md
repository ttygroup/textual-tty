# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

textual-tty is a terminal emulator library for Textual applications. It provides three main widgets:
1. `textual_tty.Terminal` - A basic terminal widget
2. `textual_tty.Program` - A widget that launches and manages a specific program
3. `textual_tty.TerminalProgram` - A complete terminal emulator in a window

The library enables embedding terminal functionality directly into Textual TUI applications.

## Development Commands

### Environment Setup
- `make dev` - Set up development environment (installs deps, pre-commit hooks)

### Testing and Quality
- `make test` - Run all tests using pytest
- `make coverage` - Generate HTML coverage report (outputs to stdout and ./htmlcov)
- `scripts/test.sh textual_tty` - Run tests directly
- `scripts/coverage.sh textual_tty` - Run coverage analysis directly
- `ruff` - Linting (configured in pyproject.toml with line length 120, target Python 3.10+)

### Documentation and Build
- Do not run these, they're for the user.
- `make docs` - Build documentation and publish to private blog
- `make dist` - Build distribution packages
- `make clean` - Clean caches and virtual environment, messing everything up.

### Demo and Testing
- `uvx textual-tty` - Run the demo application (from published release)
- `textual-tty` - Alternative demo command ()
- the user will run the app, and will provide a tmux pane for Claude to run tmux capture-pane on

## Architecture

### Core Components

**Terminal Stack (bottom to top):**
1. `pty_handler.py` - Cross-platform PTY interface (Unix pty, Windows winpty)
2. `parser.py` - VT100/ANSI terminal parser (state machine based on tmux's input.c)
3. `buffer.py` - Rich Text-based screen buffer storage
4. `terminal.py` - Base Terminal class (framework-agnostic)
5. `textual_terminal.py` - Textual-specific terminal widget

**Parser Architecture:**
- State machine implementation following Paul Williams' VT100 specification
- Processes utf8 from PTY into high-level screen operations
- Handles escape sequences, control codes, and text rendering

**Widget Hierarchy:**
- `Terminal` (base class) → `TextualTerminal` (Textual integration)

### Key Files
- `src/textual_tty/terminal.py` - Core terminal logic and process management
- `src/textual_tty/parser.py` - ANSI/VT100 escape sequence parser
- `src/textual_tty/buffer.py` - Terminal screen buffer implementation
- `src/textual_tty/pty_handler.py` - Cross-platform PTY interface
- `src/textual_tty/widgets/` - Textual widget implementations

### Dependencies
- `textual` - Primary UI framework
- `textual-window` - Window management
- `pywinpty` - Windows PTY support (Windows only)
- `rich` - Text styling and rendering

## Development Notes

### Current Status
The project is in refactor mode with ongoing work on:
- Windows terminal compatibility
- Mouse input handling
- Test suite fixes
- Cursor implementation
- Scrollback buffer support

### Testing
- Tests are organized by component: `tests/parser/`, `tests/screen/`
- Coverage reports available in `htmlcov/` after running coverage
- Uses pytest with coverage tracking

### Platform Support
- Primary: Unix/Linux/macOS (using standard pty)
- Windows: Uses pywinpty for PTY emulation
- Cross-platform PTY interface abstracts platform differences
