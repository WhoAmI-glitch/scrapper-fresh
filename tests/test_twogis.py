"""Tests for 2GIS discovery source."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from scrapper.discovery.sources.twogis import (
    CITY_CENTERS,
    SEARCH_QUERIES,
    TwoGisSource,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def twogis_response() -> dict:
    """Load the sample 2GIS API response."""
    return json.loads(
        (FIXTURES_DIR / "twogis_response.json").read_text(encoding="utf-8")
    )


def _mock_settings(api_key: str | None = "test-2gis-key") -> MagicMock:
    s = MagicMock()
    s.twogis_api_key = api_key
    return s


class TestInit:
    @patch("scrapper.discovery.sources.twogis.get_settings")
    def test_missing_api_key_raises(self, mock_gs: MagicMock) -> None:
        mock_gs.return_value = _mock_settings(api_key=None)
        with pytest.raises(ValueError, match="TWOGIS_API_KEY"):
            TwoGisSource()

    @patch("scrapper.discovery.sources.twogis.get_settings")
    def test_default_regions(self, mock_gs: MagicMock) -> None:
        mock_gs.return_value = _mock_settings()
        src = TwoGisSource()
        assert set(src._regions) == set(CITY_CENTERS.keys())

    @patch("scrapper.discovery.sources.twogis.get_settings")
    def test_specific_regions(self, mock_gs: MagicMock) -> None:
        mock_gs.return_value = _mock_settings()
        src = TwoGisSource(regions=["moscow", "spb"])
        assert src._regions == ["moscow", "spb"]

    @patch("scrapper.discovery.sources.twogis.get_settings")
    def test_unknown_region_raises(self, mock_gs: MagicMock) -> None:
        mock_gs.return_value = _mock_settings()
        with pytest.raises(ValueError, match="Unknown regions"):
            TwoGisSource(regions=["atlantis"])


class TestParseItem:
    @patch("scrapper.discovery.sources.twogis.get_settings")
    def test_valid_item(self, mock_gs: MagicMock, twogis_response: dict) -> None:
        mock_gs.return_value = _mock_settings()
        src = TwoGisSource(regions=["moscow"])
        item = twogis_response["result"]["items"][0]

        hint = src._parse_item(item, "moscow")

        assert hint is not None
        assert hint.company_name == "ООО СтройМастер"
        assert hint.source == "twogis"
        assert "Строительные компании" in hint.hint_text
        assert hint.metadata["region"] == "moscow"
        assert hint.metadata["lon"] == 37.5885
        assert "+7 (495) 123-45-67" in hint.metadata["phones"]
        assert hint.metadata["url"] == "https://stroymaster.ru"

    @patch("scrapper.discovery.sources.twogis.get_settings")
    def test_empty_name_returns_none(
        self, mock_gs: MagicMock, twogis_response: dict
    ) -> None:
        mock_gs.return_value = _mock_settings()
        src = TwoGisSource(regions=["moscow"])
        item = twogis_response["result"]["items"][2]

        hint = src._parse_item(item, "moscow")
        assert hint is None

    @patch("scrapper.discovery.sources.twogis.get_settings")
    def test_missing_optional_fields(self, mock_gs: MagicMock) -> None:
        mock_gs.return_value = _mock_settings()
        src = TwoGisSource(regions=["moscow"])
        item = {"name": "ООО Минимал", "org": {}, "rubrics": [], "contact_groups": []}

        hint = src._parse_item(item, "spb")
        assert hint is not None
        assert hint.company_name == "ООО Минимал"
        assert hint.metadata["region"] == "spb"


class TestDiscover:
    @patch("scrapper.discovery.sources.twogis.get_settings")
    def test_yields_hints(
        self, mock_gs: MagicMock, twogis_response: dict
    ) -> None:
        mock_gs.return_value = _mock_settings()
        src = TwoGisSource(regions=["moscow"])

        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = twogis_response
        mock_resp.raise_for_status = MagicMock()

        with patch("scrapper.discovery.sources.twogis.httpx.get", return_value=mock_resp):
            hints = list(src.discover())

        # 2 valid items, deduped across 2 queries -> 2 unique
        assert len(hints) == 2
        names = {h.company_name for h in hints}
        assert "ООО СтройМастер" in names
        assert "АО БетонСервис" in names

    @patch("scrapper.discovery.sources.twogis.get_settings")
    def test_dedup_within_run(
        self, mock_gs: MagicMock, twogis_response: dict
    ) -> None:
        mock_gs.return_value = _mock_settings()
        src = TwoGisSource(regions=["moscow"])

        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = twogis_response
        mock_resp.raise_for_status = MagicMock()

        with patch("scrapper.discovery.sources.twogis.httpx.get", return_value=mock_resp):
            hints = list(src.discover())

        names = [h.company_name for h in hints]
        assert names.count("ООО СтройМастер") == 1

    @patch("scrapper.discovery.sources.twogis.get_settings")
    def test_403_returns_none(self, mock_gs: MagicMock) -> None:
        mock_gs.return_value = _mock_settings()
        src = TwoGisSource(regions=["moscow"])

        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 403

        with patch("scrapper.discovery.sources.twogis.httpx.get", return_value=mock_resp):
            hints = list(src.discover())

        assert hints == []


class TestRegions:
    def test_all_major_cities_present(self) -> None:
        expected = {
            "moscow", "spb", "novosibirsk", "ekaterinburg",
            "kazan", "nizhny_novgorod", "krasnoyarsk",
            "chelyabinsk", "samara", "rostov",
        }
        assert set(CITY_CENTERS.keys()) == expected

    def test_coordinates_are_valid(self) -> None:
        for slug, (lon, lat) in CITY_CENTERS.items():
            assert -180 <= lon <= 180, f"{slug}: invalid longitude {lon}"
            assert -90 <= lat <= 90, f"{slug}: invalid latitude {lat}"

    def test_search_queries_non_empty(self) -> None:
        assert len(SEARCH_QUERIES) >= 1
        for q in SEARCH_QUERIES:
            assert q.strip()
