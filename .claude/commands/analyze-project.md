Analyze the current project thoroughly. Perform these steps in order:

1. **Structure scan**: Map the directory tree, identify key files, and determine the tech stack.
2. **Dependency audit**: Read package manifests (package.json, requirements.txt, etc.) and flag outdated or vulnerable dependencies.
3. **Code quality**: Identify large files, complex functions, missing tests, and inconsistent patterns.
4. **Architecture assessment**: Map the component/module boundaries and data flow. Identify coupling issues.
5. **Documentation gaps**: Check for missing README, incomplete API docs, or undocumented config.

Output a structured report with:
- Tech stack summary
- File structure overview
- Top 5 quality concerns (ranked by severity)
- Top 3 architecture recommendations
- Missing documentation checklist

Use the `systematic-debugging` skill methodology for any issues found.
Do not modify any files. This is a read-only analysis.
