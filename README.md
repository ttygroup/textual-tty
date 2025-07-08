# textual-tty

A terminal emulator for Textual apps.

## Demo

```bash
uv pip install textual-tty
python3 -m 'textual_tty.demo'
```

## Usage

There's 3 widgets:

1. `textual_tty.Terminal`, a tty that you can use
2. `textual_tty.Program`, launch a program
3. `textual_tty.TerminalProgram`, a terminal emulator in a window

## todo - refactor plan

* Refactor so Terminal is the base class and TextualTerminal is the widget subclass
  * Use reactives to handle updates, cause events etc
* Move process management into the Terminal base class
* Rename Screen to Buffer and have the Terminal handle it
* Have the parser set modes on the Terminal, and write() text to it
* Move the tests to match new design
