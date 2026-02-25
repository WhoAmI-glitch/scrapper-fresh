"""Yandex Maps Places API discovery source for construction companies."""

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

API_URL = "https://search-maps.yandex.ru/v1/"

# (longitude, latitude, span_lon, span_lat)
REGIONS: dict[str, tuple[float, float, float, float]] = {
    "moscow": (37.6173, 55.7558, 0.6, 0.4),
    "spb": (30.3351, 59.9343, 0.5, 0.3),
    "novosibirsk": (82.9346, 55.0084, 0.4, 0.3),
    "ekaterinburg": (60.6122, 56.8389, 0.4, 0.3),
    "kazan": (49.1221, 55.7887, 0.4, 0.3),
    "nizhny_novgorod": (43.9361, 56.2965, 0.4, 0.3),
    "krasnoyarsk": (92.8932, 56.0153, 0.4, 0.3),
    "chelyabinsk": (61.4291, 55.1644, 0.4, 0.3),
    "samara": (50.1500, 53.1959, 0.4, 0.3),
    "rostov": (39.7015, 47.2357, 0.4, 0.3),
}

SEARCH_QUERIES = [
    "строительная компания",
    "строительные материалы",
    "ремонт и строительство",
]

DAILY_REQUEST_LIMIT = 500
PAGE_SIZE = 50
MAX_RESULTS_PER_QUERY = 500
MIN_REQUEST_INTERVAL = 0.02  # 50 RPS max


class YandexMapsSource(DiscoverySource):
    """Discover construction companies via Yandex Maps Places API.

    Free tier allows 500 requests/day. Searches for construction-related
    companies across major Russian cities.
    """

    def __init__(self, regions: list[str] | None = None) -> None:
        super().__init__(source_name="yandex_maps")
        settings = get_settings()
        if not settings.yandex_api_key:
            msg = (
                "YANDEX_API_KEY environment variable is required "
                "for yandex_maps discovery source"
            )
            raise ValueError(msg)
        self._api_key = settings.yandex_api_key
        self._seen_names: set[str] = set()
        self._request_count = 0
        self._last_request_time = 0.0

        if regions is None:
            self._regions = list(REGIONS.keys())
        else:
            unknown = [r for r in regions if r not in REGIONS]
            if unknown:
                msg = f"Unknown regions: {unknown}. Valid: {list(REGIONS.keys())}"
                raise ValueError(msg)
            self._regions = regions

    def discover(self) -> Iterator[CandidateHint]:
        """Yield construction company candidates from Yandex Maps."""
        for region_slug in self._regions:
            lon, lat, span_lon, span_lat = REGIONS[region_slug]
            for query in SEARCH_QUERIES:
                if self._request_count >= DAILY_REQUEST_LIMIT:
                    logger.warning(
                        f"Daily request limit ({DAILY_REQUEST_LIMIT}) reached, "
                        "stopping discovery"
                    )
                    return
                logger.info(
                    f"Searching '{query}' in {region_slug} "
                    f"(requests used: {self._request_count})"
                )
                yield from self._search_paginated(
                    query, lon, lat, span_lon, span_lat, region_slug
                )

    def _search_paginated(
        self,
        query: str,
        lon: float,
        lat: float,
        span_lon: float,
        span_lat: float,
        region_slug: str,
    ) -> Iterator[CandidateHint]:
        """Paginate through search results for a single query+region."""
        skip = 0
        while skip < MAX_RESULTS_PER_QUERY:
            if self._request_count >= DAILY_REQUEST_LIMIT:
                return

            data = self._fetch_page(query, lon, lat, span_lon, span_lat, skip)
            if data is None:
                return

            features = data.get("features", [])
            if not features:
                return

            for feature in features:
                hint = self._parse_feature(feature, region_slug)
                if hint is not None:
                    yield hint

            total = _get_total_found(data)
            skip += PAGE_SIZE
            if total is not None and skip >= total:
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
        span_lon: float,
        span_lat: float,
        skip: int,
    ) -> dict[str, Any] | None:
        """Fetch one page of results from the Yandex Maps API."""
        self._rate_limit()
        self._request_count += 1

        params: dict[str, str | int] = {
            "apikey": self._api_key,
            "text": query,
            "type": "biz",
            "lang": "ru_RU",
            "ll": f"{lon},{lat}",
            "spn": f"{span_lon},{span_lat}",
            "results": PAGE_SIZE,
            "skip": skip,
        }

        try:
            resp = httpx.get(API_URL, params=params, timeout=15.0)
            if resp.status_code == 403:
                logger.error("Yandex Maps API returned 403 — invalid or expired API key")
                return None
            resp.raise_for_status()
            result: dict[str, Any] = resp.json()
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"Yandex Maps API HTTP error: {e.response.status_code}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Yandex Maps API request error: {e}")
            raise

    def _parse_feature(
        self, feature: dict[str, Any], region_slug: str
    ) -> CandidateHint | None:
        """Extract a CandidateHint from a GeoJSON feature."""
        properties = feature.get("properties", {})
        company_meta = properties.get("CompanyMetaData", {})

        name = company_meta.get("name", "").strip()
        if not name:
            return None

        # Dedup within this run by normalized name
        name_lower = name.lower()
        if name_lower in self._seen_names:
            return None
        self._seen_names.add(name_lower)

        # Extract metadata
        address = company_meta.get("address", "")
        categories = [
            c.get("name", "") for c in company_meta.get("Categories", [])
        ]
        phones = [
            p.get("formatted", "")
            for p in company_meta.get("Phones", [])
            if p.get("formatted")
        ]
        url = company_meta.get("url", "")

        # Coordinates
        geometry = feature.get("geometry", {})
        coordinates = geometry.get("coordinates", [])

        hint_parts = []
        if categories:
            hint_parts.append(", ".join(categories))
        if address:
            hint_parts.append(address)
        hint_text = " — ".join(hint_parts)

        metadata: dict[str, Any] = {"region": region_slug}
        if coordinates and len(coordinates) >= 2:
            metadata["lon"] = coordinates[0]
            metadata["lat"] = coordinates[1]
        if phones:
            metadata["phones"] = phones
        if url:
            metadata["url"] = url
        if categories:
            metadata["categories"] = categories
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


def _get_total_found(data: dict[str, Any]) -> int | None:
    """Extract total result count from API response properties."""
    props = data.get("properties", {})
    meta = props.get("ResponseMetaData", {})
    search_resp = meta.get("SearchResponse", {})
    found = search_resp.get("found")
    if found is None:
        return None
    try:
        return int(found)
    except (TypeError, ValueError):
        return None
