"""ProfileResolver — build russprofile.ru search URLs for company names."""

from __future__ import annotations

from urllib.parse import quote

from loguru import logger

_SEARCH_URL_TEMPLATE = "https://www.rusprofile.ru/search?query={query}&type=ul"


class ProfileResolver:
    """Resolves a company name to a russprofile.ru search URL.

    In the MVP, we simply construct the search URL with properly encoded
    Cyrillic text. Real resolution (parsing search results for the best
    match) happens after fetching the search page.
    """

    def resolve(self, company_name: str) -> str | None:
        """Build a russprofile.ru search URL for the given company name.

        Args:
            company_name: Raw company name, possibly with legal form prefix.

        Returns:
            The search URL string, or None if the name is empty after cleaning.
        """
        if not company_name:
            logger.warning("Empty company name passed to resolver")
            return None

        # Clean the name but keep the original for search
        # (russprofile handles legal forms in queries fine)
        cleaned = company_name.strip()
        if not cleaned:
            logger.warning("Company name is blank after stripping")
            return None

        encoded_query = quote(cleaned, safe="")
        url = _SEARCH_URL_TEMPLATE.format(query=encoded_query)

        logger.info(
            "Resolved company '{}' -> search URL: {}",
            company_name,
            url,
        )

        return url
