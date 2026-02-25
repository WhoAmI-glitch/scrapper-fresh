"""Data models (plain dataclasses) for the pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass
class CandidateHint:
    """A company name discovered by a source, before enrichment."""

    company_name: str
    source: str
    hint_text: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class EnrichmentTask:
    """A task in the enrichment queue."""

    id: int
    candidate_id: int
    state: str = "NEW"
    attempts: int = 0
    profile_url: str | None = None
    error_message: str | None = None
    company_name: str = ""  # joined from candidates table
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class Lead:
    """An enriched company lead (final output)."""

    task_id: int
    company_name: str
    inn: str | None = None
    ogrn: str | None = None
    kpp: str | None = None
    address: str | None = None
    ceo: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    revenue: str | None = None
    employees: str | None = None
    status: str | None = None
    okved: str | None = None
    registration_date: str | None = None
    raw_data: dict | None = None


@dataclass
class RawPageMeta:
    """Metadata about a saved HTML snapshot."""

    task_id: int
    url: str
    file_path: str
    http_status: int | None = None
    content_length: int | None = None
