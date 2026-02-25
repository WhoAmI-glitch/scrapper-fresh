"""Scrape contact information from company websites.

Fetches homepage and common contact pages (/contacts, /kontakty),
extracts phone numbers, email addresses, and social media links.
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

import httpx
from loguru import logger

from scrapper.normalizers import normalize_phone

_USER_AGENT = "Mozilla/5.0 (compatible; LeadgenBot/0.1; research)"
_TIMEOUT = httpx.Timeout(10.0, connect=5.0)

# Common contact page paths to try
_CONTACT_PATHS = [
    "/contacts",
    "/kontakty",
    "/contact",
    "/kontakt",
    "/about/contacts",
    "/o-kompanii/kontakty",
]

# Phone regex for Russian numbers
_PHONE_PATTERN = re.compile(
    r"(?:\+7|8)[\s\-.(]*\d{3}[\s\-).(]*\d{3}[\s\-.(]*\d{2}[\s\-.(]*\d{2}"
)

# Email regex
_EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)

# Social media domains
_SOCIAL_DOMAINS = {
    "vk.com", "t.me", "telegram.me", "ok.ru",
    "wa.me", "instagram.com", "facebook.com",
    "youtube.com", "zen.yandex.ru", "dzen.ru",
}

# Domains to exclude from website links
_SKIP_DOMAINS = {
    "rusprofile.ru", "google.com", "yandex.ru", "yandex.com",
    "youtube.com", "facebook.com", "instagram.com", "vk.com",
    "ok.ru", "t.me", "wa.me", "telegram.me",
}


def scrape_website_contacts(url: str) -> dict[str, list[str]]:
    """Scrape contact info from a company website.

    Fetches the homepage and common contact pages, extracts phones,
    emails, and social links.

    Args:
        url: Company website URL (e.g. "https://stroymaster.ru")

    Returns:
        Dict with keys: phones, emails, websites, social.
        Each value is a deduplicated list of strings.
    """
    result: dict[str, list[str]] = {
        "phones": [],
        "emails": [],
        "websites": [],
        "social": [],
    }

    # Normalize URL
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    pages_html: list[str] = []

    # Fetch homepage
    homepage_html = _fetch_page(url)
    if homepage_html:
        pages_html.append(homepage_html)

        # Try to find contact page link in the homepage
        contact_url = _find_contact_link(homepage_html, base_url)
        if contact_url:
            contact_html = _fetch_page(contact_url)
            if contact_html:
                pages_html.append(contact_html)

    # If no contact link found, try common paths
    if len(pages_html) < 2:
        for path in _CONTACT_PATHS:
            contact_url = urljoin(base_url, path)
            contact_html = _fetch_page(contact_url)
            if contact_html:
                pages_html.append(contact_html)
                break  # One contact page is enough

    if not pages_html:
        logger.warning(f"Could not fetch any pages from {url}")
        return result

    # Extract contacts from all fetched pages
    seen_phones: set[str] = set()
    seen_emails: set[str] = set()
    seen_social: set[str] = set()

    for html in pages_html:
        for phone in _extract_phones(html):
            if phone not in seen_phones:
                seen_phones.add(phone)
                result["phones"].append(phone)

        for email in _extract_emails(html):
            if email not in seen_emails:
                seen_emails.add(email)
                result["emails"].append(email)

        for social_url in _extract_social_links(html, base_url):
            if social_url not in seen_social:
                seen_social.add(social_url)
                result["social"].append(social_url)

    # Add the website itself
    result["websites"].append(url)

    logger.info(
        f"Scraped {url}: {len(result['phones'])} phones, "
        f"{len(result['emails'])} emails, {len(result['social'])} social"
    )

    return result


def _fetch_page(url: str) -> str | None:
    """Fetch a single page with timeout, returning HTML or None."""
    try:
        with httpx.Client(
            timeout=_TIMEOUT,
            headers={"User-Agent": _USER_AGENT, "Accept-Language": "ru-RU,ru;q=0.9"},
            follow_redirects=True,
        ) as client:
            resp = client.get(url)
        if resp.status_code == 200:
            return resp.text
        return None
    except (httpx.RequestError, httpx.HTTPStatusError):
        return None


def _find_contact_link(html: str, base_url: str) -> str | None:
    """Find a link to a contact page in the HTML."""
    # Look for href containing contact-related keywords
    pattern = re.compile(
        r'href=["\']([^"\']*(?:contact|kontakt|контакт)[^"\']*)["\']',
        re.IGNORECASE,
    )
    match = pattern.search(html)
    if match:
        href = match.group(1)
        if href.startswith(("http://", "https://")):
            return href
        result: str = urljoin(base_url, href)
        return result
    return None


def _extract_phones(html: str) -> list[str]:
    """Extract and normalize phone numbers from HTML."""
    phones: list[str] = []

    # Extract from tel: links
    tel_pattern = re.compile(r'href=["\']tel:([^"\']+)["\']')
    for match in tel_pattern.finditer(html):
        raw = match.group(1).strip()
        normalized = normalize_phone(raw)
        if normalized and normalized not in phones:
            phones.append(normalized)

    # Extract from visible text (strip HTML tags first)
    text = re.sub(r"<[^>]+>", " ", html)
    for match in _PHONE_PATTERN.finditer(text):
        raw = match.group(0).strip()
        normalized = normalize_phone(raw)
        if normalized and normalized not in phones:
            phones.append(normalized)

    return phones


def _extract_emails(html: str) -> list[str]:
    """Extract email addresses from HTML."""
    emails: list[str] = []

    # Extract from mailto: links
    mailto_pattern = re.compile(r'href=["\']mailto:([^"\'?]+)["\']')
    for match in mailto_pattern.finditer(html):
        email = match.group(1).strip().lower()
        if _is_valid_email(email) and email not in emails:
            emails.append(email)

    # Extract from visible text
    text = re.sub(r"<[^>]+>", " ", html)
    for match in _EMAIL_PATTERN.finditer(text):
        email = match.group(0).strip().lower()
        if _is_valid_email(email) and email not in emails:
            emails.append(email)

    return emails


def _is_valid_email(email: str) -> bool:
    """Basic email validation — exclude image files and common noise."""
    if not email or "@" not in email:
        return False
    # Exclude common false positives (image filenames, CSS, etc.)
    noise_extensions = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".css", ".js")
    return not any(email.endswith(ext) for ext in noise_extensions)


def _extract_social_links(html: str, base_url: str) -> list[str]:
    """Extract social media links from HTML."""
    social: list[str] = []

    href_pattern = re.compile(r'href=["\']([^"\']+)["\']')
    for match in href_pattern.finditer(html):
        href = match.group(1).strip()
        if not href.startswith(("http://", "https://")):
            continue
        try:
            parsed = urlparse(href)
            domain = parsed.netloc.lower().removeprefix("www.")
            if domain in _SOCIAL_DOMAINS and href not in social:
                social.append(href)
        except ValueError:
            continue

    return social
