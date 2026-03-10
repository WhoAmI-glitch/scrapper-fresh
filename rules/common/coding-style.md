# Coding Style

These conventions apply to all code in the workspace regardless of language.

## Naming

- Use descriptive names. Abbreviations only when universally understood (e.g., `id`, `url`, `config`).
- Functions: verb-first (`getUserById`, `validate_schema`, `parse_response`).
- Booleans: prefix with `is`, `has`, `should`, `can` (`isValid`, `hasPermission`).
- Constants: UPPER_SNAKE_CASE for true constants, camelCase/snake_case for computed values.
- Files: kebab-case for non-class files, PascalCase for class/component files.

## Formatting

- Indentation: 2 spaces for JS/TS/JSON/YAML, 4 spaces for Python.
- Max line length: 100 characters. Break long lines at logical boundaries.
- Trailing commas in multi-line arrays and objects (where language supports it).
- Single quotes for strings in JS/TS, double quotes in Python.

## Comments

- Do not comment what the code does. Comment WHY it does it.
- Use `TODO:` with a brief description for deferred work. Never leave bare TODOs.
- Delete commented-out code. Version control exists for history.
- Document public APIs with JSDoc or docstrings. Internal helpers need comments only when non-obvious.

## Error Handling

- Never swallow errors silently. Log or re-throw with context.
- Use early returns to avoid deep nesting.
- Prefer specific error types over generic ones.
- Include the failing input in error messages when safe to do so.

## Functions

- Maximum 40 lines per function. Extract when longer.
- Maximum 4 parameters. Use an options object/dict beyond that.
- Pure functions preferred. Isolate side effects at the boundary.
- Single responsibility: one function does one thing.

## Imports

- Group imports: stdlib, external packages, internal modules. Blank line between groups.
- No unused imports. Configure linter to enforce.
- Prefer named exports over default exports.
