# textual-tty

A terminal emulator for Textual apps.

## Demo

```bash
uvx textual-tty
```

## Usage

There's 3 main classes

1. `textual_tty.Terminal`, a standalone terminal
2. `textual_tty.TextualTerminal`, a tty widget subclass
3. `textual_tty.TerminalApp`, a terminal emulator in a window

## todo

- [ ] fix resizing - apps like htop don't resize
- [ ] arrow keys for input in tui apps, not sure what's happening
- [ ] performance improvements
  - [ ] profile it!
  - [ ] fix the slow parts
