"""Offline tests: they parse saved HTML, so they never hit the real website."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import scraper  # noqa: E402

FIX = Path(__file__).parent / "fixtures"
URL = "https://books.toscrape.com/catalogue/page-1.html"


def test_parse_books_and_next_link():
    books, nxt = scraper.parse_page((FIX / "page-1.html").read_text(encoding="utf-8"), URL)
    assert [b.title for b in books] == ["A Light in the Attic", "Tipping the Velvet"]
    assert books[0].price_gbp == 51.77 and books[0].rating == 3 and books[0].in_stock
    assert books[1].price_gbp == 53.74 and books[1].rating == 1 and not books[1].in_stock
    assert books[0].url == "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    assert nxt == "https://books.toscrape.com/catalogue/page-2.html"


def test_last_page_has_no_next():
    books, nxt = scraper.parse_page((FIX / "last-page.html").read_text(encoding="utf-8"), URL)
    assert len(books) == 1 and books[0].rating == 5 and nxt is None


class FakeResp:
    def __init__(self, text, url):
        self.text, self.url, self.encoding = text, url, None

    def raise_for_status(self):
        pass


class FakeSession:
    def __init__(self):
        self.pages = {
            URL: (FIX / "page-1.html").read_text(encoding="utf-8"),
            "https://books.toscrape.com/catalogue/page-2.html": (FIX / "last-page.html").read_text(encoding="utf-8"),
        }
        self.calls = []

    def get(self, url, timeout):
        self.calls.append(url)
        return FakeResp(self.pages[url], url)


def test_scrape_follows_pages_and_stops(tmp_path):
    s = FakeSession()
    books = scraper.scrape(max_pages=10, delay=0, session=s)
    assert len(books) == 3 and len(s.calls) == 2
    scraper.save(books, tmp_path / "books")
    assert (tmp_path / "books.csv").read_text(encoding="utf-8").splitlines()[0] == "title,price_gbp,rating,in_stock,url"


def test_max_pages_limit():
    s = FakeSession()
    assert len(scraper.scrape(max_pages=1, delay=0, session=s)) == 2 and len(s.calls) == 1
