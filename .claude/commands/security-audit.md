---
description: "Run a structured security audit across the codebase with remediation"
argument-hint: "<target path or description> [--depth quick|standard|comprehensive] [--compliance owasp|soc2|pci-dss]"
---

# Security Audit Orchestrator

Multi-phase workflow coordinating security-auditor, qa-reviewer, devils-advocate, and backend-builder agents for security scanning, analysis, and remediation.

## Behavioral Rules

1. Execute phases in strict order. Do not skip or merge steps.
2. Write each phase output to `.claude/state/workflows/security-audit/` before starting the next phase.
3. Stop at every PHASE CHECKPOINT and wait for explicit user approval.
4. On any failure, halt immediately and present the error.

## Pre-flight

Check if `.claude/state/workflows/security-audit/state.json` exists:
- If `status: "in_progress"`: display current phase and offer to resume or start fresh.
- If `status: "complete"`: offer to archive and start fresh.

Initialize `.claude/state/workflows/security-audit/state.json`:
```json
{
  "target": "$ARGUMENTS",
  "status": "in_progress",
  "depth": "standard",
  "compliance": [],
  "current_phase": "scan",
  "completed_phases": [],
  "files_created": [],
  "started_at": "ISO_TIMESTAMP",
  "last_updated": "ISO_TIMESTAMP"
}
```

Parse `$ARGUMENTS` for `--depth` and `--compliance` flags.

---

## Phase 1: Scan

### Step 1 -- Static Analysis

Dispatch to **security-auditor** agent: perform static application security testing across the target codebase.

Scan for:
- Injection vulnerabilities (SQL, command, XSS, path traversal)
- Hardcoded secrets and credentials
- Insecure deserialization
- Insecure random number generation
- Framework-specific misconfigurations (CSRF exemptions, debug modes, weak keys)

Run available tools: semgrep (`--config=auto --config=p/security-audit`), bandit (Python), eslint-security (JS/TS), or language-appropriate equivalents.

Write findings to `.claude/state/workflows/security-audit/01-static-analysis.md`.

### Step 2 -- Dependency Audit

Dispatch to **security-auditor** agent: audit all dependency manifests (package.json, requirements.txt, go.mod, Cargo.toml, etc.) for known vulnerabilities using `npm audit`, `pip-audit`, `govulncheck`, or equivalents.

Flag: outdated packages, CVEs by severity, transitive dependency risks, license compliance issues.

Write findings to `.claude/state/workflows/security-audit/02-dependencies.md`.

### Step 3 -- Configuration and Infrastructure Review

Dispatch to **security-auditor** agent: review configuration files, environment handling, deployment configs, and infrastructure-as-code for security issues.

Check: TLS configuration, CORS policies, authentication middleware, rate limiting, security headers, secrets management, container security, network policies.

Write findings to `.claude/state/workflows/security-audit/03-config-review.md`.

Update `state.json`: `current_phase: "checkpoint-1"`.

### PHASE CHECKPOINT 1

Present scan summary: total findings by severity across all three scans. Options:
1. Approve -- proceed to analysis
2. Adjust scope -- rescan specific areas
3. Pause -- save progress and stop

---

## Phase 2: Analyze

### Step 4 -- Risk Analysis and Prioritization

Dispatch to **devils-advocate** agent: review all scan findings, eliminate false positives, assess exploitability, and prioritize by risk.

For each confirmed finding, document: severity (Critical/High/Medium/Low), CVSS estimate, attack vector, exploitability, business impact, affected component, and CWE/OWASP classification.

Write to `.claude/state/workflows/security-audit/04-risk-analysis.md`.

### Step 5 -- Compliance Mapping

If `--compliance` flags were provided, dispatch to **analyst** agent: map confirmed findings to the specified compliance frameworks (OWASP Top 10, SOC 2, PCI-DSS). Identify gaps and required controls.

Write to `.claude/state/workflows/security-audit/05-compliance.md`. Skip if no compliance flags.

Update `state.json`: `current_phase: "checkpoint-2"`.

### PHASE CHECKPOINT 2

Present prioritized risk report and compliance gaps. Options:
1. Approve -- proceed to remediation
2. Request deeper analysis on specific findings
3. Pause -- save progress and stop

---

## Phase 3: Report

### Step 6 -- Audit Report

Dispatch to **qa-reviewer** agent: compile a structured audit report combining all findings, risk analysis, and compliance mapping.

Report structure:
- Executive summary (risk score 0-100, critical counts)
- Findings by severity with evidence and locations
- Compliance status (if applicable)
- Remediation priorities ranked by risk-to-effort ratio

Write to `.claude/state/workflows/security-audit/06-audit-report.md`.

---

## Phase 4: Remediate

### Step 7 -- Fix Implementation

Dispatch to **backend-builder** agent: implement fixes for Critical and High severity findings. For each fix: apply the change, verify it does not break existing tests, document the remediation.

Use `systematic-debugging` skill if fixes introduce regressions.

Write fix summary to `.claude/state/workflows/security-audit/07-remediations.md`.

### Step 8 -- Verification

Dispatch to **qa-reviewer** agent: re-run scans from Phase 1 against remediated code. Confirm Critical and High findings are resolved. Run existing test suite to verify no regressions.

Write verification results to `.claude/state/workflows/security-audit/08-verification.md`.

Run `.claude/quality/scripts/validate.sh` against all artifacts if available.

Update `state.json`: `current_phase: "checkpoint-3"`.

### PHASE CHECKPOINT 3

Present remediation results: findings fixed, findings remaining, test status. Options:
1. Accept -- finalize audit
2. Continue remediation -- address Medium findings
3. Pause -- save progress and stop

---

## Completion

Update `state.json`: `status: "complete"`, `last_updated: ISO_TIMESTAMP`.

Present summary:
- Static Analysis: `.claude/state/workflows/security-audit/01-static-analysis.md`
- Dependencies: `.claude/state/workflows/security-audit/02-dependencies.md`
- Config Review: `.claude/state/workflows/security-audit/03-config-review.md`
- Risk Analysis: `.claude/state/workflows/security-audit/04-risk-analysis.md`
- Compliance: `.claude/state/workflows/security-audit/05-compliance.md`
- Audit Report: `.claude/state/workflows/security-audit/06-audit-report.md`
- Remediations: `.claude/state/workflows/security-audit/07-remediations.md`
- Verification: `.claude/state/workflows/security-audit/08-verification.md`

Next steps: review remaining Medium/Low findings, schedule follow-up audit, update security policies.
