"""Email parsing service -- extracts structured shipment data from emails.

Analyses email subjects and bodies to identify contract references,
vessel names, dates, quantities, and other shipment-relevant information.
Links parsed emails to existing deals and shipments in the database.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from uuid import UUID

import psycopg
from loguru import logger


# Patterns for extracting structured data from email text
_CONTRACT_PATTERN = re.compile(r"CHR-\d{4}-\d{4,}", re.IGNORECASE)
_IMO_PATTERN = re.compile(r"IMO[:\s]*(\d{7})", re.IGNORECASE)
_VESSEL_MV_PATTERN = re.compile(r"(?:MV|M/V|MT|M/T)\s+([A-Za-z][A-Za-z\s]+)", re.IGNORECASE)
_QUANTITY_PATTERN = re.compile(
    r"(\d[\d,]*(?:\.\d+)?)\s*(?:MT|tons?|metric\s*tons?)", re.IGNORECASE
)
_BL_PATTERN = re.compile(r"B/?L[:\s#]*([A-Z0-9\-]+)", re.IGNORECASE)
_DATE_PATTERNS = [
    re.compile(r"\d{4}-\d{2}-\d{2}"),  # ISO format
    re.compile(r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4}"),
    re.compile(r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}"),
]

# Category keywords for email classification
_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "charter": [
        "charter party", "c/p", "fixture", "laycan", "demurrage",
        "freight rate", "hire", "charter agreement",
    ],
    "bol": [
        "bill of lading", "b/l", "bl number", "shipped on board",
        "mate's receipt", "loading confirmation",
    ],
    "notification": [
        "eta", "arrival notice", "departure", "sailed", "berthed",
        "vessel update", "position report", "loading commenced",
    ],
    "broker": [
        "offer", "counter offer", "firm offer", "indicative",
        "cargo available", "tonnage available", "market report",
    ],
}


def parse_shipment_email(
    subject: str,
    body: str,
    sender: str,
) -> dict[str, Any]:
    """Extract structured shipment data from an email.

    Scans the subject and body for contract IDs, vessel names, IMO numbers,
    quantities, bill of lading references, and dates.

    Returns a dict with extracted fields (any may be None if not found).
    """
    full_text = f"{subject}\n{body}"
    parsed: dict[str, Any] = {
        "contract_ids": [],
        "vessel_names": [],
        "imo_numbers": [],
        "quantities_tons": [],
        "bill_of_lading_refs": [],
        "dates": [],
        "sender": sender,
    }

    # Contract IDs (e.g. CHR-2026-0042)
    contract_matches = _CONTRACT_PATTERN.findall(full_text)
    parsed["contract_ids"] = list(set(contract_matches))

    # IMO numbers
    imo_matches = _IMO_PATTERN.findall(full_text)
    parsed["imo_numbers"] = list(set(imo_matches))

    # Vessel names (MV Something, M/V Something)
    vessel_matches = _VESSEL_MV_PATTERN.findall(full_text)
    parsed["vessel_names"] = [v.strip() for v in set(vessel_matches)]

    # Quantities in tons
    qty_matches = _QUANTITY_PATTERN.findall(full_text)
    parsed["quantities_tons"] = [
        float(q.replace(",", "")) for q in qty_matches
    ]

    # Bill of lading references
    bl_matches = _BL_PATTERN.findall(full_text)
    parsed["bill_of_lading_refs"] = list(set(bl_matches))

    # Dates
    extracted_dates: list[str] = []
    for pattern in _DATE_PATTERNS:
        matches = pattern.findall(full_text)
        extracted_dates.extend(matches)
    parsed["dates"] = extracted_dates

    logger.debug(
        "Parsed email from {}: contracts={}, vessels={}, imo={}",
        sender,
        parsed["contract_ids"],
        parsed["vessel_names"],
        parsed["imo_numbers"],
    )
    return parsed


def categorize_email(subject: str, body: str) -> str:
    """Classify an email into a category based on keyword matching.

    Returns one of: 'charter', 'bol', 'notification', 'broker', 'other'.
    """
    full_text = f"{subject} {body}".lower()

    # Score each category by keyword hits
    scores: dict[str, int] = {}
    for category, keywords in _CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in full_text)
        if score > 0:
            scores[category] = score

    if not scores:
        return "other"

    # Return the category with the highest score
    best_category = max(scores, key=scores.get)  # type: ignore[arg-type]
    logger.debug("Email categorised as '{}' (scores: {})", best_category, scores)
    return best_category


async def link_email_to_deal(
    conn: psycopg.AsyncConnection,
    email_id: UUID,
    parsed_data: dict[str, Any],
) -> dict[str, UUID | None]:
    """Attempt to link an email to existing deals and shipments.

    Matching strategy (in priority order):
    1. Match by contract_id from parsed data
    2. Match by vessel IMO number
    3. Match by vessel name

    Updates the email record with the matched deal_id and shipment_id.
    Returns a dict with the matched IDs (or None if no match).
    """
    deal_id: UUID | None = None
    shipment_id: UUID | None = None

    # Strategy 1: Match by contract ID
    for contract_id in parsed_data.get("contract_ids", []):
        cursor = await conn.execute(
            "SELECT id FROM deals WHERE contract_id = %s",
            [contract_id],
        )
        row = await cursor.fetchone()
        if row:
            deal_id = row["id"]
            logger.info("Email {} matched to deal {} by contract_id", email_id, deal_id)
            break

    # Strategy 2: Match by IMO number -> vessel -> shipment -> deal
    if deal_id is None:
        for imo in parsed_data.get("imo_numbers", []):
            cursor = await conn.execute(
                """
                SELECT s.id AS shipment_id, s.deal_id
                FROM shipments s
                JOIN vessels v ON s.vessel_id = v.id
                WHERE v.imo_number = %s
                  AND s.status NOT IN ('arrived', 'discharged')
                ORDER BY s.created_at DESC
                LIMIT 1
                """,
                [imo],
            )
            row = await cursor.fetchone()
            if row:
                shipment_id = row["shipment_id"]
                deal_id = row["deal_id"]
                logger.info(
                    "Email {} matched to shipment {} via IMO {}", email_id, shipment_id, imo
                )
                break

    # Strategy 3: Match by vessel name
    if deal_id is None:
        for vessel_name in parsed_data.get("vessel_names", []):
            cursor = await conn.execute(
                """
                SELECT s.id AS shipment_id, s.deal_id
                FROM shipments s
                JOIN vessels v ON s.vessel_id = v.id
                WHERE LOWER(v.name) LIKE LOWER(%s)
                  AND s.status NOT IN ('arrived', 'discharged')
                ORDER BY s.created_at DESC
                LIMIT 1
                """,
                [f"%{vessel_name}%"],
            )
            row = await cursor.fetchone()
            if row:
                shipment_id = row["shipment_id"]
                deal_id = row["deal_id"]
                logger.info(
                    "Email {} matched to shipment {} via vessel name '{}'",
                    email_id,
                    shipment_id,
                    vessel_name,
                )
                break

    # If we found a deal but not a shipment, try to find the active shipment
    if deal_id is not None and shipment_id is None:
        cursor = await conn.execute(
            """
            SELECT id FROM shipments
            WHERE deal_id = %s
              AND status NOT IN ('arrived', 'discharged')
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [str(deal_id)],
        )
        row = await cursor.fetchone()
        if row:
            shipment_id = row["id"]

    # Update the email record with matched references
    await conn.execute(
        """
        UPDATE emails
        SET deal_id = %s, shipment_id = %s
        WHERE id = %s
        """,
        [str(deal_id) if deal_id else None, str(shipment_id) if shipment_id else None, str(email_id)],
    )

    return {"deal_id": deal_id, "shipment_id": shipment_id}


async def store_email(
    conn: psycopg.AsyncConnection,
    *,
    gmail_id: str,
    subject: str,
    sender: str,
    recipients: list[str],
    body_text: str,
    received_at: datetime,
    category: str,
    parsed_data: dict[str, Any],
) -> dict:
    """Store an email record in the database.

    Returns the inserted row.
    """
    import json

    query = """
        INSERT INTO emails (
            gmail_id, subject, sender, recipients, body_text,
            received_at, category, parsed_data
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (gmail_id) DO NOTHING
        RETURNING *
    """
    cursor = await conn.execute(
        query,
        [
            gmail_id,
            subject,
            sender,
            recipients,
            body_text,
            received_at,
            category,
            json.dumps(parsed_data),
        ],
    )
    row = await cursor.fetchone()
    if row is None:
        logger.debug("Email {} already exists, skipping", gmail_id)
        return {}
    logger.info("Stored email {}: '{}'", gmail_id, subject[:60])
    return row
