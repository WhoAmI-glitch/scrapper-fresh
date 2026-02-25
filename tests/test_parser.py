"""Tests for the RussprofileParser."""

import pytest

from scrapper.enrichment.parser import RussprofileParser


@pytest.fixture
def parser():
    return RussprofileParser()


class TestParseProfile:
    def test_extracts_company_name(self, parser, sample_profile_html):
        lead = parser.parse(sample_profile_html)
        assert "СтройГарант" in lead.company_name

    def test_extracts_inn(self, parser, sample_profile_html):
        lead = parser.parse(sample_profile_html)
        assert lead.inn is not None
        assert lead.inn.startswith("770")

    def test_extracts_ogrn(self, parser, sample_profile_html):
        lead = parser.parse(sample_profile_html)
        assert lead.ogrn is not None

    def test_extracts_address(self, parser, sample_profile_html):
        lead = parser.parse(sample_profile_html)
        assert lead.address is not None
        assert "Москва" in lead.address

    def test_extracts_ceo(self, parser, sample_profile_html):
        lead = parser.parse(sample_profile_html)
        assert lead.ceo is not None
        assert "Иванов" in lead.ceo

    def test_extracts_phone(self, parser, sample_profile_html):
        lead = parser.parse(sample_profile_html)
        assert lead.phone is not None

    def test_extracts_email(self, parser, sample_profile_html):
        lead = parser.parse(sample_profile_html)
        assert lead.email is not None
        assert "@" in lead.email


class TestParseSearchResults:
    def test_finds_results(self, parser, sample_search_html):
        results = parser.parse_search_results(sample_search_html)
        assert len(results) >= 1

    def test_result_has_name(self, parser, sample_search_html):
        results = parser.parse_search_results(sample_search_html)
        assert results[0].get("name") is not None

    def test_result_has_url(self, parser, sample_search_html):
        results = parser.parse_search_results(sample_search_html)
        assert results[0].get("url") is not None
