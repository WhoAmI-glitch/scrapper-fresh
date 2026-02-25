"""PostgreSQL-backed task queue using SELECT FOR UPDATE SKIP LOCKED."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from scrapper.db.models import CandidateHint, EnrichmentTask, Lead

if TYPE_CHECKING:
    from psycopg import Connection


def save_candidate(conn: Connection, hint: CandidateHint) -> int | None:
    """Insert a candidate (ignore duplicates). Return candidate id or None."""
    row = conn.execute(
        """
        INSERT INTO candidates (company_name, source, hint_text, metadata)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (source, company_name) DO NOTHING
        RETURNING id
        """,
        (hint.company_name, hint.source, hint.hint_text, json.dumps(hint.metadata)),
    ).fetchone()
    if row:
        return row["id"]  # type: ignore[call-overload]
    return None


def create_enrichment_task(conn: Connection, candidate_id: int) -> int:
    """Create an enrichment task for a candidate. Return task id."""
    row = conn.execute(
        """
        INSERT INTO enrichment_tasks (candidate_id)
        VALUES (%s)
        RETURNING id
        """,
        (candidate_id,),
    ).fetchone()
    assert row is not None  # RETURNING always returns for INSERT
    return row["id"]  # type: ignore[call-overload]


def claim_tasks(conn: Connection, batch_size: int = 10) -> list[EnrichmentTask]:
    """Claim a batch of NEW tasks using row-level locking."""
    rows = conn.execute(
        """
        UPDATE enrichment_tasks
        SET state = 'FETCHING',
            attempts = attempts + 1,
            updated_at = NOW()
        WHERE id IN (
            SELECT et.id
            FROM enrichment_tasks et
            WHERE et.state = 'NEW'
            ORDER BY et.created_at ASC
            LIMIT %s
            FOR UPDATE SKIP LOCKED
        )
        RETURNING id, candidate_id, state, attempts, profile_url, error_message,
                  created_at, updated_at
        """,
        (batch_size,),
    ).fetchall()

    tasks = []
    for r in rows:
        # Fetch company name from candidates
        cand = conn.execute(
            "SELECT company_name FROM candidates WHERE id = %s", (r["candidate_id"],)
        ).fetchone()
        tasks.append(
            EnrichmentTask(
                id=r["id"],
                candidate_id=r["candidate_id"],
                state=r["state"],
                attempts=r["attempts"],
                profile_url=r["profile_url"],
                error_message=r["error_message"],
                company_name=cand["company_name"] if cand else "",
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
        )
    return tasks


def update_task_state(
    conn: Connection,
    task_id: int,
    state: str,
    *,
    profile_url: str | None = None,
    error_message: str | None = None,
) -> None:
    """Update a task's state and optional fields."""
    conn.execute(
        """
        UPDATE enrichment_tasks
        SET state = %s,
            profile_url = COALESCE(%s, profile_url),
            error_message = COALESCE(%s, error_message),
            updated_at = NOW()
        WHERE id = %s
        """,
        (state, profile_url, error_message, task_id),
    )


def save_lead(conn: Connection, lead: Lead) -> None:
    """Upsert a lead record keyed on task_id."""

    conn.execute(
        """
        INSERT INTO leads (
            task_id, company_name, inn, ogrn, kpp, address, ceo,
            phone, email, website, revenue, employees, status,
            okved, registration_date, raw_data
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s
        )
        ON CONFLICT (task_id) DO UPDATE SET
            company_name = EXCLUDED.company_name,
            inn = EXCLUDED.inn,
            ogrn = EXCLUDED.ogrn,
            kpp = EXCLUDED.kpp,
            address = EXCLUDED.address,
            ceo = EXCLUDED.ceo,
            phone = EXCLUDED.phone,
            email = EXCLUDED.email,
            website = EXCLUDED.website,
            revenue = EXCLUDED.revenue,
            employees = EXCLUDED.employees,
            status = EXCLUDED.status,
            okved = EXCLUDED.okved,
            registration_date = EXCLUDED.registration_date,
            raw_data = EXCLUDED.raw_data,
            updated_at = NOW()
        """,
        (
            lead.task_id, lead.company_name, lead.inn, lead.ogrn, lead.kpp,
            lead.address, lead.ceo, lead.phone, lead.email, lead.website,
            lead.revenue, lead.employees, lead.status, lead.okved,
            lead.registration_date,
            json.dumps(lead.raw_data) if lead.raw_data else None,
        ),
    )


def get_candidate_metadata(conn: Connection, candidate_id: int) -> dict:
    """Return the metadata dict for a candidate, or empty dict."""
    row = conn.execute(
        "SELECT metadata FROM candidates WHERE id = %s",
        (candidate_id,),
    ).fetchone()
    if row and row["metadata"]:
        raw = row["metadata"]
        if isinstance(raw, str):
            return json.loads(raw)
        return dict(raw)
    return {}


def get_queue_stats(conn: Connection) -> dict[str, int]:
    """Return task counts by state."""
    rows = conn.execute(
        "SELECT state, COUNT(*) as cnt FROM enrichment_tasks GROUP BY state"
    ).fetchall()
    return {r["state"]: r["cnt"] for r in rows}


def get_leads_count(conn: Connection) -> int:
    """Return total number of leads."""
    row = conn.execute("SELECT COUNT(*) as cnt FROM leads").fetchone()
    return row["cnt"] if row else 0


def get_candidates_count(conn: Connection) -> int:
    """Return total number of candidates."""
    row = conn.execute("SELECT COUNT(*) as cnt FROM candidates").fetchone()
    return row["cnt"] if row else 0
