"""
GitLab Handbook & Direction Pages Scraper
==========================================
Crawls GitLab handbook and direction pages, extracts clean text,
and saves structured data for downstream embedding.
"""

import json
import hashlib
import logging
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass, asdict

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Seed URLs ────────────────────────────────────────────────
SEED_URLS = [
    "https://handbook.gitlab.com/handbook/",
    "https://about.gitlab.com/direction/",
]

# Allowed URL prefixes to stay in scope
ALLOWED_PREFIXES = [
    "https://handbook.gitlab.com/handbook/",
    "https://about.gitlab.com/direction/",
]

MAX_PAGES = 500  # Safety cap — adjust as needed
REQUEST_DELAY = 1  # Seconds between requests (be polite)
REQUEST_TIMEOUT = 15


@dataclass
class ScrapedPage:
    url: str
    title: str
    content: str  # Cleaned plain text
    content_hash: str


def is_allowed(url: str) -> bool:
    """Check if a URL falls within allowed prefixes."""
    return any(url.startswith(prefix) for prefix in ALLOWED_PREFIXES)


def normalize_url(url: str) -> str:
    """Strip fragments and trailing slashes for dedup."""
    parsed = urlparse(url)
    clean = parsed._replace(fragment="").geturl()
    return clean.rstrip("/")


def extract_text(soup: BeautifulSoup) -> str:
    """Extract meaningful text from page, removing nav/footer/scripts."""
    # Remove non-content elements
    for tag in soup.find_all(["nav", "footer", "header", "script", "style", "aside"]):
        tag.decompose()

    # Try to find main content area
    main = soup.find("main") or soup.find("article") or soup.find("div", class_="content")
    target = main if main else soup.body

    if not target:
        return ""

    # Get text with spacing
    text = target.get_text(separator="\n", strip=True)

    # Clean up excessive blank lines
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def scrape_page(url: str, session: requests.Session) -> tuple[ScrapedPage | None, list[str]]:
    """Scrape a single page. Returns (page_data, discovered_links)."""
    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None, []

    content_type = resp.headers.get("content-type", "")
    if "text/html" not in content_type:
        return None, []

    soup = BeautifulSoup(resp.text, "html.parser")

    # Extract title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else url

    # Extract clean text
    content = extract_text(soup)
    if len(content) < 50:  # Skip near-empty pages
        logger.debug(f"Skipping {url} — too little content")
        return None, []

    content_hash = hashlib.md5(content.encode()).hexdigest()

    page = ScrapedPage(url=url, title=title, content=content, content_hash=content_hash)

    # Discover links
    links = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        full_url = normalize_url(urljoin(url, href))
        if is_allowed(full_url):
            links.append(full_url)

    return page, links


def crawl(max_pages: int = MAX_PAGES) -> list[ScrapedPage]:
    """BFS crawl starting from seed URLs."""
    visited: set[str] = set()
    queue: list[str] = [normalize_url(u) for u in SEED_URLS]
    pages: list[ScrapedPage] = []
    seen_hashes: set[str] = set()

    session = requests.Session()
    session.headers.update({
        "User-Agent": "GitLabHandbookBot/1.0 (educational project)"
    })

    while queue and len(pages) < max_pages:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)

        logger.info(f"[{len(pages)+1}/{max_pages}] Scraping: {url}")
        page, links = scrape_page(url, session)

        if page and page.content_hash not in seen_hashes:
            seen_hashes.add(page.content_hash)
            pages.append(page)

        # Add new links to queue
        for link in links:
            if link not in visited:
                queue.append(link)

        time.sleep(REQUEST_DELAY)

    logger.info(f"Crawl complete. Scraped {len(pages)} pages.")
    return pages


def save_pages(pages: list[ScrapedPage], output_path: str = "scraped_pages.json"):
    """Save scraped pages to JSON."""
    data = [asdict(p) for p in pages]
    Path(output_path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Saved {len(pages)} pages to {output_path}")


if __name__ == "__main__":
    pages = crawl(max_pages=MAX_PAGES)
    save_pages(pages, output_path="scraped_pages.json")
