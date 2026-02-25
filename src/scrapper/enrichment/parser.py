"""RussprofileParser — HTML extraction for russprofile.ru pages.

Extracts structured data from russprofile.ru company profile and search pages
using CSS-class-based selectors matched to the real site DOM structure:

  - dl > dt.company-info__title + dd.company-info__text  (ОГРН, ИНН/КПП, dates)
  - div.company-row > span.company-info__title + ...      (address, CEO, OKVED)
  - div#contacts-row                                       (phone, email, website)
  - div.finance-col                                        (revenue)
"""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup, Tag
from loguru import logger

from scrapper.db.models import Lead
from scrapper.normalizers import (
    clean_text,
    normalize_inn,
    normalize_ogrn,
    normalize_phone,
)


class RussprofileParser:
    """Parse company profile pages and search results from russprofile.ru."""

    def parse(self, html: str) -> Lead:
        """Parse a company profile page into a Lead.

        Args:
            html: Raw HTML of a russprofile.ru company profile page.

        Returns:
            Lead with extracted fields. task_id is set to 0 (caller sets real value).
        """
        soup = BeautifulSoup(html, "lxml")

        company_name = self._extract_company_name(soup)
        inn_raw, kpp_raw = self._extract_inn_kpp(soup)
        ogrn_raw = self._extract_ogrn(soup)
        reg_date_raw = self._extract_dt_dd_value(soup, "Дата регистрации")
        address_raw = self._extract_address(soup)
        ceo_raw = self._extract_ceo(soup)
        okved_raw = self._extract_okved(soup)
        status_raw = self._extract_status(soup)
        revenue_raw = self._extract_revenue(soup)
        employees_raw = self._extract_employees(soup)

        # Contacts
        phone_raw, email_raw, website_raw = self._extract_contacts(soup)

        # Normalize
        inn = normalize_inn(inn_raw)
        ogrn = normalize_ogrn(ogrn_raw)
        phone = normalize_phone(phone_raw)

        fields = {
            "company_name": company_name,
            "inn": inn,
            "ogrn": ogrn,
            "kpp": clean_text(kpp_raw),
            "address": clean_text(address_raw),
            "ceo": clean_text(ceo_raw),
            "phone": phone,
            "email": clean_text(email_raw),
            "website": clean_text(website_raw),
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

        return Lead(
            task_id=0,
            company_name=company_name or "",
            inn=inn,
            ogrn=ogrn,
            kpp=clean_text(kpp_raw) or None,
            address=clean_text(address_raw) or None,
            ceo=clean_text(ceo_raw) or None,
            phone=phone,
            email=clean_text(email_raw) or None,
            website=clean_text(website_raw) or None,
            revenue=clean_text(revenue_raw) or None,
            employees=clean_text(employees_raw) or None,
            status=clean_text(status_raw) or None,
            okved=clean_text(okved_raw) or None,
            registration_date=clean_text(reg_date_raw) or None,
        )

    def parse_search_results(self, html: str) -> list[dict[str, Any]]:
        """Extract company entries from a russprofile.ru search results page.

        Returns:
            List of dicts with keys: 'name', 'url', 'inn', 'address'.
        """
        soup = BeautifulSoup(html, "lxml")
        results: list[dict[str, Any]] = []

        profile_links = soup.find_all("a", href=re.compile(r"/id/\d+"))

        seen_urls: set[str] = set()
        for link in profile_links:
            href = str(link.get("href", ""))
            if not href or href in seen_urls:
                continue

            full_url = f"https://www.rusprofile.ru{href}" if href.startswith("/") else href
            seen_urls.add(href)

            name = clean_text(link.get_text())

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

        logger.info("Parsed search results: {} company links found", len(results))
        return results

    # ------------------------------------------------------------------
    # Private extraction helpers targeting real russprofile.ru DOM
    # ------------------------------------------------------------------

    def _extract_company_name(self, soup: BeautifulSoup) -> str:
        """Extract company name from <h1> or <title>."""
        h1 = soup.find("h1")
        if h1:
            return clean_text(h1.get_text()) or ""

        title = soup.find("title")
        if title:
            text = clean_text(title.get_text()) or ""
            text = re.sub(r"\s*[—–-]\s*[Rr]us[Pp]rofile.*$", "", text)
            return text

        return ""

    def _extract_inn_kpp(self, soup: BeautifulSoup) -> tuple[str | None, str | None]:
        """Extract INN and KPP from the 'ИНН/КПП' dt/dd block.

        Real structure:
            <dl>
              <dt class="company-info__title">ИНН/КПП</dt>
              <dd class="company-info__text ...">
                <span id="clip_inn">6161022535</span>
              </dd>
              <dd class="company-info__text ...">
                <span id="clip_kpp">616101001</span>
              </dd>
            </dl>
        """
        # Primary: use the dedicated clip_ spans
        inn_span = soup.find("span", id="clip_inn")
        kpp_span = soup.find("span", id="clip_kpp")
        if inn_span or kpp_span:
            inn = clean_text(inn_span.get_text()) if inn_span else None
            kpp = clean_text(kpp_span.get_text()) if kpp_span else None
            return inn, kpp

        # Fallback: find the dt label and read dd siblings
        dt = self._find_dt_label(soup, "ИНН")
        if dt:
            dds = dt.find_next_siblings("dd", class_="company-info__text")
            inn = clean_text(dds[0].get_text()) if len(dds) > 0 else None
            kpp = clean_text(dds[1].get_text()) if len(dds) > 1 else None
            return inn, kpp

        return None, None

    def _extract_ogrn(self, soup: BeautifulSoup) -> str | None:
        """Extract OGRN from the dt/dd block.

        Real structure:
            <dl>
              <dt class="company-info__title">ОГРН</dt>
              <dd class="company-info__text ...">
                <span id="clip_ogrn">1026102899602</span>
              </dd>
            </dl>
        """
        ogrn_span = soup.find("span", id="clip_ogrn")
        if ogrn_span:
            return clean_text(ogrn_span.get_text())

        return self._extract_dt_dd_value(soup, "ОГРН")

    def _extract_address(self, soup: BeautifulSoup) -> str | None:
        """Extract legal address.

        Real structure:
            <div class="company-row">
              <span class="company-info__title">Юридический адрес</span>
              <div ... itemprop="address">
                <address class="company-info__text">
                  <span id="clip_address">344068, Ростовская ...</span>
                </address>
              </div>
            </div>
        """
        addr_span = soup.find("span", id="clip_address")
        if addr_span:
            return clean_text(addr_span.get_text())

        # Fallback: find <address> tag with company-info__text class
        addr_tag = soup.find("address", class_="company-info__text")
        if addr_tag:
            return clean_text(addr_tag.get_text())

        # Fallback: find span label "Юридический адрес" and look inside its row
        for span in soup.find_all("span", class_="company-info__title"):
            if "адрес" in span.get_text().lower():
                row = span.find_parent(class_="company-row")
                if row:
                    text_el = row.find(class_="company-info__text")
                    if text_el:
                        return clean_text(text_el.get_text())

        return None

    def _extract_ceo(self, soup: BeautifulSoup) -> str | None:
        """Extract CEO name and title.

        Real structure:
            <div class="company-row hidden-parent">
              <span class="company-info__title">Руководитель</span>
              <div class="company-info__item">
                <span class="chief-title">Генеральный директор</span>
                <span class="company-info__text">
                  <a ...>Бурка Сергей Васильевич</a>
                </span>
              </div>
            </div>
        """
        for span in soup.find_all("span", class_="company-info__title"):
            if "Руководитель" in span.get_text():
                row = span.find_parent(class_="company-row")
                if not row:
                    continue

                item = row.find(class_="company-info__item")
                if not item:
                    continue

                # Get title (e.g. "Генеральный директор")
                title_el = item.find(class_="chief-title")
                title = clean_text(title_el.get_text()) if title_el else ""

                # Get name from the link or text span
                name_el = item.find(class_="company-info__text")
                name = ""
                if name_el:
                    link = name_el.find("a")
                    if link:
                        # Get just the name text, excluding "подробнее" links
                        name_span = link.find("span", class_="margin-right-s")
                        if name_span:
                            name = clean_text(name_span.get_text())
                        else:
                            name = clean_text(link.get_text())
                    else:
                        name = clean_text(name_el.get_text())

                parts = [p for p in [title, name] if p]
                return " ".join(parts) if parts else None

        return None

    def _extract_okved(self, soup: BeautifulSoup) -> str | None:
        """Extract primary OKVED activity.

        Real structure:
            <div class="company-row extra-padding-r">
              <span class="company-info__title">Основной вид деятельности</span>
              <span class="company-info__text">
                Производство радио... <span class="bolder">(26.51)</span>
              </span>
            </div>
        """
        for span in soup.find_all("span", class_="company-info__title"):
            text = span.get_text(strip=True)
            if "вид деятельности" in text.lower():
                row = span.find_parent(class_="company-row")
                if row:
                    val = row.find("span", class_="company-info__text")
                    if val:
                        return clean_text(val.get_text())
                # Fallback: next sibling
                next_sib = span.find_next_sibling(class_="company-info__text")
                if next_sib:
                    return clean_text(next_sib.get_text())
        return None

    def _extract_status(self, soup: BeautifulSoup) -> str | None:
        """Extract MSP registry status.

        Real structure:
            <div class="company-row">
              <span class="company-info__title">Реестр МСП</span>
              <span class="company-info__text">Статус: микропредприятие</span>
            </div>
        """
        for span in soup.find_all("span", class_="company-info__title"):
            text = span.get_text(strip=True)
            if "Реестр МСП" in text:
                row = span.find_parent(class_="company-row")
                if row:
                    val = row.find(class_="company-info__text")
                    if val:
                        return clean_text(val.get_text())

        # Also check for company status in meta or header area
        # Some pages show "Действующая организация" or "Ликвидирована"
        status_tag = soup.find(class_="company-status")
        if status_tag:
            return clean_text(status_tag.get_text())

        return None

    def _extract_revenue(self, soup: BeautifulSoup) -> str | None:
        """Extract revenue from the finance section.

        Real structure:
            <div class="finance-col space-between">
              <div class="tab-opener active" data-tab_name="tab_revenue">Выручка</div>
              <div>
                <span class="num">815</span>
                <span class="num-text">млн руб.</span>
              </div>
            </div>
        """
        for col in soup.find_all(class_="finance-col"):
            col_text = col.get_text(strip=True)
            if "Выручка" not in col_text:
                continue

            num_el = col.find(class_="num")
            unit_el = col.find(class_="num-text")
            if num_el:
                num = clean_text(num_el.get_text()) or ""
                unit = clean_text(unit_el.get_text()) if unit_el else ""
                return f"{num} {unit}".strip() if num else None

        return None

    def _extract_employees(self, soup: BeautifulSoup) -> str | None:
        """Extract employee count from 'Среднесписочная численность' dt/dd."""
        val = self._extract_dt_dd_value(soup, "Среднесписочная численность")
        if val and val.lower() != "нет данных":
            return val
        return None

    def _extract_contacts(
        self, soup: BeautifulSoup
    ) -> tuple[str | None, str | None, str | None]:
        """Extract phone, email, and website from #contacts-row.

        Contacts are often masked for non-subscribers. We extract what's visible.

        Real structure:
            <div id="contacts-row">
              <div class="company-info__contact phone iconer">
                <span class="company-info__contact-title">Телефон</span>
                <div class="company-info__contact">
                  <span ...>+7 (░░░) ░░░-░░-░░</span>
                </div>
              </div>
              <div class="company-info__contact mail iconer">
                <span class="company-info__contact-title">Электронная почта</span>
                ...
              </div>
              <div class="company-info__contact site iconer">
                <span class="company-info__contact-title">Сайт</span>
                ...
              </div>
            </div>
        """
        phone = self._extract_contact_field(soup, "phone")
        email = self._extract_contact_field(soup, "email")
        website = self._extract_contact_field(soup, "website")
        return phone, email, website

    def _extract_contact_field(self, soup: BeautifulSoup, field: str) -> str | None:
        """Extract a single contact field from #contacts-row.

        Args:
            field: One of 'phone', 'email', 'website'.
        """
        contacts_row = soup.find(id="contacts-row")
        if not contacts_row:
            if field == "phone":
                return self._extract_phone_fallback(soup)
            if field == "email":
                return self._extract_email_fallback(soup)
            if field == "website":
                return self._extract_website_fallback(soup)
            return None

        # Check if contacts say "not listed"
        empty = contacts_row.find(class_="company-info__contact empty")
        if empty:
            return None

        # Map field to CSS class on the iconer section and to label text
        css_class_map = {"phone": "phone", "email": "mail", "website": "site"}
        title_map = {
            "phone": "Телефон",
            "email": "Электронная почта",
            "website": "Сайт",
        }

        css_cls = css_class_map.get(field, "")
        title_text = title_map.get(field, "")

        # Find the section wrapper (has both the type class AND "iconer")
        section: Tag | None = None
        for el in contacts_row.find_all(class_="company-info__contact"):
            classes: list[str] = el.get("class") or []  # type: ignore[assignment]
            if css_cls in classes and "iconer" in classes:
                section = el
                break

        if not section:
            for title_el in contacts_row.find_all(class_="company-info__contact-title"):
                if title_text in title_el.get_text():
                    section = title_el.find_parent()
                    break

        if not section:
            return None

        # Collect child divs that hold individual values (not the section itself,
        # not the title, and not "Ещё N" links)
        values: list[str] = []
        for child in section.find_all("div", class_="company-info__contact", recursive=False):
            # Skip the "Ещё N" elements
            if "no-indent" in (child.get("class") or []):
                continue
            text = clean_text(child.get_text())
            if text:
                values.append(text)

        if not values:
            return None

        # Prefer unmasked value; otherwise return first (masked) value
        for v in values:
            if "░" not in v:
                return v
        return values[0]

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _find_dt_label(self, soup: BeautifulSoup, label_text: str) -> Tag | None:
        """Find a <dt class='company-info__title'> containing label_text."""
        for dt in soup.find_all("dt", class_="company-info__title"):
            if label_text in dt.get_text():
                return dt
        return None

    def _extract_dt_dd_value(self, soup: BeautifulSoup, label_text: str) -> str | None:
        """Extract the first <dd> value for a given <dt> label."""
        dt = self._find_dt_label(soup, label_text)
        if not dt:
            return None
        dd = dt.find_next_sibling("dd", class_="company-info__text")
        if dd:
            return clean_text(dd.get_text())
        return None

    # ------------------------------------------------------------------
    # Legacy fallback extractors (used when #contacts-row is absent)
    # ------------------------------------------------------------------

    def _extract_phone_fallback(self, soup: BeautifulSoup) -> str | None:
        tel_link = soup.find("a", href=re.compile(r"^tel:"))
        if tel_link:
            href = str(tel_link.get("href", ""))
            return href.replace("tel:", "").strip()

        text = soup.get_text()
        match = re.search(
            r"(?:\+7|8)[\s\-\(]*\d{3}[\s\-\)]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}",
            text,
        )
        return match.group(0).strip() if match else None

    def _extract_email_fallback(self, soup: BeautifulSoup) -> str | None:
        mailto_link = soup.find("a", href=re.compile(r"^mailto:"))
        if mailto_link:
            href = str(mailto_link.get("href", ""))
            return href.replace("mailto:", "").strip()

        text = soup.get_text()
        match = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}").search(
            text
        )
        return match.group(0) if match else None

    def _extract_website_fallback(self, soup: BeautifulSoup) -> str | None:
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
        return None
