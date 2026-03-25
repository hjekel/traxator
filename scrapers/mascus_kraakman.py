#!/usr/bin/env python3
"""
MascusKraakmanScraper - Scrapes Mascus.nl for Kraakman John Deere tractors.

Usage:
    python mascus_kraakman.py                   # Full scrape, save JSON+CSV
    python mascus_kraakman.py --quick            # First page only
    python mascus_kraakman.py --pages 3          # First 3 pages
    python mascus_kraakman.py --export csv       # Export format (json/csv/both)
    python mascus_kraakman.py --output ./data    # Output directory
"""

import argparse
import csv
import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Installeer vereiste packages: pip install -r requirements.txt")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


# Kraakman vestigingen mapping
KRAAKMAN_LOCATIONS = {
    'steenbergen': 'Steenbergen',
    'maasdam': 'Maasdam',
    'dronten': 'Dronten',
    'oldehove': 'Oldehove',
    'lieshout': 'Lieshout',
    'reusel': 'Reusel',
    'hillegom': 'Hillegom',
    'koudekerk': 'Koudekerk a/d Rijn',
    'koudekerk a/d rijn': 'Koudekerk a/d Rijn',
    'koudekerk aan den rijn': 'Koudekerk a/d Rijn',
}


class MascusKraakmanScraper:
    """Scrapes Mascus.nl for Kraakman John Deere tractor listings."""

    BASE_URL = "https://www.mascus.nl"
    SEARCH_URL = (
        "https://www.mascus.nl/landbouw/gebruikte-tractoren/"
        "john-deere?dealer=kraakman"
    )

    HEADERS = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        ),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'nl-NL,nl;q=0.9,en;q=0.8',
    }

    # Rate limiting
    MIN_DELAY = 2.0  # seconds between requests
    MAX_DELAY = 5.0
    MAX_RETRIES = 3
    RETRY_BACKOFF = 2.0  # multiplier for retry delay

    def __init__(self, output_dir: str = "./output"):
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.listings: List[Dict] = []
        self._last_request_time = 0.0

        os.makedirs(output_dir, exist_ok=True)

    def _rate_limit(self):
        """Enforce minimum delay between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.MIN_DELAY:
            delay = self.MIN_DELAY - elapsed
            logger.debug(f"Rate limiting: waiting {delay:.1f}s")
            time.sleep(delay)

    def _fetch(self, url: str, retries: int = 0) -> Optional[str]:
        """Fetch URL with retry logic and rate limiting."""
        self._rate_limit()
        try:
            logger.info(f"Fetching: {url}")
            resp = self.session.get(url, timeout=30)
            self._last_request_time = time.time()

            if resp.status_code == 429:
                # Too Many Requests
                wait = min(self.RETRY_BACKOFF ** (retries + 1) * 10, 120)
                logger.warning(f"Rate limited (429). Waiting {wait:.0f}s...")
                time.sleep(wait)
                if retries < self.MAX_RETRIES:
                    return self._fetch(url, retries + 1)
                return None

            resp.raise_for_status()
            return resp.text

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            if retries < self.MAX_RETRIES:
                wait = self.RETRY_BACKOFF ** (retries + 1)
                logger.info(f"Retrying in {wait:.0f}s... (attempt {retries + 2}/{self.MAX_RETRIES + 1})")
                time.sleep(wait)
                return self._fetch(url, retries + 1)
            logger.error(f"Max retries exceeded for {url}")
            return None

    def _map_location(self, raw_location: str) -> str:
        """Map raw location text to Kraakman vestiging name."""
        if not raw_location:
            return "Onbekend"

        loc_lower = raw_location.lower().strip()

        # Direct match
        for key, value in KRAAKMAN_LOCATIONS.items():
            if key in loc_lower:
                return value

        # Try partial match on city names
        for key, value in KRAAKMAN_LOCATIONS.items():
            if key.split()[0] in loc_lower:
                return value

        return raw_location.strip()

    def _parse_listing(self, item_element) -> Optional[Dict]:
        """Parse a single listing element from the search results page."""
        try:
            listing = {}

            # Model name
            title_el = item_element.select_one('.listing-title, h3 a, .title a, [class*="title"]')
            if title_el:
                title_text = title_el.get_text(strip=True)
                # Remove "John Deere" prefix if present
                model = re.sub(r'^John\s*Deere\s*', '', title_text, flags=re.IGNORECASE)
                listing['model'] = model.strip()
            else:
                return None

            # Link
            link_el = item_element.select_one('a[href]')
            if link_el:
                listing['url'] = urljoin(self.BASE_URL, link_el['href'])

            # Price
            price_el = item_element.select_one('[class*="price"], .listing-price, .price')
            if price_el:
                price_text = price_el.get_text(strip=True)
                price_num = re.sub(r'[^\d]', '', price_text)
                listing['price'] = int(price_num) if price_num else 0
            else:
                listing['price'] = 0

            # Year
            year_el = item_element.select_one('[class*="year"], .listing-year')
            if year_el:
                year_text = year_el.get_text(strip=True)
                year_match = re.search(r'(19|20)\d{2}', year_text)
                listing['year'] = int(year_match.group()) if year_match else 0
            else:
                # Try to find year in specs
                specs = item_element.get_text()
                year_match = re.search(r'(20[0-2]\d)', specs)
                listing['year'] = int(year_match.group()) if year_match else 0

            # Hours
            hours_text = item_element.get_text()
            hours_match = re.search(r'(\d[\d.,]*)\s*(?:uur|hours?|hrs?|Betriebsstunden)', hours_text, re.IGNORECASE)
            if hours_match:
                hours_str = hours_match.group(1).replace('.', '').replace(',', '')
                listing['hours'] = int(hours_str)
            else:
                listing['hours'] = 0

            # Location
            loc_el = item_element.select_one('[class*="location"], .listing-location, .location')
            if loc_el:
                listing['location'] = self._map_location(loc_el.get_text(strip=True))
            else:
                listing['location'] = 'Onbekend'

            # Calculate days_in_stock (estimate based on when we first see it)
            listing['days_in_stock'] = 0
            listing['scraped_at'] = datetime.now().isoformat()

            return listing

        except Exception as e:
            logger.warning(f"Error parsing listing: {e}")
            return None

    def _get_page_count(self, html: str) -> int:
        """Extract total number of pages from search results."""
        soup = BeautifulSoup(html, 'html.parser')

        # Look for pagination
        pagination = soup.select('.pagination a, [class*="pager"] a, .page-numbers a')
        if pagination:
            page_nums = []
            for el in pagination:
                text = el.get_text(strip=True)
                if text.isdigit():
                    page_nums.append(int(text))
            return max(page_nums) if page_nums else 1

        return 1

    def scrape(self, max_pages: Optional[int] = None) -> List[Dict]:
        """
        Scrape Mascus.nl for Kraakman listings.

        Args:
            max_pages: Maximum number of pages to scrape (None = all)

        Returns:
            List of listing dictionaries
        """
        logger.info("Starting Mascus Kraakman scrape...")
        self.listings = []

        # Fetch first page
        html = self._fetch(self.SEARCH_URL)
        if not html:
            logger.error("Failed to fetch first page")
            return []

        total_pages = self._get_page_count(html)
        if max_pages:
            total_pages = min(total_pages, max_pages)

        logger.info(f"Found {total_pages} page(s) to scrape")

        # Process all pages
        for page in range(1, total_pages + 1):
            if page > 1:
                page_url = f"{self.SEARCH_URL}&page={page}"
                html = self._fetch(page_url)
                if not html:
                    logger.warning(f"Failed to fetch page {page}, stopping")
                    break

            soup = BeautifulSoup(html, 'html.parser')

            # Find listing items - try multiple selectors
            items = (
                soup.select('.listing-item') or
                soup.select('[class*="listing"]') or
                soup.select('.search-results .item') or
                soup.select('[data-listing-id]')
            )

            if not items:
                logger.warning(f"No listings found on page {page}")
                # Try broader selector
                items = soup.select('article, .result-item, [class*="result"]')

            page_count = 0
            for item in items:
                listing = self._parse_listing(item)
                if listing and listing.get('model'):
                    self.listings.append(listing)
                    page_count += 1

            logger.info(f"Page {page}/{total_pages}: found {page_count} listings")

        logger.info(f"Scrape complete: {len(self.listings)} total listings")
        return self.listings

    def save_json(self, filename: str = "kraakman_inventory.json") -> str:
        """Save listings to JSON file."""
        filepath = os.path.join(self.output_dir, filename)
        data = {
            'scraped_at': datetime.now().isoformat(),
            'source': 'mascus.nl',
            'dealer': 'Kraakman',
            'count': len(self.listings),
            'listings': self.listings
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved JSON: {filepath} ({len(self.listings)} listings)")
        return filepath

    def save_csv(self, filename: str = "kraakman_inventory.csv") -> str:
        """Save listings to CSV file."""
        filepath = os.path.join(self.output_dir, filename)
        if not self.listings:
            logger.warning("No listings to save")
            return filepath

        fieldnames = ['model', 'year', 'hours', 'price', 'location', 'days_in_stock', 'url', 'scraped_at']
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(self.listings)

        logger.info(f"Saved CSV: {filepath} ({len(self.listings)} listings)")
        return filepath

    def load_existing(self, filename: str = "kraakman_inventory.json") -> List[Dict]:
        """Load existing listings from JSON for days_in_stock tracking."""
        filepath = os.path.join(self.output_dir, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data.get('listings', [])
            except (json.JSONDecodeError, KeyError):
                return []
        return []

    def merge_with_existing(self, existing: List[Dict]):
        """Merge new listings with existing, tracking days_in_stock."""
        existing_map = {}
        for item in existing:
            key = f"{item.get('model', '')}_{item.get('year', '')}"
            existing_map[key] = item

        for listing in self.listings:
            key = f"{listing.get('model', '')}_{listing.get('year', '')}"
            if key in existing_map:
                old = existing_map[key]
                old_date = old.get('first_seen', old.get('scraped_at', ''))
                if old_date:
                    try:
                        first_seen = datetime.fromisoformat(old_date)
                        days = (datetime.now() - first_seen).days
                        listing['days_in_stock'] = max(days, 0)
                        listing['first_seen'] = old_date
                    except (ValueError, TypeError):
                        listing['first_seen'] = listing['scraped_at']
                        listing['days_in_stock'] = 0
            else:
                listing['first_seen'] = listing['scraped_at']
                listing['days_in_stock'] = 0


def main():
    parser = argparse.ArgumentParser(
        description='Mascus Kraakman John Deere Tractor Scraper'
    )
    parser.add_argument(
        '--quick', action='store_true',
        help='Quick mode: only scrape first page'
    )
    parser.add_argument(
        '--pages', type=int, default=None,
        help='Maximum number of pages to scrape'
    )
    parser.add_argument(
        '--export', choices=['json', 'csv', 'both'], default='both',
        help='Export format (default: both)'
    )
    parser.add_argument(
        '--output', type=str, default='./output',
        help='Output directory (default: ./output)'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = MascusKraakmanScraper(output_dir=args.output)

    # Load existing data for days_in_stock tracking
    existing = scraper.load_existing()

    # Determine max pages
    max_pages = 1 if args.quick else args.pages

    # Run scrape
    listings = scraper.scrape(max_pages=max_pages)

    if not listings:
        logger.warning("No listings found. Site structure may have changed.")
        logger.info("Check if Mascus.nl is accessible and the URL is correct.")
        return

    # Merge with existing for days tracking
    if existing:
        scraper.merge_with_existing(existing)
        logger.info(f"Merged with {len(existing)} existing listings")

    # Save results
    if args.export in ('json', 'both'):
        scraper.save_json()
    if args.export in ('csv', 'both'):
        scraper.save_csv()

    # Summary
    print(f"\n{'='*50}")
    print(f"Mascus Kraakman Scrape Resultaat")
    print(f"{'='*50}")
    print(f"Gevonden: {len(listings)} machines")
    if listings:
        avg_price = sum(l.get('price', 0) for l in listings) / len(listings)
        print(f"Gem. prijs: \u20ac {avg_price:,.0f}")

        # Per location
        locations = {}
        for l in listings:
            loc = l.get('location', 'Onbekend')
            locations[loc] = locations.get(loc, 0) + 1
        print(f"\nPer vestiging:")
        for loc, count in sorted(locations.items()):
            print(f"  {loc}: {count}")

    print(f"{'='*50}\n")


if __name__ == '__main__':
    main()
