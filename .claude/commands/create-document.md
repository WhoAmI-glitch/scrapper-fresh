Generate an office document. The user will specify the type and content.

Supported formats:
- **PDF**: Use the `pdf` skill. For reports, invoices, certificates.
- **DOCX**: Use the `docx` skill. For Word documents with formatting.
- **XLSX**: Use the `xlsx` skill. For spreadsheets with formulas and formatting.
- **PPTX**: Use the `pptx` skill. For presentations with layouts and charts.

Steps:

1. **Clarify**: Determine the document type, content structure, and any specific formatting requirements.
2. **Generate**: Create the document using the appropriate skill.
3. **Validate**: Verify the output file exists, is not empty, and opens correctly.
4. **Report**: Tell the user the file path and what was created.

For multi-document workflows (e.g., "create a report with a PDF summary and Excel data appendix"), generate each document separately and list all output files.
