# Security

These rules are non-negotiable for all code in the workspace.

## Secrets

- Never hardcode secrets, API keys, tokens, or passwords in source files.
- Use environment variables or a secrets manager. Reference `.env.example` for required variables.
- Never commit `.env`, credentials files, or private keys. Verify `.gitignore` covers them.
- If a secret is accidentally committed, rotate it immediately. Do not just delete the commit.

## Input Validation

- Validate all external input at the boundary (API handlers, CLI args, file parsers).
- Use schema validation (zod, pydantic, JSON Schema) rather than manual checks.
- Sanitize user input before rendering in HTML to prevent XSS.
- Parameterize all database queries. Never interpolate user input into SQL.

## Authentication and Authorization

- Check authorization on every request, not just at the UI level.
- Use established libraries for auth (next-auth, passport, etc.). Do not roll your own.
- Tokens must have expiry. Refresh tokens must be rotatable.
- Log authentication failures. Rate-limit login attempts.

## Dependencies

- Pin dependency versions. Use lockfiles (package-lock.json, uv.lock).
- Run `npm audit` / `pip audit` in CI. Block merges on critical vulnerabilities.
- Review new dependencies before adding. Check maintenance status and download count.
- Minimize dependency surface. Prefer stdlib when the task is simple.

## Data Handling

- Encrypt sensitive data at rest and in transit (TLS everywhere).
- Never log sensitive data (passwords, tokens, PII).
- Apply principle of least privilege to database credentials and API scopes.
- Implement proper CORS configuration. Do not use `*` in production.

## File Operations

- Validate file paths to prevent directory traversal.
- Set size limits on file uploads.
- Never execute user-uploaded files.
