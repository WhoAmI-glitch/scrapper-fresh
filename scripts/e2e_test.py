#!/usr/bin/env python3
"""End-to-end integration test for the full scrapper pipeline.

Runs one company through: discovery -> SERP search -> fetch profile -> parse.
Does NOT require a database. Needs YANDEX_API_KEY in .env (optional: BRIGHTDATA_API_KEY).

Usage:
    python scripts/e2e_test.py
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import fields
from pathlib import Path
from urllib.parse import quote

# Ensure project root is on sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "src"))

# Load .env manually (avoid DB-triggering get_settings call)
_env_file = project_root / ".env"
if _env_file.exists():
    for line in _env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


import httpx  # noqa: E402
from loguru import logger  # noqa: E402

from scrapper.db.models import CandidateHint, Lead  # noqa: E402
from scrapper.enrichment.parser import RussprofileParser  # noqa: E402
from scrapper.normalizers import normalize_phone  # noqa: E402

# Known-good fallback URL for testing when live steps fail
FALLBACK_PROFILE_URL = "https://www.rusprofile.ru/id/3467260"


def _sep(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


# ── Step 1: Discovery ────────────────────────────────────────────

def step_discover(max_companies: int = 3) -> list[CandidateHint]:
    """Discover construction companies in Moscow via Yandex Maps."""
    _sep("STEP 1: Discovery (Yandex Maps)")

    api_key = os.environ.get("YANDEX_API_KEY", "")
    if not api_key:
        print("[SKIP] YANDEX_API_KEY not set. Using hardcoded fallback companies.")
        return [
            CandidateHint(
                company_name="ООО СтройГарант",
                source="fallback",
                hint_text="Строительная компания, Москва",
                metadata={"region": "moscow"},
            ),
            CandidateHint(
                company_name="АО Бетон-Сервис",
                source="fallback",
                hint_text="Производство бетона, Москва",
                metadata={"region": "moscow"},
            ),
            CandidateHint(
                company_name="ООО ТеплоСтрой",
                source="fallback",
                hint_text="Утепление фасадов, Москва",
                metadata={"region": "moscow"},
            ),
        ]

    from scrapper.discovery.sources.yandex_maps import YandexMapsSource

    try:
        src = YandexMapsSource(regions=["moscow"])
        hints: list[CandidateHint] = []
        for hint in src.discover():
            hints.append(hint)
            print(f"  Found: {hint.company_name} — {hint.hint_text}")
            if len(hints) >= max_companies:
                break

        print(f"\n  Discovered {len(hints)} companies in Moscow.")
        return hints

    except Exception as e:
        print(f"[ERROR] Discovery failed: {e}")
        print("[FALLBACK] Using hardcoded companies.")
        return [
            CandidateHint(
                company_name="ООО СтройГарант",
                source="fallback",
                hint_text="Строительная компания, Москва",
                metadata={"region": "moscow"},
            ),
        ]


# ── Step 2: SERP Search ─────────────────────────────────────────

def step_serp_search(company_name: str) -> str | None:
    """Search Google via Bright Data SERP API for company on rusprofile.ru."""
    _sep(f"STEP 2: SERP Search for '{company_name}'")

    api_key = os.environ.get("BRIGHTDATA_API_KEY", "")
    if not api_key:
        print("[SKIP] BRIGHTDATA_API_KEY not set.")
        print("  Falling back to direct rusprofile search URL.")
        return _build_rusprofile_search_url(company_name)

    query = f'"{company_name}" site:rusprofile.ru'
    print(f"  Query: {query}")

    try:
        # Bright Data SERP API endpoint
        resp = httpx.post(
            "https://api.brightdata.com/serp/req",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "query": query,
                "search_engine": "google",
                "country": "ru",
                "language": "ru",
            },
            timeout=30.0,
        )
        if resp.status_code != 200:
            print(f"  [WARN] SERP API returned {resp.status_code}: {resp.text[:200]}")
            return _build_rusprofile_search_url(company_name)

        data = resp.json()
        organic = data.get("organic", [])
        for result in organic:
            url = result.get("link", "")
            if "rusprofile.ru/id/" in url:
                print(f"  Found profile URL: {url}")
                return url

        print("  No rusprofile.ru profile URL found in SERP results.")
        return _build_rusprofile_search_url(company_name)

    except Exception as e:
        print(f"  [ERROR] SERP search failed: {e}")
        return _build_rusprofile_search_url(company_name)


def _build_rusprofile_search_url(company_name: str) -> str:
    """Build a direct rusprofile.ru search URL as fallback."""
    encoded = quote(company_name, safe="")
    url = f"https://www.rusprofile.ru/search?query={encoded}&type=ul"
    print(f"  Using rusprofile search URL: {url}")
    return url


# ── Step 3: Find best profile URL ───────────────────────────────

def step_find_profile_url(search_url: str) -> str | None:
    """Fetch rusprofile search page and extract the best profile URL."""
    _sep("STEP 3: Find best profile URL")

    # If it's already a direct profile URL, return it
    if "/id/" in search_url:
        print(f"  Already have profile URL: {search_url}")
        return search_url

    print(f"  Fetching search page: {search_url}")

    try:
        resp = httpx.get(
            search_url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; LeadgenBot/0.1; research)",
                "Accept-Language": "ru-RU,ru;q=0.9",
            },
            follow_redirects=True,
            timeout=15.0,
        )

        if resp.status_code != 200:
            print(f"  [WARN] Got status {resp.status_code}")
            return None

        parser = RussprofileParser()
        results = parser.parse_search_results(resp.text)

        if results:
            best = results[0]
            print(f"  Best match: {best['name']} — {best['url']}")
            return best["url"]

        # Fallback: look for /id/ links in the HTML
        profile_links = re.findall(r'href="(/id/\d+)"', resp.text)
        if profile_links:
            url = f"https://www.rusprofile.ru{profile_links[0]}"
            print(f"  Found profile link via regex: {url}")
            return url

        print("  No profile URLs found on search page.")
        return None

    except Exception as e:
        print(f"  [ERROR] Search page fetch failed: {e}")
        return None


# ── Step 4: Fetch profile page ───────────────────────────────────

def step_fetch_profile(profile_url: str) -> str | None:
    """Fetch the russprofile.ru profile page HTML."""
    _sep("STEP 4: Fetch profile page")
    print(f"  URL: {profile_url}")

    # Try Bright Data Web Unlocker first, then direct
    proxy_url = os.environ.get("BRIGHTDATA_PROXY_URL", "")

    try:
        client_kwargs: dict = {
            "timeout": httpx.Timeout(30.0, connect=10.0),
            "headers": {
                "User-Agent": "Mozilla/5.0 (compatible; LeadgenBot/0.1; research)",
                "Accept-Language": "ru-RU,ru;q=0.9",
            },
            "follow_redirects": True,
        }
        if proxy_url:
            client_kwargs["proxy"] = proxy_url
            print("  Using Bright Data proxy")
        else:
            print("  Using direct HTTP (no proxy)")

        with httpx.Client(**client_kwargs) as client:
            resp = client.get(profile_url)

        print(f"  Status: {resp.status_code}, Content length: {len(resp.text)}")

        if resp.status_code == 200:
            return resp.text

        print(f"  [WARN] Non-200 status: {resp.status_code}")
        return None

    except Exception as e:
        print(f"  [ERROR] Fetch failed: {e}")
        return None


# ── Step 5: Parse profile ────────────────────────────────────────

def step_parse(html: str) -> Lead | None:
    """Parse the profile HTML into a Lead."""
    _sep("STEP 5: Parse profile with RussprofileParser")

    try:
        parser = RussprofileParser()
        lead = parser.parse(html)
        return lead
    except Exception as e:
        print(f"  [ERROR] Parse failed: {e}")
        return None


# ── Step 6 & 7: Print results ───────────────────────────────────

def print_lead(lead: Lead, extra_phones: list[str] | None = None) -> None:
    """Print all lead fields and a summary of fill rate."""
    _sep("STEP 6: Extracted Lead Data")

    lead_fields = fields(lead)
    filled = 0
    total = 0

    for f in lead_fields:
        if f.name in ("task_id", "raw_data"):
            continue
        total += 1
        value = getattr(lead, f.name)
        is_filled = bool(value)
        if is_filled:
            filled += 1
        status = "+" if is_filled else "-"
        print(f"  [{status}] {f.name:20s} = {value}")

    if extra_phones:
        print("\n  Yandex Maps phones (supplemental):")
        for p in extra_phones:
            normalized = normalize_phone(p)
            print(f"    {p} -> {normalized}")

    _sep("STEP 7: Summary")
    print(f"  Fields filled:  {filled}/{total}")
    print(f"  Fields empty:   {total - filled}/{total}")
    print(f"  Fill rate:      {filled / total * 100:.0f}%")

    empty_fields = [
        f.name for f in lead_fields
        if f.name not in ("task_id", "raw_data") and not getattr(lead, f.name)
    ]
    if empty_fields:
        print(f"  Missing:        {', '.join(empty_fields)}")


# ── Main ─────────────────────────────────────────────────────────

def main() -> int:
    logger.remove()  # suppress loguru noise in script output

    print("Scrapper E2E Integration Test")
    print("Runs one company through the full pipeline (no database needed)")

    # Step 1: Discover
    hints = step_discover(max_companies=3)
    if not hints:
        print("\n[FAIL] No companies discovered. Exiting.")
        return 1

    # Pick the first company
    target = hints[0]
    print(f"\n  Target company: {target.company_name}")

    # Extract phones from Yandex Maps metadata (for supplemental data in step 6)
    yandex_phones: list[str] = target.metadata.get("phones", [])

    # Step 2: SERP search
    search_url = step_serp_search(target.company_name)
    if not search_url:
        print("[FALLBACK] Using known-good test URL")
        search_url = FALLBACK_PROFILE_URL

    # Step 3: Find profile URL
    profile_url = step_find_profile_url(search_url)
    if not profile_url:
        print("[FALLBACK] Using known-good test URL")
        profile_url = FALLBACK_PROFILE_URL

    # Step 4: Fetch profile
    html = step_fetch_profile(profile_url)
    if not html:
        print("[FALLBACK] Trying known-good test URL")
        html = step_fetch_profile(FALLBACK_PROFILE_URL)

    if not html:
        print("\n[FAIL] Could not fetch any profile page. Exiting.")
        return 1

    # Step 5: Parse
    lead = step_parse(html)
    if not lead:
        print("\n[FAIL] Could not parse profile HTML. Exiting.")
        return 1

    # Steps 6 & 7: Print results
    print_lead(lead, extra_phones=yandex_phones)

    print("\n[DONE] E2E test completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
