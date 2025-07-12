# textual-tty

A pure Python terminal emulator for Textual apps, that aims for tmux
compatibility.

Currently lacks a cursor, any decent debugging tools, and is too chatty,
but it's still somewhat usable.

## Demo

```bash
uvx textual-tty
```

## Usage

There's 3 main classes:

1. `Terminal`, a standalone terminal that doesn't need Textual.
2. `TextualTerminal`, a tty widget subclass.
3. `TerminalApp`, a terminal emulator in a window.

Read the demo code for more info.

## Links

* [🏠 home](https://bitplane.net/dev/python/textual-tty)
* [🐍 pypi](https://pypi.org/project/textual-tty)
* [🐱 github](https://github.com/bitplane/textual-tty)

## License

WTFPL with one additional clause

1. Don't blame me

Do wtf you want, but don't blame me when it rips a hole in your trousers.

## todo / ideas

- [ ] debug logger
  - [ ] make file logging optional
  - [ ] add arg parser to demo app
- [ ] break terminal project out from Textual deps
  - [ ] pick a snazzy name
  - [ ] stdio -> pty wrapper
  - [ ] gui
    - [ ] make `framebuffer.py`
    - [ ] choose a backend
  - [ ] asciinema streaming -> terminal web
- [ ] performance improvements
  - [x] rewrite using ANSI buffer grid
  - [ ] parse with regex over large buffer sizes
  - [x] lazily draw the outputs, render to Rich at the last moment
- [ ] scrollback buffer
  - [ ] rewrite app so we have consistent + performant buffer class
  - [ ] scrollbar support when used
- [ ] bugs
  - [x] blank background to end of line
    - [x] Move away from rich
  - [ ] corruption in stream
  - [ ] scroll region: scroll up in `vim` corrupts outside scroll region
- [ ] testing
  - [ ] move tests
    - [ ] integration ./tests/integration
    - [ ] comparison scripts ./tests/integration/scripts
    - [x] performance ./test/performance
  - [ ] more coverage
  - [x] performance counters
- [ ] reduce redundancy redundancy of repeated repeated code code
  - [ ] code code of of redundancy redundancy
- [ ] add terminal visuals
  - [x] mouse cursor (disabled by default)
  - [ ] bell flash effect (enabled in base class, disabled in textual_terminal)
- [ ] Theme support
  - [ ] base terminal using config + themes
  - [ ] textual widget using CSS styles
  - [ ] textual app using theme/css loader
- [ ] flesh out terminal app
  - [ ] multiple tabs
  - [ ] settings panel
    - [ ] bell: system [Y/n], title bar [y/N], flash [y/N]
    - [ ] mouse: display [y/N]
    - [ ] wide chars detection
    - [ ] theme selector/editor

