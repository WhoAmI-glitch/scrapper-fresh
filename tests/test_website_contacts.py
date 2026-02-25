"""Tests for website contact scraper."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from scrapper.enrichment.website_contacts import (
    _extract_emails,
    _extract_phones,
    _extract_social_links,
    _find_contact_link,
    _is_valid_email,
    scrape_website_contacts,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture() -> str:
    return (FIXTURES_DIR / "company_website.html").read_text(encoding="utf-8")


class TestExtractPhones:
    def test_extracts_tel_links(self) -> None:
        html = _load_fixture()
        phones = _extract_phones(html)
        assert "+74951234567" in phones
        assert "+78001234567" in phones

    def test_extracts_from_text(self) -> None:
        html = '<p>Звоните: +7 (499) 222-33-44 или 8-800-555-12-34</p>'
        phones = _extract_phones(html)
        assert "+74992223344" in phones
        assert "+78005551234" in phones

    def test_deduplicates(self) -> None:
        html = (
            '<a href="tel:+74951234567">+7 (495) 123-45-67</a>'
            '<p>+7 (495) 123-45-67</p>'
        )
        phones = _extract_phones(html)
        assert phones.count("+74951234567") == 1

    def test_empty_html(self) -> None:
        assert _extract_phones("<p>no phones here</p>") == []


class TestExtractEmails:
    def test_extracts_mailto_links(self) -> None:
        html = _load_fixture()
        emails = _extract_emails(html)
        assert "info@stroymaster.ru" in emails
        assert "sales@stroymaster.ru" in emails

    def test_extracts_from_text(self) -> None:
        html = "<p>Пишите: support@example.com</p>"
        emails = _extract_emails(html)
        assert "support@example.com" in emails

    def test_excludes_image_files(self) -> None:
        html = '<img src="logo@2x.png">'
        emails = _extract_emails(html)
        assert not any(e.endswith(".png") for e in emails)

    def test_empty_html(self) -> None:
        assert _extract_emails("<p>no emails</p>") == []


class TestExtractSocialLinks:
    def test_extracts_social_links(self) -> None:
        html = _load_fixture()
        social = _extract_social_links(html, "https://stroymaster.ru")
        assert any("vk.com" in s for s in social)
        assert any("t.me" in s for s in social)

    def test_ignores_non_social_links(self) -> None:
        html = '<a href="https://example.com/page">Link</a>'
        social = _extract_social_links(html, "https://example.com")
        assert social == []


class TestFindContactLink:
    def test_finds_contact_link(self) -> None:
        html = _load_fixture()
        link = _find_contact_link(html, "https://stroymaster.ru")
        assert link is not None
        assert "kontakty" in link

    def test_finds_absolute_link(self) -> None:
        html = '<a href="https://example.com/contacts">Contact</a>'
        link = _find_contact_link(html, "https://example.com")
        assert link == "https://example.com/contacts"

    def test_returns_none_when_no_contact_link(self) -> None:
        html = "<a href='/about'>About</a>"
        link = _find_contact_link(html, "https://example.com")
        assert link is None


class TestIsValidEmail:
    def test_valid_email(self) -> None:
        assert _is_valid_email("test@example.com") is True

    def test_rejects_image_extension(self) -> None:
        assert _is_valid_email("logo@2x.png") is False
        assert _is_valid_email("icon@2x.jpg") is False

    def test_rejects_empty(self) -> None:
        assert _is_valid_email("") is False
        assert _is_valid_email("nope") is False


class TestScrapeWebsiteContacts:
    def test_full_scrape_with_mock(self) -> None:
        html = _load_fixture()

        def mock_fetch(url: str) -> str | None:
            return html

        with patch(
            "scrapper.enrichment.website_contacts._fetch_page",
            side_effect=mock_fetch,
        ):
            result = scrape_website_contacts("https://stroymaster.ru")

        assert len(result["phones"]) >= 2
        assert "+74951234567" in result["phones"]
        assert len(result["emails"]) >= 2
        assert "info@stroymaster.ru" in result["emails"]
        assert len(result["social"]) >= 2
        assert len(result["websites"]) >= 1

    def test_handles_dead_site(self) -> None:
        with patch(
            "scrapper.enrichment.website_contacts._fetch_page",
            return_value=None,
        ):
            result = scrape_website_contacts("https://dead-site.example.com")

        assert result["phones"] == []
        assert result["emails"] == []

    def test_normalizes_url(self) -> None:
        html = "<p>+7 (495) 111-22-33</p>"

        with patch(
            "scrapper.enrichment.website_contacts._fetch_page",
            return_value=html,
        ):
            result = scrape_website_contacts("stroymaster.ru")

        assert "+74951112233" in result["phones"]
