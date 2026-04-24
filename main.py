
import argparse
import logging
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from scraper.crawler import Crawler
from scraper.playwright_crawler import PlaywrightCrawler
from ai.extractor import AIExtractor
from export.exporter import Exporter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-scraper",
        description="AI-powered web scraper: extract structured data from any website.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract leadership names from a company website
  python main.py --url https://stripe.com/about --fields "leadership names" --pages 2

  # Extract product listings and save as JSON
  python main.py --url https://books.toscrape.com --fields "title" "price" "rating" \\
      --pages 5 --format json --output books.json

  # Use Playwright for a JS-rendered site
  python main.py --url https://example-spa.com --fields "product name" "price" \\
      --js --pages 3
""",
    )
    parser.add_argument("--url", required=True, help="Starting URL to crawl")
    parser.add_argument(
        "--fields",
        nargs="+",
        required=True,
        metavar="FIELD",
        help="One or more data fields to extract (e.g. 'title' 'price' 'rating')",
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=5,
        metavar="N",
        help="Maximum number of pages to crawl (default: 5)",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "excel", "json"],
        default="csv",
        help="Output file format (default: csv)",
    )
    parser.add_argument(
        "--output",
        default="results.csv",
        help="Output file path (default: results.csv)",
    )
    parser.add_argument(
        "--js",
        action="store_true",
        help="Use Playwright for JavaScript-heavy / SPA websites",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        metavar="SECS",
        help="Delay between requests in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--all-domains",
        action="store_true",
        help="Follow links across all domains (default: same-domain only)",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # ── Crawl ──────────────────────────────────────────────────────────────────
    if args.js:
        logger.info("Using Playwright crawler (--js flag set)")
        crawler = PlaywrightCrawler(delay=args.delay)
    else:
        crawler = Crawler(delay=args.delay)

    logger.info("Crawling: %s  (max %d pages)", args.url, args.pages)
    pages = crawler.crawl(
        start_url=args.url,
        max_pages=args.pages,
        same_domain=not args.all_domains,
    )

    if not pages:
        logger.error("No pages could be crawled. Check the URL and try again.")
        sys.exit(1)

    logger.info("Crawled %d page(s). Extracting fields: %s", len(pages), args.fields)

    # ── Extract ────────────────────────────────────────────────────────────────
    extractor = AIExtractor()
    records = []
    for page in pages:
        extracted = extractor.extract(page["text"], args.fields, page["url"])
        # Only keep records that contain at least one non-null value
        if any(v is not None for v in extracted.values()):
            extracted["_source_url"] = page["url"]
            records.append(extracted)

    if not records:
        logger.warning(
            "No data extracted. Try different fields or increase --pages."
        )
        sys.exit(0)

    logger.info("Extracted %d record(s).", len(records))

    # ── Export ─────────────────────────────────────────────────────────────────
    exporter = Exporter()
    output_path = exporter.export(records, args.output, args.format)
    logger.info("✓ Saved → %s", output_path)


if __name__ == "__main__":
    main()
