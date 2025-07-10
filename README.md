# textual-tty

A terminal emulator for Textual apps.

Made by summarizing tmux's code, implementing a similar structure then almost
vibe coding it into existence with Claude and Gemini.

Currently lacks a cursor, mouse, any decent debugging tools, and is too chatty,
but it's still somewhat usable.

## Demo

```bash
uvx textual-tty
```

## Usage

There's 3 main classes:

1. `textual_tty.Terminal`, a standalone terminal that doesn't need Textual.
2. `textual_tty.TextualTerminal`, a tty widget subclass.
3. `textual_tty.TerminalApp`, a terminal emulator in a window.

See the demo for more info.

## Links

* [🏠 home](https://bitplane.net/dev/python/textual-tty)
* [🐍 pypi](https://pypi.org/project/textual-tty)
* [🐱 github](https://github.com/bitplane/textual-tty)

## License

WTFPL with one additional clause

1. Don't blame me

Do wtf you want, but don't blame me if it rips a hole in your trousers.

## todo

- [ ] fix resizing - apps like htop don't resize
- [ ] implement cursor (with width)
- [ ] arrow keys for input in tui apps, not sure what's happening
- [ ] performance improvements
  - [x] profile it!
  - [ ] reduce draw calls
- [ ] bugs
  - [x] scroll region
  - [ ] blank background to end of line
  - [x] `ESC[nnnnb` repeat sequence (nethogs)
- [ ] more coverage
- [ ] reduce redundancy redundancy of repeated repeated code code
