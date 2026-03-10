# Testing

These testing conventions apply to all projects in the workspace.

## Coverage

- New code must have tests. No exceptions for "simple" code.
- Target 80% line coverage minimum. Critical paths (auth, payments, data mutations) target 95%.
- Coverage is measured per PR, not globally. Do not let existing gaps justify new gaps.

## Test Naming

- Name tests as sentences: `it("returns 404 when user does not exist")`.
- Group related tests with `describe` blocks that read as documentation.
- Pattern: `[unit under test] [scenario] [expected result]`.

## Structure

- Arrange / Act / Assert (AAA) pattern. One blank line between each section.
- One assertion per test when practical. Multiple assertions acceptable if testing a single logical outcome.
- No logic in tests: no conditionals, no loops, no try/catch.

## Isolation

- Unit tests must not touch the network, filesystem, or database.
- Use dependency injection or mocks for external services.
- Each test must be independent. No shared mutable state between tests.
- Reset mocks in `beforeEach` / `setUp`, not in individual tests.

## Test Data

- Use factory functions or fixtures for test data, not inline object literals.
- Never use production data in tests.
- Use deterministic values. No `Math.random()` or `Date.now()` in test setup.

## Performance

- Unit tests should complete in under 5 seconds total.
- Integration tests should complete in under 30 seconds.
- Mark slow tests explicitly so they can be excluded from fast feedback loops.

## What Not to Test

- Framework internals or third-party library behavior.
- Trivial getters/setters with no logic.
- Private implementation details (test through public interface).
