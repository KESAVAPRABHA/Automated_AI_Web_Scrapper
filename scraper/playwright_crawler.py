"""
Playwright-based crawler for JavaScript-heavy / SPA websites.
Falls back gracefully if playwright is not installed.
"""
import logging
import sys
import asyncio
from typing import Dict, List, Tuple

# Fix for Playwright/asyncio NotImplementedError on Windows
if sys.platform == 'win32':
    try:
        if not isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

from utils.helpers import (
    deduplicate,
    is_same_domain,
    normalize_url,
    rate_limit,
)

logger = logging.getLogger(__name__)

# JS that strips noise and returns clean visible text
_EXTRACT_TEXT_JS = """() => {
    const el = document.body.cloneNode(true);
    el.querySelectorAll(
        'script,style,noscript,iframe,path,svg,head,meta,link'
    ).forEach(n => n.remove());
    // Also strip hidden elements
    el.querySelectorAll('[style*="display:none"],[style*="display: none"],[hidden]')
      .forEach(n => n.remove());
    const text = el.innerText || el.textContent || '';
    // Collapse excessive whitespace
    return text.replace(/\\n{3,}/g, '\\n\\n').trim();
}"""


class PlaywrightCrawler:
    """
    Chromium-based crawler using Playwright (sync API).

    Use when the target site requires JavaScript to render content.

    Parameters
    ----------
    delay : float
        Seconds to wait between page navigations.
    headless : bool
        Run browser headlessly (no visible window).
    """

    def __init__(self, delay: float = 1.5, headless: bool = True) -> None:
        self.delay = delay
        self.headless = headless

    # ── Private helpers ────────────────────────────────────────────────────────

    def _fetch_page(self, page, url: str) -> Tuple[str, str]:
        """Navigate to *url* and return (html, visible_text)."""
        try:
            # Step 1: Navigate — try networkidle first, fall back to domcontentloaded
            try:
                page.goto(url, timeout=30_000, wait_until="networkidle")
            except Exception:
                try:
                    page.goto(url, timeout=30_000, wait_until="domcontentloaded")
                except Exception as e:
                    logger.warning("[Playwright] goto failed for %s: %s", url, e)
                    return "", ""

            # Step 2: Greedy wait — wait for common content containers
            try:
                page.wait_for_selector(
                    "table, .table, .list, .item, .product, .job, article, main, "
                    ".quote, .quotes, [class*='quote'], [class*='content']",
                    timeout=10_000,
                )
            except Exception:
                pass  # Continue even if specific selectors don't show up

            # Step 3: Multi-scroll to trigger lazy-loading / AJAX pagination
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1500)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(500)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)

            # Step 4: Extract clean text and HTML
            html: str = page.content()
            text: str = page.evaluate(_EXTRACT_TEXT_JS)
            return html, text
        except Exception as exc:
            logger.warning("[Playwright] Error on %s: %s", url, exc)
            return "", ""

    def _extract_links(self, page, base_url: str) -> List[str]:
        """Return all absolute hrefs found on the current page."""
        try:
            hrefs: List[str] = page.evaluate(
                "() => Array.from(document.querySelectorAll('a[href]')).map(a => a.href)"
            )
        except Exception:
            hrefs = []
        return [normalize_url(h) for h in hrefs if h.startswith("http")]

    # ── Public API ─────────────────────────────────────────────────────────────

    def crawl(
        self,
        start_url: str,
        max_pages: int = 10,
        same_domain: bool = True,
    ) -> List[Dict]:
        """Crawl from *start_url* using a headless Chromium browser."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise RuntimeError(
                "playwright is not installed. Run: pip install playwright && playwright install chromium"
            )

        start_url = normalize_url(start_url)
        visited: set = set()
        queue: List[str] = [start_url]
        results: List[Dict] = []

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                # Disable image loading for faster crawls
                java_script_enabled=True,
            )
            # Block images and fonts for speed
            context.route(
                "**/*.{png,jpg,jpeg,gif,webp,svg,woff,woff2,ttf,eot}",
                lambda route: route.abort(),
            )
            page = context.new_page()

            while queue and len(results) < max_pages:
                url = queue.pop(0)
                if url in visited:
                    continue
                visited.add(url)

                logger.info(
                    "[Playwright] %d/%d  %s", len(results) + 1, max_pages, url
                )
                html, text = self._fetch_page(page, url)
                if not text.strip():
                    logger.warning("[Playwright] Empty text for %s — skipping", url)
                    continue

                results.append({"url": url, "text": text, "html": html})
                logger.info("[Playwright] Extracted %d chars from %s", len(text), url)

                links = self._extract_links(page, url)
                if same_domain:
                    links = [lnk for lnk in links if is_same_domain(start_url, lnk)]
                for lnk in deduplicate(links):
                    if lnk not in visited:
                        queue.append(lnk)

                rate_limit(self.delay)

            browser.close()

        logger.info("[Playwright] Finished. %d pages crawled.", len(results))
        return results
