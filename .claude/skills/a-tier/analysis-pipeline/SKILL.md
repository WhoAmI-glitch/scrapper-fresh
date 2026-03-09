---
name: analysis-pipeline
description: >
  Build data analysis and enrichment pipelines for transforming raw scraped data
  into actionable intelligence. Use when building ETL pipelines, data enrichment
  workflows, entity extraction, deduplication, scoring algorithms, or when the
  user needs to process scraped data through multiple transformation stages.
---

# Analysis Pipeline Patterns

Transform raw scraped data into structured, enriched, actionable intelligence.

## Pipeline Stages

### 1. Ingestion
- Accept data from multiple sources (scrapers, APIs, files)
- Normalize input formats to common schema
- Assign unique identifiers and timestamps
- Log ingestion metadata

### 2. Cleaning
- Remove duplicates by content hash
- Normalize text (whitespace, encoding, case)
- Validate against expected schemas
- Flag and quarantine malformed records

### 3. Enrichment
- Entity extraction (companies, people, locations)
- Cross-reference with external databases
- Geocoding and address normalization
- Industry/sector classification
- Sentiment analysis on text fields

### 4. Scoring & Ranking
- Define scoring criteria (relevance, quality, freshness)
- Weight factors by importance
- Normalize scores to 0-100 scale
- Rank results by composite score

### 5. Output
- Structure for downstream consumers (API, dashboard, export)
- Generate summaries and highlights
- Export to Excel/CSV/JSON
- Trigger notifications for high-value results

## Quality Metrics
- Completeness: % of fields populated
- Accuracy: validation pass rate
- Freshness: time since last update
- Deduplication: unique record ratio
