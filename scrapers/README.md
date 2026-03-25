# TraxaTor Scrapers

Python scrapers for collecting John Deere tractor market data.

## Setup

```bash
pip install -r requirements.txt
```

## Mascus Kraakman Scraper

Scrapes Mascus.nl for Kraakman John Deere tractor listings.

### Usage

```bash
# Full scrape (all pages)
python mascus_kraakman.py

# Quick mode (first page only)
python mascus_kraakman.py --quick

# Limit pages
python mascus_kraakman.py --pages 3

# Export format
python mascus_kraakman.py --export csv
python mascus_kraakman.py --export json
python mascus_kraakman.py --export both

# Custom output directory
python mascus_kraakman.py --output ./data
```

### Output

- `kraakman_inventory.json` - Full listing data with metadata
- `kraakman_inventory.csv` - CSV compatible with TraxaTor import

### Features

- Rate limiting (2-5s between requests)
- Retry logic with exponential backoff
- Location mapping to Kraakman vestigingen
- Days-in-stock tracking across runs
- CLI with --quick, --pages, --export flags

## Wanted Ads Scraper

Collects "wanted" advertisements for tractors from various sources.

### Usage

```bash
# Manual entry mode
python wanted_ads_scraper.py --add

# List current ads
python wanted_ads_scraper.py --list

# Export
python wanted_ads_scraper.py --export json
```

## CSV Format (TraxaTor compatible)

```
model,year,hours,price,location,days_in_stock
6R 155,2021,3200,145000,Steenbergen,120
```

## Kraakman Vestigingen

- Steenbergen
- Maasdam
- Dronten
- Oldehove
- Lieshout
- Reusel
- Hillegom
- Koudekerk a/d Rijn
