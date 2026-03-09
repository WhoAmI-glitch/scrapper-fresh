# Command: /market-brief

## Description
Generate a comprehensive market brief or competitive analysis for a wellness industry topic.

## Usage
```
/market-brief "<topic>" [--focus competitors|trends|opportunities|regulations] [--depth quick|standard|deep]
```

## Workflow

### Phase 1: Scope
1. Parse the topic and determine the research focus.
2. Identify key questions to answer.
3. Determine the appropriate depth level:
   - **Quick**: 1-page summary with key insights (30 min)
   - **Standard**: Full brief with data tables and recommendations (2 hrs)
   - **Deep**: Comprehensive analysis with projections and strategy (4+ hrs)

### Phase 2: Research
1. Gather data from available sources:
   - Competitor websites and app stores
   - Industry reports and news
   - Academic publications
   - Regulatory databases
   - Social media and community sentiment
2. Organize findings by theme.
3. Identify data gaps and note limitations.

### Phase 3: Analysis
1. Synthesize findings into actionable insights.
2. Create comparison tables where applicable.
3. Identify NUAMAKA's positioning opportunities.
4. Assess risks and challenges.
5. Develop recommendations ranked by impact/effort.

### Phase 4: Deliverable
1. Write the brief following the research template.
2. Include executive summary for quick consumption.
3. Add data visualizations (Mermaid charts) where helpful.
4. Save to `docs/research/YYYY-MM-DD-{topic-slug}.md`.

## Output Structure
```markdown
# Market Brief: {Topic}

**Date**: {today}
**Depth**: Quick | Standard | Deep
**Prepared for**: NUAMAKA Product Team

## Executive Summary
{3-5 key takeaways}

## Market Overview
{Size, growth, key players}

## Competitive Landscape
{Comparison matrix of relevant competitors}

## Trends & Signals
{What is changing and why it matters}

## Opportunities for NUAMAKA
{Specific, actionable opportunities}

## Risks & Challenges
{What could go wrong}

## Recommendations
{Prioritized action items}

## Sources
{Numbered references}
```

## Acceptance Criteria
- [ ] Brief follows the output structure
- [ ] All claims have sources
- [ ] Recommendations are specific and actionable
- [ ] NUAMAKA positioning is addressed
- [ ] Saved to correct location in `docs/research/`
