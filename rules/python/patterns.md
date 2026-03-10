# Python Patterns

Python-specific conventions. See `../common/` for language-agnostic rules.

## Version and Tooling

- Target Python 3.11+. Use modern syntax (match statements, `X | Y` union types).
- Use `uv` for dependency management. `uv pip install`, `uv run`, `uv sync`.
- Lockfile: `uv.lock`. Pin all dependencies. No floating versions.
- Use `ruff` for linting and formatting. Configure in `pyproject.toml`.

## Type Hints

- Type-hint all function signatures (parameters and return types).
- Use `from __future__ import annotations` for forward references.
- Prefer `list[str]` over `List[str]` (builtin generics, Python 3.9+).
- Use `TypeAlias` for complex type definitions.
- Use `Protocol` for structural typing instead of ABC when possible.

## Data Classes

- Use `@dataclass` or `pydantic.BaseModel` for structured data. No raw dicts for domain objects.
- Use `frozen=True` for immutable data classes.
- Use `field(default_factory=list)` for mutable defaults. Never `def __init__(self, items=[])`.

## Async

- Use `asyncio` for IO-bound concurrency. Use `multiprocessing` for CPU-bound work.
- Prefer `async def` / `await` over callback patterns.
- Use `asyncio.gather` for concurrent independent tasks.
- Never mix sync and async database calls in the same codebase.

## Error Handling

- Define custom exceptions inheriting from a project base exception.
- Use `raise ... from e` to preserve exception chains.
- Catch specific exceptions, never bare `except:`.
- Use `contextlib.suppress` for expected exceptions that should be silenced.

## Imports

- Follow isort conventions: stdlib, third-party, local. Blank line between groups.
- Absolute imports only. No relative imports except within a package's `__init__.py`.
- Never `from module import *`.

## Testing

- Use `pytest` with `pytest-asyncio` for async tests.
- Fixtures over setUp/tearDown. Use `conftest.py` for shared fixtures.
- Use `pytest.mark.parametrize` for data-driven tests.

## Project Structure

- `src/` layout: `src/package_name/`. Not flat layout.
- Entry points in `pyproject.toml`, not `setup.py`.
- Configuration in `pyproject.toml` (single config file, not scattered).
