# Web Scraper Demo: Books to CSV and Excel

Collect product data from a website and save it as a clean spreadsheet.

This demo scrapes [books.toscrape.com](https://books.toscrape.com), a public sandbox site made for practicing web scraping. The same approach works for product catalogs, directories and listings.

## What it collects

| Column | Example |
| --- | --- |
| `title` | A Light in the Attic |
| `price_gbp` | 51.77 |
| `rating` | 3 (converted from the site's star rating) |
| `in_stock` | True |
| `url` | full link to the product page |

## Features

- Follows "next page" links automatically, with a `--pages` limit
- Waits between pages (`--delay`) so it doesn't overload the website
- Retries on temporary server errors (429 and 5xx)
- Cleans prices, including broken currency symbols like `Â£`
- Saves both **CSV** and **Excel**
- Offline tests use saved HTML pages, so they run without the internet

## Run it

```bash
pip install -r requirements.txt
python scraper.py --pages 3 --out output/books
```

This creates `output/books.csv` and `output/books.xlsx` (20 books per page). If your network blocks HTTPS for this site, add `--start-url http://books.toscrape.com/catalogue/page-1.html`.

## Tests

```bash
python -m pytest -q
```

## Responsible scraping

Only scrape sites that allow it. Check the site's terms and `robots.txt`, keep request rates low, and never collect personal data without permission.

## Tech

Python, requests, BeautifulSoup, pandas, pytest.

---
Need data collected from a website into a spreadsheet? I build custom Python scrapers and automation scripts.
