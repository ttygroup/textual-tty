# Claude Development Notes

## Code Style Requirements

- **NEVER put imports inside functions** - top of the file only.
- Always ask for explicit permission before adding legacy fallback methods.
- By default, old methods are removed. This is a pre-alpha release.
- This application is for Python version 3.10+. Use appropriate type hints
- **DONT USE PRINTS FOR DEBUGGING** this is a TUI app. Use the debug() from
  `textual_tty.log` and check `debug.log`

## Testing

Run tests with: `make test`

## Key Implementation Notes

- The buffer.py clear_region method needs to explicitly create spans for cleared regions to match test expectations
- Rich Text optimizes away default/empty styles, but tests expect explicit spans
