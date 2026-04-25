import time
from urllib.parse import urlparse, urldefrag, urljoin
from typing import List


def normalize_url(url: str) -> str:
    #Strip fragments, trailing slashes, and ensure a protocol exists.
    url = url.strip()
    if not url:
        return ""
    if not (url.startswith("http://") or url.startswith("https://")):
        # Check if it looks like a relative path or a plain domain
        if "." in url.split("/")[0]: 
            url = "https://" + url
            
    url, _ = urldefrag(url)
    return url.rstrip("/")


def is_same_domain(base_url: str, target_url: str) -> bool:
    #Return True if target_url shares the same netloc as base_url
    base_netloc = urlparse(base_url).netloc
    target_netloc = urlparse(target_url).netloc
    # Allow relative-looking URLs (empty netloc)
    return target_netloc == "" or base_netloc == target_netloc


def deduplicate(urls: List[str]) -> List[str]:
    #Return unique URLs preserving insertion order.
    seen: set = set()
    result: List[str] = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            result.append(url)
    return result


def make_absolute(base_url: str, href: str) -> str:
    return urljoin(base_url, href)


def rate_limit(delay: float = 1.0) -> None:
    #Sleep for `delay` seconds to respect server rate limits.
    if delay > 0:
        time.sleep(delay)
