# Command: /cite-source

## Description
Format a citation from provided source information.

## Usage
```
/cite-source "<source details>" [--style harvard|apa|chicago|mla|vancouver|ieee]
```

## Instructions
1. Identify the source type (book, journal, website, report, etc.)
2. Extract all available metadata
3. Default to Harvard style (Regent's standard) unless specified
4. Generate both in-text citation and reference list entry
5. Flag any missing metadata that should be added
6. If a DOI or URL is provided, verify format

## Output Format
```markdown
## Citation: {Short Source Title}

### In-text Citation
{Formatted in-text citation}

### Reference List Entry
{Full formatted reference}

### Style
{Which citation style was used}

### Source Type
{Book / Journal article / Website / Report / etc.}

### Missing Fields
- {Any metadata gaps that should be filled}

### Notes
- {Any style-specific considerations}
- {Alternative forms if applicable, e.g., first citation vs subsequent}
```

## Acceptance Criteria
- [ ] Source type correctly identified
- [ ] In-text citation follows style rules exactly
- [ ] Reference list entry follows style rules exactly
- [ ] Missing metadata is flagged
- [ ] Style-specific formatting applied (italics, punctuation, capitalization)
- [ ] DOI or URL included where applicable
