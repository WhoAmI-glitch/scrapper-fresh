# Command: /build-app

## Description
Scaffold and build a complete application or major feature from scratch within the NUAMAKA monorepo.

## Usage
```
/build-app <app-name> [--type web|api|data|mobile] [--description "..."]
```

## Workflow

### Phase 1: Planning
1. Analyze the request and determine application type.
2. Review existing monorepo structure for conventions and shared packages.
3. Create a detailed build plan with:
   - Architecture overview
   - File structure
   - Dependencies needed
   - Database schema (if applicable)
   - API contracts (if applicable)
   - UI components needed (if applicable)

### Phase 2: Scaffolding
1. Create the application directory structure under `apps/`.
2. Initialize `package.json` / `pyproject.toml` with correct workspace references.
3. Set up TypeScript config / Python tooling config.
4. Add the app to workspace configuration.
5. Install dependencies.

### Phase 3: Implementation
1. **Types/Interfaces first** — define all data models and contracts.
2. **Database layer** — create schemas and migrations.
3. **Business logic** — implement core services.
4. **API layer** — build endpoints/routes (if applicable).
5. **UI layer** — build pages and components (if applicable).
6. **Integration** — wire everything together.

### Phase 4: Quality
1. Write tests for all new code (target >80% coverage).
2. Run linting and type-checking.
3. Verify the app starts and serves requests.
4. Create documentation (README, API docs).

### Phase 5: Ship
1. Create atomic commits for each logical unit.
2. Run full validation suite.
3. Report results.

## Acceptance Criteria
- [ ] App scaffolded in correct monorepo location
- [ ] All dependencies installed and lockfile updated
- [ ] Type-checking passes
- [ ] Linting passes
- [ ] Tests pass with >80% coverage
- [ ] App starts successfully
- [ ] README.md created with setup instructions
- [ ] All commits follow conventional format
