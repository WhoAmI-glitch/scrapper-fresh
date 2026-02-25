"""Tests for zakupki.gov.ru discovery source."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from scrapper.discovery.sources.zakupki import (
    CONSTRUCTION_QUERIES,
    ZakupkiSource,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def zakupki_html() -> str:
    """Load the sample zakupki.gov.ru search results HTML."""
    return (FIXTURES_DIR / "zakupki_search.html").read_text(encoding="utf-8")


class TestInit:
    def test_creates_without_api_key(self) -> None:
        """Zakupki requires no API key."""
        src = ZakupkiSource()
        assert src.source_name == "zakupki"

    def test_accepts_regions(self) -> None:
        src = ZakupkiSource(regions=["moscow"])
        assert src._regions == ["moscow"]


class TestParseSearchPage:
    def test_parses_contract_blocks(self, zakupki_html: str) -> None:
        src = ZakupkiSource()
        contracts = src._parse_search_page(zakupki_html)
        # Should find at least 2 contracts with company names
        named = [c for c in contracts if c.get("company_name")]
        assert len(named) >= 2

    def test_extracts_company_names(self, zakupki_html: str) -> None:
        src = ZakupkiSource()
        contracts = src._parse_search_page(zakupki_html)
        names = [c["company_name"] for c in contracts if c.get("company_name")]
        assert any("СтройИнвест" in n for n in names)
        assert any("МонтажСтрой" in n for n in names)

    def test_extracts_inn(self, zakupki_html: str) -> None:
        src = ZakupkiSource()
        contracts = src._parse_search_page(zakupki_html)
        inns = [c.get("inn") for c in contracts if c.get("inn")]
        assert "7707083893" in inns

    def test_extracts_contract_value(self, zakupki_html: str) -> None:
        src = ZakupkiSource()
        contracts = src._parse_search_page(zakupki_html)
        values = [c.get("contract_value") for c in contracts if c.get("contract_value")]
        assert any("15" in v for v in values)


class TestContractToHint:
    def test_valid_contract(self) -> None:
        src = ZakupkiSource()
        contract = {
            "company_name": "ООО СтройИнвест",
            "inn": "7707083893",
            "contract_value": "15500000",
            "region": "Москва",
        }
        hint = src._contract_to_hint(contract)
        assert hint is not None
        assert hint.company_name == "ООО СтройИнвест"
        assert hint.source == "zakupki"
        assert "Госзакупки" in hint.hint_text
        assert hint.metadata["inn"] == "7707083893"

    def test_empty_name_returns_none(self) -> None:
        src = ZakupkiSource()
        assert src._contract_to_hint({"company_name": ""}) is None
        assert src._contract_to_hint({"company_name": "ab"}) is None

    def test_dedup_within_run(self) -> None:
        src = ZakupkiSource()
        c1 = {"company_name": "ООО Тест"}
        c2 = {"company_name": "ООО Тест"}  # duplicate
        h1 = src._contract_to_hint(c1)
        h2 = src._contract_to_hint(c2)
        assert h1 is not None
        assert h2 is None


class TestDiscover:
    def test_yields_hints(self, zakupki_html: str) -> None:
        src = ZakupkiSource()

        with patch(
            "scrapper.discovery.sources.zakupki.ZakupkiSource._fetch_page",
            return_value=zakupki_html,
        ):
            hints = list(src.discover())

        # At least 2 unique companies across all queries
        assert len(hints) >= 2
        names = {h.company_name for h in hints}
        assert any("СтройИнвест" in n for n in names)

    def test_handles_403(self) -> None:
        src = ZakupkiSource()

        with patch(
            "scrapper.discovery.sources.zakupki.ZakupkiSource._fetch_page",
            return_value=None,
        ):
            hints = list(src.discover())

        assert hints == []


class TestQueries:
    def test_construction_queries_non_empty(self) -> None:
        assert len(CONSTRUCTION_QUERIES) >= 1
        for q in CONSTRUCTION_QUERIES:
            assert q.strip()
