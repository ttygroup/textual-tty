# Claude Development Notes

## Code Style Requirements

- **NEVER put imports inside functions** - top of the file only.
- Always ask for explicit permission before adding legacy fallback methods.
- By default, old methods are removed. This is a pre-alpha release.
- This application is for Python version 3.10+. Use appropriate type hints
- **DONT USE PRINTS FOR DEBUGGING** this is a TUI app. Use the debug() from
  `textual_tty.log` and check `debug.log`
- Tests are in pytest functional style. No classes.
- We are in a `./.venv`, which might not be activated.
- The user will run tests with: `make test`. It might take a lot of tokens, so
  don't run it yourself unless asked.
- Claude is running in a tmux panel, so when the user says "peep the pane", use
  "tmux capture-pane -p -e -t" with the given pane. This is how we debug.

## Important

Don't put imports in functions without a good reason.

## VERY IMPORTNT

Remember not to put imports in functions.
