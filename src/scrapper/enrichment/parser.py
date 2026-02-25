"""RussprofileParser — label-based HTML extraction for russprofile.ru pages."""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup
from loguru import logger

from scrapper.db.models import Lead
from scrapper.normalizers import (
    clean_text,
    normalize_inn,
    normalize_ogrn,
    normalize_phone,
)


class RussprofileParser:
    """Parse company profile pages and search results from russprofile.ru.

    Uses label-based extraction: finds text labels like "ИНН", "ОГРН", etc.
    and extracts the adjacent value text.
    """

    def parse(self, html: str) -> Lead:
        """Parse a company profile page into a Lead dataclass.

        Args:
            html: Raw HTML of a russprofile.ru company profile page.

        Returns:
            Lead dataclass with extracted fields. task_id is set to 0
            as a placeholder (caller should set the real value).
        """
        soup = BeautifulSoup(html, "lxml")

        # Extract the company name from the page title or heading
        company_name = self._extract_company_name(soup)

        # Extract fields by label
        inn_raw = self._find_by_label(soup, "ИНН")
        ogrn_raw = self._find_by_label(soup, "ОГРН")
        kpp_raw = self._find_by_label(soup, "КПП")
        address_raw = self._find_by_label(soup, "Адрес")
        ceo_raw = self._find_by_label(soup, "Руководитель")
        okved_raw = self._find_by_label(soup, "ОКВЭД")
        status_raw = self._find_by_label(soup, "Статус")
        reg_date_raw = self._find_by_label(soup, "Дата регистрации")
        revenue_raw = self._find_by_label(soup, "Выручка")
        employees_raw = self._find_by_label(soup, "Сотрудники")

        # Extract contact info (these are often in separate sections)
        phone_raw = self._extract_phone(soup)
        email = self._extract_email(soup)
        website = self._extract_website(soup)

        # Normalize extracted values
        inn = normalize_inn(inn_raw)
        ogrn = normalize_ogrn(ogrn_raw)
        phone = normalize_phone(phone_raw)

        # Count how many fields we actually extracted
        fields = {
            "company_name": company_name,
            "inn": inn,
            "ogrn": ogrn,
            "kpp": clean_text(kpp_raw),
            "address": clean_text(address_raw),
            "ceo": clean_text(ceo_raw),
            "phone": phone,
            "email": clean_text(email),
            "website": clean_text(website),
            "okved": clean_text(okved_raw),
            "status": clean_text(status_raw),
            "registration_date": clean_text(reg_date_raw),
            "revenue": clean_text(revenue_raw),
            "employees": clean_text(employees_raw),
        }

        filled = sum(1 for v in fields.values() if v)
        logger.info(
            "Parsed profile for '{}': {}/{} fields extracted",
            company_name,
            filled,
            len(fields),
        )

        lead = Lead(
            task_id=0,  # placeholder — caller sets the real task_id
            company_name=company_name or "",
            inn=inn,
            ogrn=ogrn,
            kpp=clean_text(kpp_raw) or None,
            address=clean_text(address_raw) or None,
            ceo=clean_text(ceo_raw) or None,
            phone=phone,
            email=clean_text(email) or None,
            website=clean_text(website) or None,
            revenue=clean_text(revenue_raw) or None,
            employees=clean_text(employees_raw) or None,
            status=clean_text(status_raw) or None,
            okved=clean_text(okved_raw) or None,
            registration_date=clean_text(reg_date_raw) or None,
        )

        return lead

    def parse_search_results(self, html: str) -> list[dict[str, Any]]:
        """Extract company entries from a russprofile.ru search results page.

        Args:
            html: Raw HTML of a search results page.

        Returns:
            List of dicts with keys: 'name', 'url', 'inn', 'address'.
        """
        soup = BeautifulSoup(html, "lxml")
        results: list[dict[str, Any]] = []

        # russprofile.ru search results are typically in div or li elements
        # with links to /id/XXXXX profile pages
        profile_links = soup.find_all("a", href=re.compile(r"/id/\d+"))

        seen_urls: set[str] = set()
        for link in profile_links:
            href = str(link.get("href", ""))
            if not href or href in seen_urls:
                continue

            # Build full URL if relative
            full_url = f"https://www.rusprofile.ru{href}" if href.startswith("/") else href

            seen_urls.add(href)

            # Try to extract name from the link text or parent container
            name = clean_text(link.get_text())

            # Try to find INN near this link
            parent = link.find_parent("div") or link.find_parent("li")
            inn = None
            address = None
            if parent:
                inn_match = re.search(r"ИНН[:\s]*(\d{10,12})", parent.get_text())
                if inn_match:
                    inn = inn_match.group(1)

                addr_match = re.search(
                    r"(?:Адрес|адрес)[:\s]*(.+?)(?:\n|$)",
                    parent.get_text(),
                )
                if addr_match:
                    address = clean_text(addr_match.group(1))

            results.append(
                {
                    "name": name,
                    "url": full_url,
                    "inn": inn,
                    "address": address,
                }
            )

        logger.info(
            "Parsed search results: {} company links found",
            len(results),
        )

        return results

    def _extract_company_name(self, soup: BeautifulSoup) -> str:
        """Extract company name from the page heading or title."""
        # Try h1 tag first (typical for profile pages)
        h1 = soup.find("h1")
        if h1:
            return clean_text(h1.get_text())

        # Fall back to title tag
        title = soup.find("title")
        if title:
            text = clean_text(title.get_text())
            # Strip common suffixes like " — Rusprofile"
            text = re.sub(r"\s*[—–-]\s*[Rr]us[Pp]rofile.*$", "", text)
            return text

        return ""

    def _find_by_label(self, soup: BeautifulSoup, label_text: str) -> str | None:
        """Find the value adjacent to a label like 'ИНН', 'ОГРН', etc.

        Searches for text nodes containing the label, then looks at the
        parent element's siblings or children for the value.
        """
        # Find all text nodes that contain the label
        label = soup.find(string=re.compile(rf"\b{re.escape(label_text)}\b", re.IGNORECASE))
        if not label:
            return None

        parent = label.find_parent()
        if not parent:
            return None

        # Strategy 1: Value is in the next sibling element
        next_sib = parent.find_next_sibling()
        if next_sib:
            text = clean_text(next_sib.get_text())
            if text and text.lower() != label_text.lower():
                return text

        # Strategy 2: Value is in the parent's next sibling
        grandparent = parent.find_parent()
        if grandparent:
            next_parent_sib = grandparent.find_next_sibling()
            if next_parent_sib:
                text = clean_text(next_parent_sib.get_text())
                if text and text.lower() != label_text.lower():
                    return text

        # Strategy 3: Value is in the same element, after the label
        parent_text = clean_text(parent.get_text())
        if parent_text and parent_text != label_text:
            # Try to extract value after the label
            match = re.search(
                rf"{re.escape(label_text)}[:\s]+(.+)",
                parent_text,
                re.IGNORECASE,
            )
            if match:
                return clean_text(match.group(1))

        # Strategy 4: Look in the next element in document order
        next_elem = parent.find_next()
        if next_elem and next_elem != parent:
            text = clean_text(next_elem.get_text())
            if text and text.lower() != label_text.lower():
                return text

        return None

    def _extract_phone(self, soup: BeautifulSoup) -> str | None:
        """Extract a phone number from the page.

        Looks for tel: links and common phone patterns.
        """
        # Try tel: links first
        tel_link = soup.find("a", href=re.compile(r"^tel:"))
        if tel_link:
            href = str(tel_link.get("href", ""))
            return href.replace("tel:", "").strip()

        # Search for phone patterns in page text
        text = soup.get_text()
        phone_pattern = re.compile(
            r"(?:\+7|8)[\s\-\(]*\d{3}[\s\-\)]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}"
        )
        match = phone_pattern.search(text)
        if match:
            return match.group(0).strip()

        return None

    def _extract_email(self, soup: BeautifulSoup) -> str | None:
        """Extract an email address from the page."""
        # Try mailto: links
        mailto_link = soup.find("a", href=re.compile(r"^mailto:"))
        if mailto_link:
            href = str(mailto_link.get("href", ""))
            return href.replace("mailto:", "").strip()

        # Search for email pattern in page text
        text = soup.get_text()
        email_pattern = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
        match = email_pattern.search(text)
        if match:
            return match.group(0)

        return None

    def _extract_website(self, soup: BeautifulSoup) -> str | None:
        """Extract the company website from the page.

        Looks for links labeled as website or external links that are not
        russprofile.ru itself.
        """
        # Look for a label like "Сайт" or "Веб-сайт"
        site_label = soup.find(
            string=re.compile(r"\b(?:Сайт|Веб-сайт|Website)\b", re.IGNORECASE)
        )
        if site_label:
            parent = site_label.find_parent()
            if parent:
                link = parent.find_next("a", href=re.compile(r"^https?://"))
                if link:
                    href = str(link.get("href", ""))
                    if "rusprofile.ru" not in href:
                        return href

        # Look for external links that are not rusprofile.ru
        for link in soup.find_all("a", href=re.compile(r"^https?://")):
            href = str(link.get("href", ""))
            if (
                "rusprofile.ru" not in href
                and "yandex" not in href
                and "google" not in href
                and "vk.com" not in href
            ):
                link_text = clean_text(link.get_text())
                # Check if this looks like a company website link
                if link_text and re.match(r"^[\w\-]+\.\w{2,}", link_text):
                    return href

        return None
