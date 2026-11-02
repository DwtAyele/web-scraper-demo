"""Scrape book data from books.toscrape.com into CSV and Excel.

books.toscrape.com is a public sandbox site built for practicing web scraping.

Usage:
    python scraper.py --pages 3 --out output/books
"""
import argparse
import csv
import logging
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

START_URL = "https://books.toscrape.com/catalogue/page-1.html"
RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
log = logging.getLogger("scraper")


@dataclass
class Book:
    title: str
    price_gbp: float
    rating: int
    in_stock: bool
    url: str


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0 (demo scraper; contact via GitHub)"
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://", HTTPAdapter(max_retries=retry))
    return s


def parse_page(html: str, page_url: str) -> tuple[list[Book], str | None]:
    """Return the books on one catalogue page and the URL of the next page (or None)."""
    soup = BeautifulSoup(html, "html.parser")
    books = []
    for pod in soup.select("article.product_pod"):
        link = pod.select_one("h3 a")
        price_text = pod.select_one("p.price_color").get_text()
        rating_cls = [c for c in pod.select_one("p.star-rating")["class"] if c != "star-rating"]
        books.append(Book(
            title=link["title"].strip(),
            price_gbp=float(re.sub(r"[^\d.]", "", price_text)),
            rating=RATINGS.get(rating_cls[0], 0) if rating_cls else 0,
            in_stock="in stock" in pod.select_one("p.availability").get_text().lower(),
            url=urljoin(page_url, link["href"]),
        ))
    nxt = soup.select_one("li.next a")
    return books, (urljoin(page_url, nxt["href"]) if nxt else None)


def scrape(max_pages: int, delay: float = 1.0, session: requests.Session | None = None,
           start_url: str = START_URL) -> list[Book]:
    session = session or make_session()
    url, results, page = start_url, [], 0
    while url and page < max_pages:
        page += 1
        log.info("Page %d: %s", page, url)
        resp = session.get(url, timeout=20)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        books, url = parse_page(resp.text, resp.url)
        results.extend(books)
        if url:
            time.sleep(delay)  # be polite to the server
    return results


def save(books: list[Book], out_base: Path) -> None:
    out_base.parent.mkdir(parents=True, exist_ok=True)
    rows = [asdict(b) for b in books]
    with open(out_base.with_suffix(".csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else list(Book.__annotations__))
        w.writeheader()
        w.writerows(rows)
    try:
        import pandas as pd
        pd.DataFrame(rows).to_excel(out_base.with_suffix(".xlsx"), index=False)
    except ImportError:
        log.warning("pandas/openpyxl not installed: skipped Excel output")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--pages", type=int, default=3, help="how many catalogue pages to scrape (site has 50)")
    p.add_argument("--delay", type=float, default=1.0, help="seconds to wait between pages")
    p.add_argument("--out", type=Path, default=Path("output/books"), help="output path without extension")
    p.add_argument("--start-url", default=START_URL, help="first catalogue page (use http:// if https fails)")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    books = scrape(args.pages, args.delay, start_url=args.start_url)
    save(books, args.out)
    log.info("Saved %d books to %s.csv and .xlsx", len(books), args.out)


if __name__ == "__main__":
    main()
