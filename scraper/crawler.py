#requests + BeautifulSoup crawler.
#Handles static/server-rendered pages; for JS-heavy sites use PlaywrightCrawler.
import logging
from typing import Dict, List, Tuple

import requests
from bs4 import BeautifulSoup

from utils.helpers import (
    deduplicate,
    is_same_domain,
    make_absolute,
    normalize_url,
    rate_limit,
)

logger = logging.getLogger(__name__)

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# Tags whose content we strip before extracting text
_NOISE_TAGS = ["script", "style", "noscript", "header", "footer", "nav", "aside"]


class Crawler:
    """
    Breadth-first web crawler using requests + BeautifulSoup.

    Parameters
    ----------
    delay : float
        Seconds to wait between requests.
    timeout : int
        HTTP request timeout in seconds.
    """

    def __init__(self, delay: float = 1.0, timeout: int = 15) -> None:
        self.delay = delay
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(_DEFAULT_HEADERS)

    # ── Private helpers ────────────────────────────────────────────────────────

    def _fetch(self, url: str) -> Tuple[str, str]:
        """Return (html, cleaned_text) for *url*, or ("", "") on error."""
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            html = resp.text
            soup = BeautifulSoup(html, "lxml")
            for tag in soup(_NOISE_TAGS):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            return html, text
        except requests.RequestException as exc:
            logger.warning("Fetch failed for %s: %s", url, exc)
            return "", ""

    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """Extract all absolute hrefs from *html*."""
        soup = BeautifulSoup(html, "lxml")
        links: List[str] = []
        for anchor in soup.find_all("a", href=True):
            absolute = make_absolute(base_url, anchor["href"])
            normalized = normalize_url(absolute)
            if normalized.startswith("http"):
                links.append(normalized)
        return links

    # ── Public API ─────────────────────────────────────────────────────────────

    def crawl(
        self,
        start_url: str,
        max_pages: int = 10,
        same_domain: bool = True,
    ) -> List[Dict]:
        """
        Crawl from *start_url* and return a list of page dicts.

        Each dict has keys: ``url``, ``text``, ``html``.
        """
        start_url = normalize_url(start_url)
        visited: set = set()
        queue: List[str] = [start_url]
        results: List[Dict] = []

        while queue and len(results) < max_pages:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            logger.info("[Crawler] %d/%d  %s", len(results) + 1, max_pages, url)
            html, text = self._fetch(url)
            if not text.strip():
                continue

            results.append({"url": url, "text": text, "html": html})

            # Discover outbound links
            links = self._extract_links(html, url)
            if same_domain:
                links = [lnk for lnk in links if is_same_domain(start_url, lnk)]
            for lnk in deduplicate(links):
                if lnk not in visited:
                    queue.append(lnk)

            rate_limit(self.delay)

        logger.info("[Crawler] Finished. %d pages crawled.", len(results))
        return results
