# TypeScript Patterns

TypeScript-specific conventions. See `../common/` for language-agnostic rules.

## Compiler Settings

- Always use `strict: true`. No exceptions.
- Enable `noUncheckedIndexedAccess` for array/object safety.
- Target ES2022 or later. Use modern syntax.

## Types

- Never use `any`. Use `unknown` for truly unknown types, then narrow.
- Prefer `interface` for object shapes that may be extended. Use `type` for unions, intersections, and computed types.
- Export types from the same file as their related functions.
- Use `readonly` for properties that should not be mutated after construction.

## Utility Types

- Use `Pick`, `Omit`, `Partial`, `Required` to derive types from existing ones. Do not duplicate.
- `Record<string, T>` for dictionaries. Never `{ [key: string]: T }`.
- `Awaited<T>` for unwrapping promise types.
- `satisfies` operator for type-safe object literals without widening.

## Null Handling

- Prefer `undefined` over `null` for optional values (aligns with optional chaining).
- Use optional chaining (`?.`) and nullish coalescing (`??`) instead of manual checks.
- Never use non-null assertion (`!`) except in test files.

## Functions

- Use arrow functions for callbacks. Use function declarations for top-level named functions.
- Always annotate return types on exported functions. Inferred types are fine for internal helpers.
- Use `const` assertions for literal tuples and objects.

## Async

- Always `await` promises. Never fire-and-forget without explicit `void` annotation.
- Use `Promise.all` for independent concurrent operations, not sequential `await`.
- Handle errors with try/catch at the boundary, not around every await.

## Enums

- Avoid `enum`. Use `as const` objects with derived union types instead.
- If you must use enum, use string enums (never numeric).

## Imports

- Use `import type` for type-only imports. This improves tree-shaking and build performance.
- Barrel files (`index.ts`) are acceptable for public APIs, not for internal modules.

## Error Handling

- Define custom error classes extending `Error` for domain-specific failures.
- Use discriminated unions for result types: `{ ok: true, data: T } | { ok: false, error: E }`.
- Never throw strings. Always throw Error instances.
