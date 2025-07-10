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

- [ ] resizing oddities
  - [ ] htop doesn't resize properly
- [x] implement mouse
- [ ] performance improvements
  - [x] profile it!
  - [ ] reduce draw calls
- [ ] scrollback buffer
  - [ ] rewrite app so we have consistent + performant buffer class
  - [ ] understand text wrapping
  - [ ] scrollbar support
- [ ] bugs
  - [ ] blank background to end of line
  - [x] clear + flip buffer = restore before clear
  - [ ] corruption in stream
  - [x] text input issues
    - This was caused by us not supporting all modes.
    - [x] implement keymapping that works inside and outside textual
  - [ ] scroll region: scroll up in `vim` corrupts outside scroll region
- [x] fix terminal bell
- [x] replace magic numbers with constants
- [ ] testing
  - [ ] move tests
    - [ ] unit tests to ./tests/unit
    - [ ] integration ./tests/integration
    - [ ] comparison scripts ./tests/integration/scripts
  - [ ] more coverage
- [ ] reduce redundancy redundancy of repeated repeated code code
  - [x] redundancy redundancy repeated repeated
  - [ ] code code of of redundancy redundancy
- [ ] add terminal visuals
  - [ ] text cursor
  - [ ] mouse cursor (disabled by default)
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

