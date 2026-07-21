# textual-tty

A terminal emulator for Textual apps, using `bittty`, my pure Python terminal
emulator.

Terminals in your terminal: draggable, resizable windows running real ptys.

## Demo

```bash
uvx textual-tty
```

## Usage

```python
from textual_tty import Terminal, TerminalWindow, Window

# A terminal as a plain widget: composes a bittty Board, never subclasses it.
yield Terminal(command="htop")

# Or in a draggable, resizable window that closes when the process exits.
yield TerminalWindow(command=["vim", "README.md"])
```

`Terminal` posts `Bell`, `TitleChanged` and `ProcessExited` messages; anything
deeper is on `terminal.board` (the bittty emulator). `Window` is a bare-bones
draggable/resizable window you can use for other things too.

Read the demo code (`textual_tty/demo.py`) for a working app.

## Links

* [🏠 home](https://ttygroup.github.io/textual-tty)
* [🗔  bittty](https://bitplane.net/dev/python/bittty)
* [🐍 pypi](https://pypi.org/project/textual-tty)
* [🐱 github](https://github.com/ttygroup/textual-tty)

## License

WTFPL with one additional clause

1. Don't blame me

Do wtf you want, but don't blame me when it rips a hole in your trousers.

