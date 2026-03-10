---
name: scientific-writing
description: Use when writing scientific manuscripts in full paragraphs (never bullet points). Core skill for the deep research and writing tool. Use two-stage process with (1) section outlines with key points using research-lookup then (2) convert to flowing prose. IMRAD structure, citations (APA/AMA/Vancouver), figures/tables, and reporting guidelines (CONSORT/STROBE/PRISMA).
license: MIT license
metadata:
    skill-author: K-Dense Inc.
---

# Scientific Writing

## Overview

**This is the core skill for the deep research and writing tool**--combining AI-driven deep research with well-formatted written outputs. Every document produced is backed by comprehensive literature search and verified citations through the research-lookup skill.

Scientific writing is a process for communicating research with precision and clarity. Write manuscripts using IMRAD structure, citations (APA/AMA/Vancouver), figures/tables, and reporting guidelines (CONSORT/STROBE/PRISMA).

**Critical Principle: Always write in full paragraphs with flowing prose. Never submit bullet points in the final manuscript.** Use a two-stage process: first create section outlines with key points using research-lookup, then convert those outlines into complete paragraphs.

## When to Use This Skill

- Writing or revising any section of a scientific manuscript
- Structuring a research paper using IMRAD or other standard formats
- Formatting citations and references (APA, AMA, Vancouver, Chicago, IEEE)
- Creating figures, tables, and data visualizations
- Applying reporting guidelines (CONSORT, STROBE, PRISMA)
- Preparing manuscripts for submission to specific journals

## Visual Enhancement

**Every scientific paper MUST include a graphical abstract plus 1-2 additional AI-generated figures using the scientific-schematics skill.**

Generate the graphical abstract FIRST:
```bash
python scripts/generate_schematic.py "Graphical abstract for [paper title]: [brief description]" -o figures/graphical_abstract.png
```

Use `scientific-schematics` for technical diagrams (flowcharts, pathways, architectures) and `generate-image` for visual content (illustrations, infographics).

## Core Capabilities

### 1. Manuscript Structure (IMRAD)

- **Introduction**: Establish research context, identify gaps, state objectives
- **Methods**: Detail study design, populations, procedures, and analysis approaches
- **Results**: Present findings objectively without interpretation
- **Discussion**: Interpret results, acknowledge limitations, propose future directions

**Alternative Structures**: Review articles, case reports, meta-analyses, theoretical/modeling papers, methods papers.

### 2. Section-Specific Writing

**Abstract**: 100-250 words; standalone summary of purpose, methods, results, conclusions. Support structured and unstructured formats.

**Introduction**: Establish importance, review literature, identify gaps, state hypotheses, explain novelty.

**Methods**: Ensure reproducibility through detailed participant descriptions, procedures, statistical methods, equipment specs, ethical approval.

**Results**: Logical flow from primary to secondary outcomes, integration with figures/tables, statistical significance with effect sizes.

**Discussion**: Relate to research questions, compare with literature, acknowledge limitations, propose implications and future research.

### 3. Citation Management

**Major Styles**: AMA (numbered superscript, medicine), Vancouver (numbered brackets, biomedical), APA (author-date, social sciences), Chicago (notes-bibliography, humanities), IEEE (numbered brackets, engineering).

**Best Practices**: Cite primary sources, include recent literature (5-10 years), balance distribution, verify against originals.

### 4. Figures and Tables

- Tables for precise numerical data; Figures for trends, patterns, relationships
- Make each self-explanatory with complete captions
- Label all axes with units, include sample sizes and statistical annotations
- Follow "one table/figure per 1000 words" guideline
- Avoid duplicating information between text, tables, and figures

### 5. Reporting Guidelines

| Guideline | Study Type |
|-----------|-----------|
| CONSORT | Randomized controlled trials |
| STROBE | Observational studies |
| PRISMA | Systematic reviews and meta-analyses |
| STARD | Diagnostic accuracy studies |
| TRIPOD | Prediction model studies |
| ARRIVE | Animal research |
| CARE | Case reports |

### 6. Writing Principles

**Clarity**: Precise language, define terms at first use, logical flow, active voice.
**Conciseness**: Eliminate redundancy, favor shorter sentences (15-20 words), respect word limits.
**Accuracy**: Exact values, consistent terminology, distinguish observations from interpretations.
**Objectivity**: No bias, avoid overstating, acknowledge conflicting evidence, neutral tone.

### 7. Writing Process: Outline to Prose

**Stage 1: Create Section Outlines**
1. Use research-lookup to gather literature
2. Create structured outline with bullet points (main arguments, key studies, data points, logical flow)
3. These bullets are scaffolding, NOT the final manuscript

**Stage 2: Convert to Full Paragraphs**
1. Transform bullets into complete sentences
2. Add transitions (however, moreover, in contrast)
3. Integrate citations naturally within sentences
4. Expand with context bullet points omit
5. Ensure logical flow and vary sentence structure

**Lists are acceptable ONLY in**: Methods (inclusion/exclusion criteria, materials), Supplementary Materials. **Never in**: Abstract, Introduction, Results, Discussion, Conclusions.

### 8. Professional Report Formatting

For non-journal documents (research reports, white papers, grant reports), use `scientific_report.sty` LaTeX style package. For journal manuscripts and conference papers, use the `venue-templates` skill instead.

**Key features**: Helvetica fonts, professional color scheme, box environments (`keyfindings`, `methodology`, `recommendations`, `limitations`), alternating-row tables, scientific notation commands (`\pvalue{}`, `\CI{}{}`, `\effectsize{}{}`, `\meansd{}{}`).

```latex
\documentclass[11pt,letterpaper]{report}
\usepackage{scientific_report}
\begin{document}
\makereporttitle{Title}{Subtitle}{Author}{Institution}{Date}
% Content here
\end{document}
```

Compile with XeLaTeX: `xelatex report.tex`

### 9. Journal-Specific Formatting

Follow author guidelines for structure, length, citation style, figure specs, required statements (funding, conflicts, data availability, ethical approval), and word limits.

### 10. Common Pitfalls

**Top Rejection Reasons**: Inappropriate statistics, over-interpretation, poorly described methods, small/biased samples, poor writing, inadequate literature review, unclear figures, failure to follow reporting guidelines.

**Writing Issues**: Mixed tenses (past for methods/results, present for established facts), excessive jargon, disrupted logical flow, missing transitions, inconsistent notation.

## Manuscript Development Workflow

**Stage 1 - Planning**: Identify target journal, determine reporting guideline, outline structure, plan figures/tables.

**Stage 2 - Drafting** (two-stage per section): Start with figures/tables, then Methods, Results, Discussion, Introduction, Abstract, Title. For each: outline with research-lookup first, then convert to prose.

**Stage 3 - Revision**: Check logical flow, verify consistency, ensure figures are self-explanatory, confirm reporting guideline adherence, verify citations, check word counts, proofread.

**Stage 4 - Final Preparation**: Format per journal, prepare supplementary materials, write cover letter, complete submission checklists.

## Integration

- **venue-templates**: Venue-specific writing styles (Nature/Science, Cell Press, medical journals, ML/CS conferences)
- **scientific_report.sty**: Professional reports, white papers, technical documents
- **Data/statistical analysis skills**: Generating results to report

## References

- `references/imrad_structure.md`: IMRAD format guide
- `references/citation_styles.md`: Citation style guides
- `references/figures_tables.md`: Data visualization best practices
- `references/reporting_guidelines.md`: Study-specific reporting standards
- `references/writing_principles.md`: Scientific communication principles
- `references/professional_report_formatting.md`: Report styling guide
- `assets/scientific_report.sty`: LaTeX style package
- `assets/scientific_report_template.tex`: Complete template
