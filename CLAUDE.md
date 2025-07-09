# Claude Development Notes

## Code Style Guidelines

- **NEVER put imports inside functions** - all imports should be at the top of the file
- Follow existing code patterns and conventions
- Maintain consistency with Rich Text span handling

## Testing

Run tests with: `python -m pytest`

## Key Implementation Notes

- The buffer.py clear_region method needs to explicitly create spans for cleared regions to match test expectations
- Rich Text optimizes away default/empty styles, but tests expect explicit spans