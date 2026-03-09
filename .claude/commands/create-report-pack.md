# Command: /create-report-pack

## Description
Generate a comprehensive report package containing analytics, insights, and visualizations for stakeholder review.

## Usage
```
/create-report-pack "<report title>" [--period weekly|monthly|quarterly] [--audience team|leadership|investors] [--format md|pdf|slides]
```

## Workflow

### Phase 1: Planning
1. Determine report scope based on period and audience.
2. Identify required data sources and metrics.
3. Define the report structure and sections.
4. Set appropriate level of detail for the target audience:
   - **Team**: Detailed, technical, actionable
   - **Leadership**: Strategic, high-level, decision-focused
   - **Investors**: Growth metrics, milestones, market position

### Phase 2: Data Gathering
1. Collect metrics from available data sources:
   - Platform analytics (users, engagement, retention)
   - Technical metrics (uptime, performance, deployment frequency)
   - Business metrics (revenue, growth rate, CAC, LTV)
   - Product metrics (feature adoption, NPS, churn)
2. Calculate period-over-period comparisons.
3. Identify trends and anomalies.

### Phase 3: Analysis
1. Synthesize data into narrative insights.
2. Create visualizations (Mermaid charts, tables).
3. Highlight wins, challenges, and risks.
4. Develop recommendations and action items.

### Phase 4: Report Generation
1. Assemble the report following the template.
2. Create executive summary (always first, always concise).
3. Add data tables and charts.
4. Include appendix with raw data if appropriate.
5. Save to `docs/reports/YYYY-MM-DD-{title-slug}/`.

### Phase 5: Supporting Assets
1. Generate a one-page summary (for email/Slack distribution).
2. Create a data appendix with detailed numbers.
3. Prepare talking points for presentation.

## Output Structure
```markdown
# {Report Title}

**Period**: {date range}
**Prepared**: {date}
**Audience**: {team|leadership|investors}

## Executive Summary
{3-5 key points that a busy executive needs to know}

## Key Metrics Dashboard
| Metric | Current | Previous | Change |
|---|---|---|---|
| ... | ... | ... | +/-% |

## Highlights
### Wins
- {Positive developments}

### Challenges
- {Issues and blockers}

## Detailed Analysis

### {Section 1: e.g., User Growth}
{Analysis with supporting data}

### {Section 2: e.g., Product Performance}
{Analysis with supporting data}

### {Section 3: e.g., Technical Health}
{Analysis with supporting data}

## Recommendations
| # | Action | Owner | Priority | Timeline |
|---|---|---|---|---|
| 1 | ... | ... | P0/P1/P2 | ... |

## Appendix
{Raw data, methodology notes, definitions}
```

## Acceptance Criteria
- [ ] Report follows the output structure
- [ ] Executive summary is concise and actionable
- [ ] All metrics have period-over-period comparisons
- [ ] Visualizations are clear and accurate
- [ ] Recommendations are specific with owners and timelines
- [ ] Report saved to correct location
- [ ] One-page summary generated
- [ ] Appropriate detail level for target audience
