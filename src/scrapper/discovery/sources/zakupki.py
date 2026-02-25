"""Zakupki.gov.ru discovery source for construction companies.

Searches government procurement data to find companies winning
construction contracts — these are guaranteed active companies.
Uses the public search page (no API key required).
"""

from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING, Any

import httpx
from bs4 import BeautifulSoup
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from scrapper.db.models import CandidateHint
from scrapper.discovery.base import DiscoverySource
from scrapper.normalizers import clean_text, normalize_inn

if TYPE_CHECKING:
    from collections.abc import Iterator

SEARCH_URL = "https://zakupki.gov.ru/epz/contract/search/results.html"

# Construction-related OKPD2 codes for filtering
CONSTRUCTION_QUERIES = [
    "строительство зданий",
    "строительные работы",
    "ремонт зданий",
]

# OKPD2 codes for construction
OKPD2_CONSTRUCTION = [
    "41",   # Building construction
    "42",   # Civil engineering
    "43",   # Specialized construction
]

_USER_AGENT = "Mozilla/5.0 (compatible; LeadgenBot/0.1; research)"
MIN_REQUEST_INTERVAL = 3.0  # Be gentle with government site
MAX_PAGES = 5  # Limit pages to avoid overloading


class ZakupkiSource(DiscoverySource):
    """Discover construction companies from government procurement data.

    Scrapes zakupki.gov.ru search results for construction contracts
    and extracts winning company names and INNs. No API key required.
    """

    def __init__(self, regions: list[str] | None = None) -> None:
        super().__init__(source_name="zakupki")
        self._seen_names: set[str] = set()
        self._last_request_time = 0.0
        self._regions = regions

    def discover(self) -> Iterator[CandidateHint]:
        """Yield construction company candidates from zakupki.gov.ru."""
        for query in CONSTRUCTION_QUERIES:
            logger.info(f"Zakupki: searching '{query}'")
            yield from self._search_paginated(query)

    def _search_paginated(self, query: str) -> Iterator[CandidateHint]:
        """Paginate through zakupki search results."""
        for page in range(1, MAX_PAGES + 1):
            html = self._fetch_page(query, page)
            if html is None:
                return

            contracts = self._parse_search_page(html)
            if not contracts:
                return

            for contract in contracts:
                hint = self._contract_to_hint(contract)
                if hint is not None:
                    yield hint

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=3, max=30),
        reraise=True,
    )
    def _fetch_page(self, query: str, page: int) -> str | None:
        """Fetch one page of search results from zakupki.gov.ru."""
        self._rate_limit()

        params: dict[str, str | int] = {
            "searchString": query,
            "morphology": "on",
            "fz44": "on",
            "fz223": "on",
            "contractStageList_0": "0",
            "contractStageList_1": "1",
            "contractStageList": "0,1",
            "selectedCurrency": "RUB",
            "pageNumber": page,
            "sortDirection": "false",
            "recordsPerPage": "_50",
            "sortBy": "UPDATE_DATE",
        }

        try:
            resp = httpx.get(
                SEARCH_URL,
                params=params,
                headers={
                    "User-Agent": _USER_AGENT,
                    "Accept-Language": "ru-RU,ru;q=0.9",
                },
                follow_redirects=True,
                timeout=30.0,
            )
            if resp.status_code == 403:
                logger.error("Zakupki.gov.ru returned 403 — access blocked")
                return None
            if resp.status_code != 200:
                logger.warning(f"Zakupki.gov.ru returned {resp.status_code}")
                return None
            return resp.text
        except httpx.RequestError as e:
            logger.error(f"Zakupki.gov.ru request error: {e}")
            raise

    def _parse_search_page(self, html: str) -> list[dict[str, str]]:
        """Parse contract search results page.

        Extracts company names, INNs, contract values, and regions
        from the search results.
        """
        soup = BeautifulSoup(html, "lxml")
        contracts: list[dict[str, str]] = []

        # Look for contract result blocks
        for block in soup.find_all("div", class_="search-registry-entry-block"):
            contract = self._parse_contract_block(block)
            if contract:
                contracts.append(contract)

        # Fallback: look for any structured contract data
        if not contracts:
            contracts = self._parse_contract_table(soup)

        return contracts

    def _parse_contract_block(self, block: Any) -> dict[str, str] | None:
        """Parse a single contract block from search results."""
        result: dict[str, str] = {}

        # Extract supplier/contractor name
        supplier_section = block.find(string=re.compile(r"Поставщик|Исполнитель|Подрядчик"))
        if supplier_section:
            parent = supplier_section.find_parent()
            if parent:
                # The company name is usually in a nearby link or text
                link = parent.find_next("a")
                if link:
                    result["company_name"] = clean_text(link.get_text())

        # Try alternative: look for company name in the block text
        if "company_name" not in result:
            for el in block.find_all(["a", "span", "div"]):
                text = clean_text(el.get_text())
                # Russian company names typically start with ООО, АО, ИП, etc.
                if re.match(r"^(?:ООО|ОАО|ЗАО|ПАО|АО|ИП|ФГУП)\s", text):
                    result["company_name"] = text
                    break

        if "company_name" not in result:
            return None

        # Extract INN
        inn_match = re.search(r"ИНН[:\s]*(\d{10,12})", block.get_text())
        if inn_match:
            inn = normalize_inn(inn_match.group(1))
            if inn:
                result["inn"] = inn

        # Extract contract value
        price_match = re.search(
            r"(\d[\d\s.,]+)\s*(?:руб|₽|RUB)", block.get_text()
        )
        if price_match:
            result["contract_value"] = clean_text(price_match.group(1))

        # Extract region
        region_match = re.search(
            r"(?:Регион|Место)\s*(?:поставки|выполнения)?[:\s]*([^\n,]+)",
            block.get_text(),
        )
        if region_match:
            result["region"] = clean_text(region_match.group(1))

        return result

    def _parse_contract_table(self, soup: BeautifulSoup) -> list[dict[str, str]]:
        """Fallback: parse tabular contract data."""
        contracts: list[dict[str, str]] = []

        # Look for any text that looks like company names with legal forms
        text = soup.get_text()
        company_pattern = re.compile(
            r'(?:ООО|ОАО|ЗАО|ПАО|АО|ИП)\s+[«"]?[\w\s\-]+[»"]?'
        )
        for match in company_pattern.finditer(text):
            name = clean_text(match.group(0))
            if len(name) > 5:
                contracts.append({"company_name": name})

        return contracts

    def _contract_to_hint(self, contract: dict[str, str]) -> CandidateHint | None:
        """Convert a parsed contract to a CandidateHint."""
        name = contract.get("company_name", "").strip()
        if not name or len(name) < 3:
            return None

        name_lower = name.lower()
        if name_lower in self._seen_names:
            return None
        self._seen_names.add(name_lower)

        # Build hint text
        hint_parts = ["Госзакупки"]
        if contract.get("contract_value"):
            hint_parts.append(f"контракт {contract['contract_value']} руб.")
        if contract.get("region"):
            hint_parts.append(contract["region"])
        hint_text = ", ".join(hint_parts)

        metadata: dict[str, Any] = {"source_api": "zakupki.gov.ru"}
        if contract.get("inn"):
            metadata["inn"] = contract["inn"]
        if contract.get("contract_value"):
            metadata["contract_value"] = contract["contract_value"]
        if contract.get("region"):
            metadata["region"] = contract["region"]

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
