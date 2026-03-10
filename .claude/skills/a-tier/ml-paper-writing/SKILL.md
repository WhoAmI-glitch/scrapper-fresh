---
name: ml-paper-writing
description: Write publication-ready ML/AI papers for NeurIPS, ICML, ICLR, ACL, AAAI, COLM. Use when drafting papers from research repos, structuring arguments, verifying citations, or preparing camera-ready submissions. Includes LaTeX templates, reviewer guidelines, and citation verification workflows.
version: 1.0.0
author: Orchestra Research
license: MIT
tags: [Academic Writing, NeurIPS, ICML, ICLR, ACL, AAAI, COLM, LaTeX, Paper Writing, Citations, Research]
dependencies: [semanticscholar, arxiv, habanero, requests]
---

# ML Paper Writing for Top AI Conferences

Expert guidance for writing publication-ready papers targeting NeurIPS, ICML, ICLR, ACL, AAAI, and COLM. Combines writing philosophy from top researchers with practical tools.

## CRITICAL: Never Hallucinate Citations

**NEVER generate BibTeX entries from memory. ALWAYS fetch programmatically.**

| Action | Correct | Wrong |
|--------|---------|-------|
| Adding a citation | Search API, verify, fetch BibTeX | Write BibTeX from memory |
| Uncertain about paper | Mark as `[CITATION NEEDED]` | Guess the reference |
| Can't find exact paper | Note: "placeholder - verify" | Invent similar-sounding paper |

If you cannot verify a citation, mark it as a placeholder and explicitly tell the scientist.

## Core Philosophy

Paper writing is collaborative. Claude's role: understand the repo, deliver a complete first draft, search literature, refine through feedback. **Be proactive -- deliver drafts, then iterate.**

| Confidence | Action |
|-----------|--------|
| **High** (clear repo) | Write full draft, deliver, iterate |
| **Medium** (some ambiguity) | Write draft with flagged uncertainties |
| **Low** (major unknowns) | Ask 1-2 targeted questions, then draft |

## The Narrative Principle

Your paper is a story with one clear contribution supported by evidence.

**Three Pillars** (crystal clear by end of introduction):
- **The What**: 1-3 specific novel claims
- **The Why**: Rigorous empirical evidence
- **The So What**: Why readers should care

**If you cannot state your contribution in one sentence, you don't yet have a paper.**

## Workflow: Starting from a Research Repository

1. Explore repo structure, README, results
2. Identify existing citations in codebase
3. Clarify contribution with scientist
4. Search for additional literature
5. Deliver complete first draft

## Paper Structure

**Time Allocation** (Neel Nanda): Spend roughly equal time on abstract, introduction, figures, and everything else combined.

### Writing Checklist

1. Define one-sentence contribution (verify with scientist)
2. Draft Figure 1 (many readers skip to it)
3. Write Abstract (5-sentence formula): What you achieved, Why hard/important, How (with keywords), Evidence, Best result
4. Write Introduction (1-1.5 pages max, 2-4 contribution bullets)
5. Methods (enable reimplementation, all hyperparameters)
6. Experiments (explicit claims per experiment, error bars, compute info)
7. Related Work (organize methodologically, cite generously)
8. Limitations (required, pre-empt reviewer criticisms)
9. Complete paper checklist (NeurIPS/ICML/ICLR all require this)

## Writing Style Guidelines

**Sentence-Level Clarity** (Gopen & Swan):
- Keep subject and verb close
- Place emphasis at sentence ends
- Put context first, new info after
- Each paragraph makes one point
- Use verbs, not nominalizations

**Word Choice** (Lipton): Be specific ("accuracy" not "performance"), eliminate hedging, avoid intensifiers, delete filler words

**Precision** (Steinhardt): Consistent terminology, state assumptions formally, provide intuition alongside rigor

## Conference Requirements

| Conference | Pages | Key Requirement |
|------------|-------|-----------------|
| NeurIPS 2025 | 9 | Mandatory checklist |
| ICML 2026 | 8 | Broader Impact Statement |
| ICLR 2026 | 9 | LLM disclosure required |
| ACL 2025 | 8 (long) | Limitations section mandatory |
| AAAI 2026 | 7 | Strict style adherence |
| COLM 2025 | 9 | Language model focus |

**Universal**: Double-blind, references don't count toward limit, LaTeX required.

## Using LaTeX Templates

1. Copy entire template directory (not just main.tex)
2. Verify template compiles before changes
3. Keep template examples as reference
4. Replace content section by section
5. Clean up template artifacts only at end

**Never**: Copy only main.tex, modify .sty files, add random packages

## Citation Workflow

```
For every citation:
1. Search (Exa MCP or Semantic Scholar API)
2. Verify in 2+ sources
3. Retrieve BibTeX via DOI (programmatically)
4. Verify the claim you're citing actually appears
5. Add verified BibTeX
6. If ANY step fails -> mark placeholder, inform scientist
```

**Fetch BibTeX via DOI:**
```python
import requests
def doi_to_bibtex(doi: str) -> str:
    response = requests.get(f"https://doi.org/{doi}", headers={"Accept": "application/x-bibtex"})
    response.raise_for_status()
    return response.text
```

## Format Conversion (Resubmission)

When converting between venues:
- Start fresh with target template, copy only content sections
- Never copy LaTeX preambles between templates
- Adjust for page limits (move proofs to appendix, condense related work)
- Update conference-specific requirements (Broader Impact, LLM disclosure, etc.)

## Tables and Figures

**Tables**: Use `booktabs`, bold best values, include direction symbols, right-align numbers
**Figures**: Vector graphics (PDF/EPS), colorblind-safe palettes, self-contained captions, no title inside figure

## References

- [references/writing-guide.md](references/writing-guide.md) - Full writing principles
- [references/citation-workflow.md](references/citation-workflow.md) - Citation APIs and code
- [references/checklists.md](references/checklists.md) - Conference checklists
- [references/reviewer-guidelines.md](references/reviewer-guidelines.md) - Evaluation criteria
- [templates/](templates/) - LaTeX templates for all venues
