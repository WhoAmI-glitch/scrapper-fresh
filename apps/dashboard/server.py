#!/usr/bin/env python3
"""Multi-Agent System Dashboard — FastAPI backend.

Reads .claude/state/ artifacts and serves a control panel UI.
Run: uvicorn apps.dashboard.server:app --reload --port 8077
"""
import json
import subprocess
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# Resolve project root (two levels up from this file)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_DIR = PROJECT_ROOT / ".claude" / "state"
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"
SCHEMAS_DIR = PROJECT_ROOT / ".claude" / "schemas"
SKILLS_DIR = PROJECT_ROOT / ".claude" / "skills"
COMMANDS_DIR = PROJECT_ROOT / ".claude" / "commands"
QUALITY_DIR = PROJECT_ROOT / ".claude" / "quality"
DASHBOARD_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Multi-Agent System Dashboard", version="1.0.0")


# --- Helpers ---

def load_json_dir(dirpath: Path) -> list[dict]:
    """Load all JSON files from a directory."""
    results = []
    if not dirpath.is_dir():
        return results
    for f in sorted(dirpath.glob("*.json")):
        if f.name == ".gitkeep":
            continue
        try:
            results.append(json.loads(f.read_text()))
        except (json.JSONDecodeError, OSError):
            results.append({"id": f.stem, "_error": "invalid JSON"})
    return results


def count_files(dirpath: Path, pattern: str = "*.json") -> int:
    if not dirpath.is_dir():
        return 0
    return len([f for f in dirpath.glob(pattern) if f.name != ".gitkeep"])


# --- API Routes ---

@app.get("/api/overview")
def get_overview():
    """System overview: counts and high-level stats."""
    tasks = load_json_dir(STATE_DIR / "tasks")
    status_counts = {}
    for t in tasks:
        s = t.get("status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1

    registry_path = AGENTS_DIR / "REGISTRY.json"
    agent_count = 0
    if registry_path.exists():
        try:
            reg = json.loads(registry_path.read_text())
            agent_count = len(reg.get("agents", []))
        except (json.JSONDecodeError, OSError):
            pass

    s_tier = count_files(SKILLS_DIR / "s-tier" , "*/SKILL.md") if (SKILLS_DIR / "s-tier").is_dir() else 0
    a_tier = count_files(SKILLS_DIR / "a-tier", "*/SKILL.md") if (SKILLS_DIR / "a-tier").is_dir() else 0
    # Count skills via find since they're in subdirectories
    s_tier = len(list((SKILLS_DIR / "s-tier").rglob("SKILL.md"))) if (SKILLS_DIR / "s-tier").is_dir() else 0
    a_tier = len(list((SKILLS_DIR / "a-tier").rglob("SKILL.md"))) if (SKILLS_DIR / "a-tier").is_dir() else 0

    return {
        "tasks": {
            "total": len(tasks),
            "by_status": status_counts,
        },
        "agents": agent_count,
        "skills": {"s_tier": s_tier, "a_tier": a_tier, "total": s_tier + a_tier},
        "commands": len(list(COMMANDS_DIR.glob("*.md"))) if COMMANDS_DIR.is_dir() else 0,
        "schemas": len(list(SCHEMAS_DIR.glob("*.schema.json"))) if SCHEMAS_DIR.is_dir() else 0,
        "artifacts": {
            "handoffs": count_files(STATE_DIR / "handoffs"),
            "findings": count_files(STATE_DIR / "findings"),
            "decisions": count_files(STATE_DIR / "decisions"),
            "proposals": count_files(STATE_DIR / "proposals"),
            "quality_reports": count_files(QUALITY_DIR / "reports"),
        },
    }


@app.get("/api/tasks")
def get_tasks(status: str | None = None):
    """List all tasks, optionally filtered by status."""
    tasks = load_json_dir(STATE_DIR / "tasks")
    if status:
        tasks = [t for t in tasks if t.get("status") == status]
    return tasks


@app.get("/api/tasks/{task_id}")
def get_task(task_id: str):
    """Get a single task by ID."""
    path = STATE_DIR / "tasks" / f"{task_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return json.loads(path.read_text())


@app.get("/api/handoffs")
def get_handoffs():
    return load_json_dir(STATE_DIR / "handoffs")


@app.get("/api/findings")
def get_findings():
    return load_json_dir(STATE_DIR / "findings")


@app.get("/api/decisions")
def get_decisions():
    return load_json_dir(STATE_DIR / "decisions")


@app.get("/api/proposals")
def get_proposals():
    return load_json_dir(STATE_DIR / "proposals")


@app.get("/api/quality-reports")
def get_quality_reports():
    return load_json_dir(QUALITY_DIR / "reports")


@app.get("/api/agents")
def get_agents():
    """List all agents from REGISTRY.json."""
    registry_path = AGENTS_DIR / "REGISTRY.json"
    if not registry_path.exists():
        return []
    try:
        reg = json.loads(registry_path.read_text())
        return reg.get("agents", [])
    except (json.JSONDecodeError, OSError):
        raise HTTPException(status_code=500, detail="Failed to read registry")


@app.get("/api/agent-utilization")
def get_agent_utilization():
    """Show how many tasks each agent has been assigned."""
    tasks = load_json_dir(STATE_DIR / "tasks")
    utilization: dict[str, dict] = {}
    for t in tasks:
        agent = t.get("assigned_agent") or "unassigned"
        if agent not in utilization:
            utilization[agent] = {"total": 0, "by_status": {}}
        utilization[agent]["total"] += 1
        s = t.get("status", "unknown")
        utilization[agent]["by_status"][s] = utilization[agent]["by_status"].get(s, 0) + 1
    return utilization


@app.get("/api/decision-audit")
def get_decision_audit():
    """Decision audit trail — all decisions sorted by date."""
    decisions = load_json_dir(STATE_DIR / "decisions")
    decisions.sort(key=lambda d: d.get("created_at", ""), reverse=True)
    return decisions


@app.get("/api/health")
def get_health():
    """Run system health check and return results."""
    health_script = PROJECT_ROOT / "scripts" / "system-health.sh"
    if not health_script.exists():
        return {"status": "unknown", "message": "system-health.sh not found"}
    try:
        result = subprocess.run(
            ["bash", str(health_script)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT),
        )
        # Strip ANSI color codes
        import re
        clean_output = re.sub(r'\033\[[0-9;]*m', '', result.stdout)
        return {
            "status": "healthy" if result.returncode == 0 else "unhealthy",
            "return_code": result.returncode,
            "output": clean_output,
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "message": "Health check timed out"}


# --- Static UI ---

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    """Serve the dashboard UI."""
    index_path = DASHBOARD_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text())
    return HTMLResponse(content="<h1>Dashboard index.html not found</h1>", status_code=500)
