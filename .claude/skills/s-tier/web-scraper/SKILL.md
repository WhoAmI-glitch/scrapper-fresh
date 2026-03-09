---
name: web-scraper
description: >
  Production web scraping patterns for building reliable, respectful, and scalable
  data extraction pipelines. Use when building scrapers, parsing HTML, extracting
  structured data from websites, handling anti-bot measures, managing proxy rotation,
  implementing retry logic, or when the user mentions scraping, crawling, data
  extraction, BeautifulSoup, Scrapy, Playwright, Puppeteer, or needs to extract
  information from web pages programmatically.
---

# Web Scraper Patterns

Build production-grade web scraping pipelines that are reliable, respectful, and maintainable.

## Architecture Principles

### Pipeline Design
1. **Discover** — find target URLs (sitemaps, search, pagination, API)
2. **Fetch** — download pages with retry, backoff, proxy rotation
3. **Parse** — extract structured data from HTML/JSON
4. **Validate** — verify extracted data quality and completeness
5. **Store** — persist to database with deduplication
6. **Monitor** — track success rates, latency, data quality

### Fetching Strategies (priority order)
1. **Official API** — always prefer if available
2. **RSS/Atom feeds** — structured, lightweight
3. **Direct HTTP** — httpx/requests with proper headers
4. **Proxy rotation** — Bright Data, ScraperAPI, residential proxies
5. **Browser automation** — Playwright/Puppeteer for JS-rendered pages
6. **Browser API** — Bright Data Browser API for heavy anti-bot

## Python Stack

### Core Libraries
- `httpx` — async HTTP client (prefer over requests for new code)
- `beautifulsoup4` + `lxml` — HTML parsing
- `selectolax` — faster alternative for simple CSS selectors
- `playwright` — browser automation when JS rendering needed
- `scrapy` — full framework for large crawl jobs

### Data Processing
- `pydantic` — validate extracted data with schemas
- `pandas` — tabular data transformation
- `openpyxl` — Excel export

### Resilience
- `tenacity` — retry with exponential backoff
- `aiohttp` — async HTTP for concurrent requests
- `asyncio.Semaphore` — concurrency limiting

## Patterns

### Respectful Scraping
- Check robots.txt before scraping
- Set reasonable delays between requests (1-3s minimum)
- Use descriptive User-Agent strings
- Respect rate limits and HTTP 429 responses
- Cache responses to avoid redundant requests
- Prefer APIs and structured data over scraping when available

### Robust Parsing
- Use multiple selector strategies (CSS, XPath, label-based)
- Implement fallback extraction when primary selectors fail
- Validate extracted data against expected schemas
- Handle encoding issues (UTF-8, Windows-1251 for Russian sites)
- Strip whitespace and normalize text consistently

### Anti-Detection
- Rotate User-Agent strings from a realistic pool
- Rotate proxy IPs for high-volume scraping
- Add random delays between requests
- Handle CAPTCHAs gracefully (queue for manual solving or use services)
- Manage cookies and sessions properly

### Error Handling
- Retry on 429, 500, 502, 503, 504 with exponential backoff
- Log failed URLs for later retry
- Set request timeouts (connect: 10s, read: 30s)
- Handle connection errors, SSL errors, DNS failures
- Implement circuit breaker for consistently failing targets

### Data Quality
- Deduplicate by content hash or unique identifiers
- Track data freshness with fetch timestamps
- Compare new data against previous snapshots
- Flag anomalies (missing fields, unexpected values)
- Maintain raw HTML snapshots for debugging

## Example: Production Scraper Template

```python
import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

class ScrapedItem(BaseModel):
    url: str
    title: str
    content: str
    extracted_at: datetime

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
async def fetch_page(client: httpx.AsyncClient, url: str) -> str:
    resp = await client.get(url, timeout=30.0)
    resp.raise_for_status()
    return resp.text

async def parse_page(html: str, url: str) -> ScrapedItem:
    soup = BeautifulSoup(html, "lxml")
    return ScrapedItem(
        url=url,
        title=soup.select_one("h1").get_text(strip=True),
        content=soup.select_one(".content").get_text(strip=True),
        extracted_at=datetime.utcnow(),
    )
```

## Russian Web Specifics
Since this project targets Russian construction companies:
- Handle Windows-1251 and KOI8-R encodings
- Parse Russian-language labels (ИНН, ОГРН, КПП, etc.)
- Use Russian search engines (Yandex) for discovery
- Respect .ru domain conventions
- Handle Cyrillic text normalization
