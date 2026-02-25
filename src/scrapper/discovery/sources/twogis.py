"""2GIS Catalog API discovery source for construction companies."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from scrapper.config import get_settings
from scrapper.db.models import CandidateHint
from scrapper.discovery.base import DiscoverySource

if TYPE_CHECKING:
    from collections.abc import Iterator

API_URL = "https://catalog.api.2gis.com/3.0/items"

# 2GIS region IDs for major Russian cities
REGION_IDS: dict[str, int] = {
    "moscow": 32,
    "spb": 2,
    "novosibirsk": 2,  # Novosibirsk region
    "ekaterinburg": 7,
    "kazan": 12,
    "nizhny_novgorod": 11,
    "krasnoyarsk": 19,
    "chelyabinsk": 8,
    "samara": 14,
    "rostov": 16,
}

# City center coordinates (lon, lat) for point-based search
CITY_CENTERS: dict[str, tuple[float, float]] = {
    "moscow": (37.6173, 55.7558),
    "spb": (30.3351, 59.9343),
    "novosibirsk": (82.9346, 55.0084),
    "ekaterinburg": (60.6122, 56.8389),
    "kazan": (49.1221, 55.7887),
    "nizhny_novgorod": (43.9361, 56.2965),
    "krasnoyarsk": (92.8932, 56.0153),
    "chelyabinsk": (61.4291, 55.1644),
    "samara": (50.1500, 53.1959),
    "rostov": (39.7015, 47.2357),
}

SEARCH_QUERIES = [
    "строительная компания",
    "строительные материалы",
]

PAGE_SIZE = 50
MAX_PAGES = 10  # 500 results max per query
MIN_REQUEST_INTERVAL = 0.1  # 10 RPS max


class TwoGisSource(DiscoverySource):
    """Discover construction companies via 2GIS Catalog API.

    Searches for construction-related companies across major Russian cities
    using the 2GIS public API.
    """

    def __init__(self, regions: list[str] | None = None) -> None:
        super().__init__(source_name="twogis")
        settings = get_settings()
        if not settings.twogis_api_key:
            msg = (
                "TWOGIS_API_KEY environment variable is required "
                "for twogis discovery source"
            )
            raise ValueError(msg)
        self._api_key = settings.twogis_api_key
        self._seen_names: set[str] = set()
        self._last_request_time = 0.0

        if regions is None:
            self._regions = list(CITY_CENTERS.keys())
        else:
            unknown = [r for r in regions if r not in CITY_CENTERS]
            if unknown:
                msg = f"Unknown regions: {unknown}. Valid: {list(CITY_CENTERS.keys())}"
                raise ValueError(msg)
            self._regions = regions

    def discover(self) -> Iterator[CandidateHint]:
        """Yield construction company candidates from 2GIS."""
        for region_slug in self._regions:
            lon, lat = CITY_CENTERS[region_slug]
            for query in SEARCH_QUERIES:
                logger.info(f"2GIS: searching '{query}' in {region_slug}")
                yield from self._search_paginated(query, lon, lat, region_slug)

    def _search_paginated(
        self,
        query: str,
        lon: float,
        lat: float,
        region_slug: str,
    ) -> Iterator[CandidateHint]:
        """Paginate through 2GIS search results."""
        for page in range(1, MAX_PAGES + 1):
            data = self._fetch_page(query, lon, lat, page)
            if data is None:
                return

            items = data.get("result", {}).get("items", [])
            if not items:
                return

            for item in items:
                hint = self._parse_item(item, region_slug)
                if hint is not None:
                    yield hint

            total = data.get("result", {}).get("total", 0)
            if page * PAGE_SIZE >= total:
                return

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def _fetch_page(
        self,
        query: str,
        lon: float,
        lat: float,
        page: int,
    ) -> dict[str, Any] | None:
        """Fetch one page of results from 2GIS API."""
        self._rate_limit()

        params: dict[str, str | int] = {
            "key": self._api_key,
            "q": query,
            "type": "branch",
            "page": page,
            "page_size": PAGE_SIZE,
            "point": f"{lon},{lat}",
            "radius": 50000,
            "fields": "items.contact_groups,items.org",
            "locale": "ru_RU",
        }

        try:
            resp = httpx.get(API_URL, params=params, timeout=15.0)
            if resp.status_code == 403:
                logger.error("2GIS API returned 403 — invalid or expired API key")
                return None
            resp.raise_for_status()
            result: dict[str, Any] = resp.json()
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"2GIS API HTTP error: {e.response.status_code}")
            raise
        except httpx.RequestError as e:
            logger.error(f"2GIS API request error: {e}")
            raise

    def _parse_item(
        self, item: dict[str, Any], region_slug: str
    ) -> CandidateHint | None:
        """Extract a CandidateHint from a 2GIS item."""
        # Get company name from org or item name
        org = item.get("org", {})
        name = org.get("name", "") or item.get("name", "")
        name = name.strip()
        if not name:
            return None

        name_lower = name.lower()
        if name_lower in self._seen_names:
            return None
        self._seen_names.add(name_lower)

        # Extract address
        address_name = item.get("address_name", "")
        full_address = item.get("full_address_name", "")
        address = full_address or address_name

        # Extract rubrics (categories)
        rubrics = [r.get("name", "") for r in item.get("rubrics", []) if r.get("name")]

        # Extract phones from contact groups
        phones: list[str] = []
        for group in item.get("contact_groups", []):
            for contact in group.get("contacts", []):
                if contact.get("type") == "phone":
                    phone_val = contact.get("value", "")
                    if phone_val:
                        phones.append(phone_val)

        # Extract website
        website = ""
        for group in item.get("contact_groups", []):
            for contact in group.get("contacts", []):
                if contact.get("type") == "website":
                    website = contact.get("url", "") or contact.get("value", "")
                    break
            if website:
                break

        # Coordinates
        point = item.get("point", {})

        # Build hint text
        hint_parts = []
        if rubrics:
            hint_parts.append(", ".join(rubrics[:3]))
        if address:
            hint_parts.append(address)
        hint_text = " — ".join(hint_parts)

        metadata: dict[str, Any] = {"region": region_slug, "source_api": "2gis"}
        if point:
            metadata["lon"] = point.get("lon")
            metadata["lat"] = point.get("lat")
        if phones:
            metadata["phones"] = phones
        if website:
            metadata["url"] = website
        if rubrics:
            metadata["rubrics"] = rubrics
        if address:
            metadata["address"] = address

        return CandidateHint(
            company_name=name,
            source=self.source_name,
            hint_text=hint_text,
            metadata=metadata,
        )

    def _rate_limit(self) -> None:
        """Enforce minimum interval between requests."""
        now = time.monotonic()
        elapsed = now - self._last_request_time
        if elapsed < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.monotonic()
