"""Tests for OSC (Operating System Command) sequences."""

from textual_tty.parser import Parser
from textual_tty.terminal import Terminal


def render_terminal_to_string(terminal: Terminal) -> str:
    """Render the terminal content to a plain string for testing."""
    lines = []
    for line in terminal.get_content():
        lines.append(line.plain)
    return "\n".join(lines)


def test_osc_window_title():
    """Test OSC sequence for setting window title."""
    terminal = Terminal(width=80, height=24)
    parser = Parser(terminal)

    # OSC 0 sets window title
    # Format: ESC ] 0 ; <title> BEL
    title_sequence = "\x1b]0;My Terminal Window\x07"
    parser.feed(title_sequence)

    # Window title should not appear in screen content
    output = render_terminal_to_string(terminal)
    assert "My Terminal Window" not in output
    assert output.strip() == ""  # Screen should be empty


def test_osc_window_title_with_text():
    """Test OSC sequence followed by regular text."""
    terminal = Terminal(width=80, height=24)
    parser = Parser(terminal)

    # OSC sequence followed by text
    data = "\x1b]0;Terminal Title\x07Hello World"
    parser.feed(data)

    # Only "Hello World" should be visible
    output = render_terminal_to_string(terminal)
    assert "Terminal Title" not in output
    assert "Hello World" in output


def test_ps1_osc_title_sequence():
    """Test PS1 prompt with OSC (Operating System Command) sequences."""
    # Your PS1: \[\e]0;\u@\h: \w\a\]${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$
    # Let's break it down:
    # \[\e]0;...\a\] - OSC sequence to set terminal title
    # \[\033[01;32m\] - Green bold
    # \[\033[00m\] - Reset
    # \[\033[01;34m\] - Blue bold

    terminal = Terminal(width=80, height=24)
    parser = Parser(terminal)

    # Simulate a typical PS1 prompt output
    # The \e]0;user@host: /path\a part is an OSC sequence that sets the window title
    ps1_text = "\x1b]0;user@host: /home/user\x07user@host:/home/user$ "

    parser.feed(ps1_text)

    # The OSC sequence should not appear in the visible output
    output = render_terminal_to_string(terminal)
    assert "user@host: /home/user" not in output  # This is the window title, shouldn't be visible
    assert "user@host:/home/user$ " in output  # This is the actual prompt

    # Check cursor position is after the prompt
    assert terminal.cursor_x == len("user@host:/home/user$ ")


def test_ps1_with_colors():
    """Test PS1 with color escape sequences."""
    terminal = Terminal(width=80, height=24)
    parser = Parser(terminal)

    # Simplified PS1 with colors: green username, blue path
    # \033[01;32m = bold green
    # \033[01;34m = bold blue
    # \033[00m = reset
    ps1_text = "\x1b[01;32muser@host\x1b[00m:\x1b[01;34m~/projects\x1b[00m$ "

    parser.feed(ps1_text)

    # Check the text content
    output = render_terminal_to_string(terminal)
    assert "user@host:~/projects$ " in output

    # Check that styles were applied correctly
    line = terminal.get_content()[0]
    # The text should have different styled spans
    assert len(line.spans) > 1  # Should have multiple styled sections


def test_osc_string_terminator():
    """Test OSC with ST (String Terminator) instead of BEL."""
    terminal = Terminal(width=80, height=24)
    parser = Parser(terminal)

    # OSC can be terminated with ST (ESC \) instead of BEL
    # Format: ESC ] 0 ; <title> ESC \
    title_sequence = "\x1b]0;My Title\x1b\\"
    parser.feed(title_sequence)

    # Title should not appear in screen content
    output = render_terminal_to_string(terminal)
    assert "My Title" not in output
