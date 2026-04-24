"""Tests for scraper/crawler.py"""
import pytest
from unittest.mock import MagicMock, patch


FAKE_HTML_HOME = """
<html><body>
  <h1>ACME Corp</h1>
  <p>We make widgets.</p>
  <a href="/about">About</a>
  <a href="https://external.com/page">External</a>
</body></html>
"""

FAKE_HTML_ABOUT = """
<html><body>
  <h1>About Us</h1>
  <p>Founded in 2010.</p>
</body></html>
"""


def _mock_response(html: str, status: int = 200):
    resp = MagicMock()
    resp.status_code = status
    resp.text = html
    resp.raise_for_status = MagicMock()
    return resp


@patch("scraper.crawler.rate_limit")          # skip sleep
@patch("scraper.crawler.requests.Session")
def test_crawl_single_page(MockSession, mock_rl):
    """Single-page crawl returns one result with text."""
    mock_get = MockSession.return_value.get
    mock_get.return_value = _mock_response(FAKE_HTML_HOME)

    from scraper.crawler import Crawler
    crawler = Crawler(delay=0)
    results = crawler.crawl("https://acme.com", max_pages=1)

    assert len(results) == 1
    assert results[0]["url"] == "https://acme.com"
    assert "ACME Corp" in results[0]["text"]


@patch("scraper.crawler.rate_limit")
@patch("scraper.crawler.requests.Session")
def test_crawl_follows_links(MockSession, mock_rl):
    """Crawler follows internal links and respects max_pages."""
    mock_get = MockSession.return_value.get
    mock_get.side_effect = [
        _mock_response(FAKE_HTML_HOME),
        _mock_response(FAKE_HTML_ABOUT),
    ]

    from scraper.crawler import Crawler
    crawler = Crawler(delay=0)
    results = crawler.crawl("https://acme.com", max_pages=5, same_domain=True)

    urls = [r["url"] for r in results]
    assert "https://acme.com" in urls
    assert any("about" in u for u in urls)
    # External link should NOT be followed (same_domain=True)
    assert not any("external.com" in u for u in urls)


@patch("scraper.crawler.rate_limit")
@patch("scraper.crawler.requests.Session")
def test_crawl_respects_max_pages(MockSession, mock_rl):
    """Crawler never exceeds max_pages."""
    mock_get = MockSession.return_value.get
    mock_get.return_value = _mock_response(
        "<html><body><a href='/p1'>1</a><a href='/p2'>2</a><a href='/p3'>3</a></body></html>"
    )

    from scraper.crawler import Crawler
    crawler = Crawler(delay=0)
    results = crawler.crawl("https://acme.com", max_pages=2)

    assert len(results) <= 2


@patch("scraper.crawler.rate_limit")
@patch("scraper.crawler.requests.Session")
def test_crawl_handles_fetch_error(MockSession, mock_rl):
    """Crawler skips pages that return HTTP errors gracefully."""
    import requests as req_lib
    mock_get = MockSession.return_value.get
    mock_get.return_value.raise_for_status.side_effect = req_lib.RequestException("500")
    mock_get.return_value.text = ""

    from scraper.crawler import Crawler
    crawler = Crawler(delay=0)
    results = crawler.crawl("https://acme.com", max_pages=3)

    assert results == []
