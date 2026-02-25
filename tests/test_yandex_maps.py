"""Tests for Yandex Maps discovery source."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from scrapper.discovery.sources.yandex_maps import (
    REGIONS,
    SEARCH_QUERIES,
    YandexMapsSource,
    _get_total_found,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def yandex_response() -> dict:
    """Load the sample Yandex Maps API response."""
    return json.loads(
        (FIXTURES_DIR / "yandex_maps_response.json").read_text(encoding="utf-8")
    )


def _mock_settings(api_key: str | None = "test-api-key") -> MagicMock:
    """Create a mock Settings object with yandex_api_key."""
    s = MagicMock()
    s.yandex_api_key = api_key
    return s


# ---------------------------------------------------------------------------
# Init tests
# ---------------------------------------------------------------------------


class TestInit:
    @patch("scrapper.discovery.sources.yandex_maps.get_settings")
    def test_missing_api_key_raises(self, mock_gs: MagicMock) -> None:
        mock_gs.return_value = _mock_settings(api_key=None)
        with pytest.raises(ValueError, match="YANDEX_API_KEY"):
            YandexMapsSource()

    @patch("scrapper.discovery.sources.yandex_maps.get_settings")
    def test_default_regions(self, mock_gs: MagicMock) -> None:
        mock_gs.return_value = _mock_settings()
        src = YandexMapsSource()
        assert set(src._regions) == set(REGIONS.keys())

    @patch("scrapper.discovery.sources.yandex_maps.get_settings")
    def test_specific_regions(self, mock_gs: MagicMock) -> None:
        mock_gs.return_value = _mock_settings()
        src = YandexMapsSource(regions=["moscow", "spb"])
        assert src._regions == ["moscow", "spb"]

    @patch("scrapper.discovery.sources.yandex_maps.get_settings")
    def test_unknown_region_raises(self, mock_gs: MagicMock) -> None:
        mock_gs.return_value = _mock_settings()
        with pytest.raises(ValueError, match="Unknown regions"):
            YandexMapsSource(regions=["atlantis"])


# ---------------------------------------------------------------------------
# _parse_feature tests
# ---------------------------------------------------------------------------


class TestParseFeature:
    @patch("scrapper.discovery.sources.yandex_maps.get_settings")
    def test_valid_feature(self, mock_gs: MagicMock, yandex_response: dict) -> None:
        mock_gs.return_value = _mock_settings()
        src = YandexMapsSource(regions=["moscow"])
        feature = yandex_response["features"][0]

        hint = src._parse_feature(feature, "moscow")

        assert hint is not None
        assert hint.company_name == "ООО СтройМастер"
        assert hint.source == "yandex_maps"
        assert "Строительная компания" in hint.hint_text
        assert hint.metadata["region"] == "moscow"
        assert hint.metadata["lon"] == 37.5885
        assert hint.metadata["lat"] == 55.7334
        assert "+7 (495) 123-45-67" in hint.metadata["phones"]
        assert hint.metadata["url"] == "https://stroymaster.ru"

    @patch("scrapper.discovery.sources.yandex_maps.get_settings")
    def test_empty_name_returns_none(
        self, mock_gs: MagicMock, yandex_response: dict
    ) -> None:
        mock_gs.return_value = _mock_settings()
        src = YandexMapsSource(regions=["moscow"])
        feature = yandex_response["features"][2]  # empty name

        hint = src._parse_feature(feature, "moscow")
        assert hint is None

    @patch("scrapper.discovery.sources.yandex_maps.get_settings")
    def test_missing_optional_fields(self, mock_gs: MagicMock) -> None:
        mock_gs.return_value = _mock_settings()
        src = YandexMapsSource(regions=["moscow"])
        feature = {
            "properties": {
                "CompanyMetaData": {
                    "name": "ООО Минимал",
                }
            },
            "geometry": {},
        }

        hint = src._parse_feature(feature, "spb")

        assert hint is not None
        assert hint.company_name == "ООО Минимал"
        assert hint.metadata["region"] == "spb"
        assert "lon" not in hint.metadata
        assert "phones" not in hint.metadata
        assert "url" not in hint.metadata


# ---------------------------------------------------------------------------
# Discover tests
# ---------------------------------------------------------------------------


class TestDiscover:
    @patch("scrapper.discovery.sources.yandex_maps.get_settings")
    def test_yields_hints(
        self, mock_gs: MagicMock, yandex_response: dict
    ) -> None:
        mock_gs.return_value = _mock_settings()
        src = YandexMapsSource(regions=["moscow"])

        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = yandex_response
        mock_resp.raise_for_status = MagicMock()

        with patch("scrapper.discovery.sources.yandex_maps.httpx.get", return_value=mock_resp):
            hints = list(src.discover())

        # 3 features: 2 valid names, 1 empty -> 2 hints per query
        # But same companies appear across all 3 queries -> dedup kicks in
        # First query yields 2, subsequent queries yield 0 (same names)
        assert len(hints) == 2
        names = {h.company_name for h in hints}
        assert "ООО СтройМастер" in names
        assert "АО БетонСервис" in names

    @patch("scrapper.discovery.sources.yandex_maps.get_settings")
    def test_dedup_within_run(
        self, mock_gs: MagicMock, yandex_response: dict
    ) -> None:
        mock_gs.return_value = _mock_settings()
        src = YandexMapsSource(regions=["moscow"])

        # Simulate same company appearing twice (different case)
        feature = yandex_response["features"][0].copy()
        response_dupe = {
            "type": "FeatureCollection",
            "properties": {
                "ResponseMetaData": {
                    "SearchResponse": {"found": 1}
                }
            },
            "features": [feature, feature],
        }
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = response_dupe
        mock_resp.raise_for_status = MagicMock()

        with patch("scrapper.discovery.sources.yandex_maps.httpx.get", return_value=mock_resp):
            hints = list(src.discover())

        # Despite duplicates across queries, each unique name appears once
        names = [h.company_name for h in hints]
        assert names.count("ООО СтройМастер") == 1

    @patch("scrapper.discovery.sources.yandex_maps.get_settings")
    def test_daily_limit_stops_discovery(self, mock_gs: MagicMock) -> None:
        mock_gs.return_value = _mock_settings()
        src = YandexMapsSource(regions=["moscow"])
        src._request_count = 499  # one request left

        response = {
            "type": "FeatureCollection",
            "properties": {
                "ResponseMetaData": {
                    "SearchResponse": {"found": 1}
                }
            },
            "features": [
                {
                    "properties": {
                        "CompanyMetaData": {"name": "ООО Тест"}
                    },
                    "geometry": {},
                }
            ],
        }
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = response
        mock_resp.raise_for_status = MagicMock()

        with patch("scrapper.discovery.sources.yandex_maps.httpx.get", return_value=mock_resp):
            hints = list(src.discover())

        # Only 1 request allowed (of 3 queries), and it yielded 1 hint
        assert len(hints) == 1
        assert src._request_count == 500

    @patch("scrapper.discovery.sources.yandex_maps.get_settings")
    def test_403_returns_none(self, mock_gs: MagicMock) -> None:
        mock_gs.return_value = _mock_settings()
        src = YandexMapsSource(regions=["moscow"])

        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 403

        with patch("scrapper.discovery.sources.yandex_maps.httpx.get", return_value=mock_resp):
            hints = list(src.discover())

        assert hints == []


# ---------------------------------------------------------------------------
# _get_total_found tests
# ---------------------------------------------------------------------------


class TestGetTotalFound:
    def test_valid_found(self) -> None:
        data = {
            "properties": {
                "ResponseMetaData": {
                    "SearchResponse": {"found": 120}
                }
            }
        }
        assert _get_total_found(data) == 120

    def test_missing_found(self) -> None:
        assert _get_total_found({}) is None
        assert _get_total_found({"properties": {}}) is None

    def test_bad_found_value(self) -> None:
        data = {
            "properties": {
                "ResponseMetaData": {
                    "SearchResponse": {"found": "not_a_number"}
                }
            }
        }
        assert _get_total_found(data) is None

    def test_string_number(self) -> None:
        data = {
            "properties": {
                "ResponseMetaData": {
                    "SearchResponse": {"found": "250"}
                }
            }
        }
        assert _get_total_found(data) == 250


# ---------------------------------------------------------------------------
# Region data tests
# ---------------------------------------------------------------------------


class TestRegions:
    def test_all_major_cities_present(self) -> None:
        expected = {
            "moscow", "spb", "novosibirsk", "ekaterinburg",
            "kazan", "nizhny_novgorod", "krasnoyarsk",
            "chelyabinsk", "samara", "rostov",
        }
        assert set(REGIONS.keys()) == expected

    def test_coordinates_are_valid(self) -> None:
        for slug, (lon, lat, span_lon, span_lat) in REGIONS.items():
            assert -180 <= lon <= 180, f"{slug}: invalid longitude {lon}"
            assert -90 <= lat <= 90, f"{slug}: invalid latitude {lat}"
            assert span_lon > 0, f"{slug}: span_lon must be positive"
            assert span_lat > 0, f"{slug}: span_lat must be positive"

    def test_search_queries_non_empty(self) -> None:
        assert len(SEARCH_QUERIES) >= 1
        for q in SEARCH_QUERIES:
            assert q.strip()
