# Command: /literature-review

## Description
Plan and structure a literature review for academic work.

## Usage
```
/literature-review "<research question or topic>" [--structure thematic|chronological|methodological|theoretical] [--words 2000]
```

## Instructions
1. Clarify the research question or topic
2. Identify key themes and sub-topics
3. Suggest search strategy (databases, keywords, date range)
4. Propose organizational structure:
   - Thematic (grouped by theme)
   - Chronological (historical development)
   - Methodological (grouped by approach)
   - Theoretical (grouped by framework)
5. Create an outline with sections and suggested source types
6. Provide guidance on critical analysis vs. summary
7. Include Regent's academic writing standards

## Output Format
```markdown
## Literature Review Plan: {Topic}

### Research Question
{Clearly stated research question}

### Scope and Boundaries
- **Included**: {what the review covers}
- **Excluded**: {what is deliberately out of scope}
- **Date range**: {time period for sources}
- **Disciplines**: {relevant fields}
- **Geographic scope**: {if applicable}

### Proposed Structure
**Type**: {Thematic / Chronological / Methodological / Theoretical}

| Section | Focus | Suggested Sources | Word Count |
|---|---|---|---|
| 1. Introduction | Context, scope, purpose | N/A | {n} words |
| 2. {Theme/Period/Method} | {Description} | {Source types} | {n} words |
| 3. {Theme/Period/Method} | {Description} | {Source types} | {n} words |
| 4. {Theme/Period/Method} | {Description} | {Source types} | {n} words |
| 5. Research Gaps | Missing areas, limitations | Synthesis | {n} words |
| 6. Conclusion | Summary, implications | N/A | {n} words |
| **Total** | | | **{total} words** |

### Search Strategy per Section
| Section | Databases | Keywords | Filters |
|---|---|---|---|
| {Section 2} | {databases} | {keywords} | {filters} |
| {Section 3} | {databases} | {keywords} | {filters} |

### Key Authors and Seminal Works
- **{Author}** — {contribution to the field}
- **{Author}** — {contribution to the field}

### Critical Analysis Framework
For each source or group of sources, address:
1. **What** — What are the main arguments/findings?
2. **How** — What methodology was used? Is it appropriate?
3. **Strength** — What does this study do well?
4. **Weakness** — What are the limitations?
5. **Relevance** — How does this connect to your research question?
6. **Synthesis** — How does this relate to other sources in the review?

### Academic Writing Reminders
- Synthesize, do not just summarize — compare and contrast sources
- Use reporting verbs: argues, suggests, demonstrates, contends, maintains
- Maintain critical distance — evaluate, do not just describe
- Use Harvard referencing (Regent's standard)
- Include page numbers for direct quotes
- Ensure every claim is supported by a cited source
```

## Acceptance Criteria
- [ ] Research question is clearly defined
- [ ] Scope and boundaries are explicit
- [ ] Structure type is justified
- [ ] All sections have word count allocations
- [ ] Search strategy covers appropriate databases
- [ ] Key authors/works identified for the field
- [ ] Critical analysis guidance is included
- [ ] Harvard referencing standard is noted
