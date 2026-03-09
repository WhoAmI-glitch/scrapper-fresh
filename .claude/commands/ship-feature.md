# Command: /ship-feature

## Description
Implement a complete feature end-to-end, from database schema to UI, with tests and documentation.

## Usage
```
/ship-feature "<feature description>" [--scope web|api|data|full-stack] [--ticket NUA-XXX]
```

## Workflow

### Phase 1: Analysis
1. Parse the feature description and determine scope.
2. Identify affected packages and apps.
3. Check for existing related code, types, and utilities.
4. Determine the dependency graph (what must be built first).

### Phase 2: Design
1. Define the data model changes (if any).
2. Design API contracts (if any).
3. Plan UI components and pages (if any).
4. Document the plan as a checklist.

### Phase 3: Backend (if applicable)
1. Create database migrations.
2. Add/update Pydantic/Zod schemas.
3. Implement service layer with business logic.
4. Build API endpoints.
5. Write backend tests.

### Phase 4: Frontend (if applicable)
1. Create/update TypeScript types.
2. Build UI components (with accessibility).
3. Implement pages/routes.
4. Add client-side state management.
5. Write frontend tests.

### Phase 5: Integration
1. Wire frontend to backend.
2. Test the full flow end-to-end.
3. Handle error states and edge cases.
4. Add loading states and optimistic updates.

### Phase 6: Polish
1. Run full lint + type-check + test suite.
2. Verify accessibility (axe-core).
3. Check responsive design.
4. Update documentation.

### Phase 7: Ship
1. Create atomic commits per logical change.
2. Prepare PR description.
3. Run final validation.

## Acceptance Criteria
- [ ] Feature works end-to-end as described
- [ ] All new code has tests
- [ ] Type-checking passes across all affected packages
- [ ] Linting passes
- [ ] No accessibility violations
- [ ] Error states handled gracefully
- [ ] Loading states implemented
- [ ] Documentation updated
- [ ] Commits are atomic and conventional
