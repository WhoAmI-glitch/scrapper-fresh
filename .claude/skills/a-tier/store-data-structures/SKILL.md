---
name: store-data-structures
description: Zustand store data structure patterns for LobeHub. Covers List vs Detail data structures, Map + Reducer patterns, type definitions, and when to use each pattern. Use when designing store state, choosing data structures, or implementing list/detail pages.
---

# LobeHub Store Data Structures

How to structure data in Zustand stores for optimal performance and user experience.

## Core Principles

**DO**: Separate List and Detail types, use Map for details (`Record<string, Detail>`), use Array for lists, import types from `@lobechat/types` (never `@lobechat/database`).

**DON'T**: Use single detail object (can't cache multiple pages), mix List and Detail types, use database types in stores.

## Type Definitions

Organize by entity in separate files. Detail types include ALL fields; List types are subsets excluding heavy fields, with optional computed stats for UI.

```typescript
// Full entity (detail pages)
export interface AgentEvalBenchmark {
  id: string;
  name: string;
  description?: string | null;
  identifier: string;
  rubrics: EvalBenchmarkRubric[]; // Heavy field
  isSystem: boolean;
  createdAt: Date;
  updatedAt: Date;
}

// Lightweight (list display) - subset, not extension
export interface AgentEvalBenchmarkListItem {
  id: string;
  name: string;
  description?: string | null;
  identifier: string;
  isSystem: boolean;
  createdAt: Date;
  // rubrics excluded (heavy)
  testCaseCount?: number; // Computed for UI
  datasetCount?: number;
}
```

**Heavy fields to exclude from List**: large text (content, editorData), complex objects (rubrics, config), binary data, large arrays.

## When to Use Map vs Array

**Map** (`xxxDetailMap: Record<string, Xxx>`) for detail page data: caches multiple pages, supports optimistic updates, per-item loading states.

**Array** (`xxxList: XxxListItem[]`) for list display: read-only or refresh-as-whole, simple data flow.

## State Structure

```typescript
interface BenchmarkSliceState {
  // List - simple array
  benchmarkList: AgentEvalBenchmarkListItem[];
  benchmarkListInit: boolean;
  // Detail - map for caching
  benchmarkDetailMap: Record<string, AgentEvalBenchmark>;
  loadingBenchmarkDetailIds: string[];
  // Mutation states
  isCreatingBenchmark: boolean;
  isUpdatingBenchmark: boolean;
  isDeletingBenchmark: boolean;
}
```

## Reducer Pattern (for Detail Map)

```typescript
import { produce } from 'immer';

type BenchmarkDetailDispatch =
  | { type: 'setBenchmarkDetail'; id: string; value: AgentEvalBenchmark }
  | { type: 'updateBenchmarkDetail'; id: string; value: Partial<AgentEvalBenchmark> }
  | { type: 'deleteBenchmarkDetail'; id: string };

export const benchmarkDetailReducer = (
  state: Record<string, AgentEvalBenchmark> = {},
  payload: BenchmarkDetailDispatch,
): Record<string, AgentEvalBenchmark> => {
  switch (payload.type) {
    case 'setBenchmarkDetail':
      return produce(state, (d) => { d[payload.id] = payload.value; });
    case 'updateBenchmarkDetail':
      return produce(state, (d) => {
        if (d[payload.id]) d[payload.id] = { ...d[payload.id], ...payload.value };
      });
    case 'deleteBenchmarkDetail':
      return produce(state, (d) => { delete d[payload.id]; });
    default:
      return state;
  }
};
```

### Internal Dispatch

```typescript
internal_dispatchBenchmarkDetail: (payload) => {
  const currentMap = get().benchmarkDetailMap;
  const nextMap = benchmarkDetailReducer(currentMap, payload);
  if (isEqual(nextMap, currentMap)) return;
  set({ benchmarkDetailMap: nextMap }, false, `dispatch/${payload.type}`);
},
```

## Component Usage

```typescript
// List access
const benchmarks = useEvalStore((s) => s.benchmarkList);

// Detail access (from map)
const benchmark = useEvalStore((s) => benchmarkId ? s.benchmarkDetailMap[benchmarkId] : undefined);
const isLoading = useEvalStore((s) => benchmarkId ? s.loadingBenchmarkDetailIds.includes(benchmarkId) : false);

// Selectors (recommended)
export const benchmarkSelectors = {
  getBenchmarkDetail: (id: string) => (s: EvalStore) => s.benchmarkDetailMap[id],
  isLoadingDetail: (id: string) => (s: EvalStore) => s.loadingBenchmarkDetailIds.includes(id),
};
```

## Checklist

- [ ] Organize types by entity in separate files
- [ ] Detail type: full entity with all fields
- [ ] ListItem type: subset (not extension), exclude heavy fields, may add computed stats
- [ ] Array for list data, Map for detail data
- [ ] Per-item loading: `loadingXxxDetailIds: string[]`
- [ ] Reducer for detail map mutations
- [ ] Internal dispatch and loading methods
- [ ] Selectors for clean access
- [ ] Comment what fields are excluded and why

## Best Practices

1. One entity per file
2. ListItem is subset, not extension of Detail
3. Clear naming: `xxxList` for arrays, `xxxDetailMap` for maps
4. Consistent patterns across all detail maps
5. Never use `any`, always proper types
6. Use Immer in reducers for immutability
7. Per-item loading for details, global for lists
