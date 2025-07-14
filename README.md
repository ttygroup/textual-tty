# textual-tty

A pure Python terminal emulator for Textual apps, that aims for tmux
compatibility

Currently buggy and a bit slow, but it's still somewhat usable.

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

- [ ] split pty out into a cross platform package
- [ ] debug logger
  - [ ] add arg parser to demo app
  - [x] make file logging optional (and not default)
- [ ] break terminal project out from Textual deps
  - [x] pick a snazzy name - bitty/titty
  - [ ] gui
    - [ ] make `framebuffer.py`
    - [ ] choose a backend
  - [ ] asciinema streaming -> terminal web
- [ ] performance improvements
  - [ ] parse with regex over large buffer sizes
- [ ] scrollback buffer
  - [ ] consistent + performant scrollback
  - [ ] scrollbar support when used
- [ ] bugs
  - [ ] blank background to end of line
    - [ ] figure out proper order
  - [ ] corruption in stream - debug it
  - [ ] scroll region: scroll up in `vim` corrupts outside scroll region
- [ ] reduce redundancy redundancy of repeated repeated code code
  - [ ] code code of of redundancy redundancy
- [ ] add terminal visuals
  - [ ] bell flash effect (enabled in base class, disabled in `textual_terminal`)
- [ ] Theme support
  - [ ] base terminal using config + themes
  - [ ] theme for textual widget using CSS styles
  - [ ] textual app using theme/css loader
- [ ] flesh out terminal app
  - [ ] multiple tabs
  - [ ] settings panel
    - [ ] bell: system [Y/n], title bar [y/N], flash [y/N]
    - [ ] mouse: display [y/N]
    - [ ] wide chars detection
    - [ ] theme selector/editor
- [ ] terminal quantizer
  - [ ] move inside app
- [x] Windows support
