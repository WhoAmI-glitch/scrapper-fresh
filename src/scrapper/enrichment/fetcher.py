"""HTTP fetcher with retry, rate limiting, and optional proxy support."""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from scrapper.config import get_settings

_USER_AGENT = "Mozilla/5.0 (compatible; LeadgenBot/0.1; research)"
_ACCEPT_LANGUAGE = "ru-RU,ru;q=0.9"


@dataclass
class FetchResult:
    """Result of an HTTP fetch operation."""

    url: str
    status_code: int
    content: str
    content_length: int
    elapsed_ms: float


class Fetcher:
    """HTTP fetcher with rate limiting, retry, and optional Bright Data proxy.

    Usage::

        fetcher = Fetcher()
        result = fetcher.fetch("https://www.rusprofile.ru/id/12345")
        print(result.status_code, len(result.content))
    """

    def __init__(self) -> None:
        settings = get_settings()

        self._request_delay: float = settings.request_delay
        self._last_request_time: float = 0.0

        # Build httpx client kwargs
        client_kwargs: dict = {
            "timeout": httpx.Timeout(
                timeout=settings.fetch_timeout,
                connect=settings.connect_timeout,
            ),
            "headers": {
                "User-Agent": _USER_AGENT,
                "Accept-Language": _ACCEPT_LANGUAGE,
            },
            "follow_redirects": True,
        }

        # Optional Bright Data proxy
        if settings.brightdata_proxy_url:
            client_kwargs["proxy"] = settings.brightdata_proxy_url
            logger.info(
                "Fetcher configured with Bright Data proxy: {}",
                settings.brightdata_proxy_url[:40] + "...",
            )
        else:
            logger.info("Fetcher configured without proxy (direct HTTP)")

        self._client = httpx.Client(**client_kwargs)

    def _rate_limit(self) -> None:
        """Sleep if needed to respect request_delay between requests."""
        if self._last_request_time > 0:
            elapsed = time.monotonic() - self._last_request_time
            remaining = self._request_delay - elapsed
            if remaining > 0:
                logger.debug("Rate limit: sleeping {:.2f}s", remaining)
                time.sleep(remaining)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
        before_sleep=lambda retry_state: logger.warning(
            "Fetch attempt {} failed, retrying in {:.1f}s: {}",
            retry_state.attempt_number,
            retry_state.next_action.sleep if retry_state.next_action else 0,
            retry_state.outcome.exception() if retry_state.outcome else "unknown",
        ),
    )
    def _do_fetch(self, url: str) -> httpx.Response:
        """Execute the HTTP GET with retries on transport/timeout errors."""
        response = self._client.get(url)

        # Retry on server errors (5xx)
        if response.status_code >= 500:
            raise httpx.TransportError(
                f"Server error {response.status_code} for {url}"
            )

        return response

    def fetch(self, url: str) -> FetchResult:
        """Fetch a URL with rate limiting and retry.

        Args:
            url: The URL to fetch.

        Returns:
            FetchResult with status code, content, timing, etc.

        Raises:
            httpx.TransportError: If all retry attempts fail.
            httpx.TimeoutException: If all retry attempts time out.
        """
        self._rate_limit()

        logger.info("Fetching URL: {}", url)
        start = time.monotonic()

        try:
            response = self._do_fetch(url)
            elapsed_ms = (time.monotonic() - start) * 1000
            self._last_request_time = time.monotonic()

            content = response.text
            result = FetchResult(
                url=str(response.url),
                status_code=response.status_code,
                content=content,
                content_length=len(content),
                elapsed_ms=round(elapsed_ms, 1),
            )

            logger.info(
                "Fetched {} -> {} ({} chars, {:.0f}ms)",
                url,
                result.status_code,
                result.content_length,
                result.elapsed_ms,
            )
            return result

        except Exception:
            self._last_request_time = time.monotonic()
            logger.error("Failed to fetch URL after retries: {}", url)
            raise

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()
        logger.debug("Fetcher HTTP client closed")

    def __enter__(self) -> Fetcher:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
