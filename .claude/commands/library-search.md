# Command: /library-search

## Description
Search Regent's University London library resources for academic sources on a topic.

## Usage
```
/library-search "<research topic or question>"
```

## Instructions
1. Parse the research topic/question from the user
2. Generate search queries with Boolean operators (AND, OR, NOT)
3. Recommend which databases to search based on discipline:
   - Business: Business Source, Emerald, ProQuest Business
   - Social Sciences: JSTOR, Sage, Taylor & Francis
   - General: EBSCO Discovery, Academic Search Complete
   - Market/Industry: Mintel, Statista, IBISWorld
4. Provide search strings optimized for each database
5. Suggest subject headings, keywords, and synonyms
6. Recommend filters (date range, peer-reviewed, full text)
7. Output a structured search plan the user can execute

## Output Format
```markdown
## Library Search Plan: {Topic}

### Research Question
{Refined research question}

### Key Search Terms and Synonyms
| Concept | Primary Term | Synonyms / Alternatives |
|---|---|---|
| Concept 1 | term | synonym A, synonym B, synonym C |
| Concept 2 | term | synonym D, synonym E, synonym F |

### Database Recommendations (Ranked by Relevance)
1. **{Database}** — {why this database is relevant}
2. **{Database}** — {why this database is relevant}
3. **{Database}** — {why this database is relevant}

### Search Strings per Database
| Database | Search String |
|---|---|
| EBSCO Discovery | `"term one" AND ("term two" OR "synonym") AND NOT "exclusion"` |
| {Database 2} | `...` |
| {Database 3} | `...` |

### Suggested Filters
- **Date range**: {recommended range}
- **Peer-reviewed**: Yes / No
- **Full text available**: Yes / No
- **Language**: English (or as specified)
- **Source type**: Academic journals / Books / Reports

### Expected Result Types
- {Type 1}: {description}
- {Type 2}: {description}

### Access Notes
- On-campus: direct access via library portal
- Off-campus: use EZproxy or Regent's VPN
- A-Z database list: regents-uk.libguides.com/az.php
```

## Acceptance Criteria
- [ ] Research question is clearly stated
- [ ] At least 3 databases recommended with justification
- [ ] Search strings use correct Boolean syntax for each database
- [ ] Synonyms and alternative terms are provided
- [ ] Filters are appropriate for the research scope
- [ ] Access method is noted (proxy/VPN for off-campus)
