# Git Workflow

Conventions for version control across all projects.

## Branch Naming

- `main` is the production branch. Always deployable.
- Feature branches: `feat/<short-description>` (e.g., `feat/user-avatar-upload`).
- Bug fixes: `fix/<short-description>`.
- Chores: `chore/<short-description>` (deps, CI, refactoring).
- Keep branch names under 50 characters. Use hyphens, not underscores.

## Commit Messages

- Format: `<type>: <description>` where type is `feat`, `fix`, `chore`, `docs`, `test`, `refactor`.
- Description is imperative mood, lowercase, no period: `feat: add user avatar upload`.
- Body (optional): explain WHY, not WHAT. The diff shows what changed.
- Maximum 72 characters for the subject line.
- Reference issue numbers when applicable: `fix: resolve race condition in queue (#42)`.

## Pull Requests

- One PR per logical change. Do not bundle unrelated changes.
- PR title follows commit message format.
- Description must include: what changed, why, and how to test.
- Keep PRs under 400 lines of diff when possible. Break large changes into stacked PRs.
- Require at least one review before merge.

## Merge Strategy

- Prefer squash merge for feature branches (clean history).
- Use merge commits only for long-lived branches with meaningful intermediate commits.
- Delete branches after merge.
- Never force-push to `main`.

## Pre-commit

- Run linter and formatter before commit (configure via git hooks or pre-commit framework).
- Run type checker if applicable.
- Tests are encouraged pre-push but not required pre-commit (speed matters).

## Tags and Releases

- Use semantic versioning: `v1.2.3`.
- Tag releases on `main` only.
- Include changelog entries in release notes.
