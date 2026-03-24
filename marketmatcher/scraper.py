"""Placeholder scraper voor Boerenbusiness, Marktplaats en Facebook."""

from config import SOURCES


def scrape_source(name, config):
    """Scrape een enkele bron (placeholder)."""
    print(f"  [{name}] Status: {'ACTIEF' if config['enabled'] else 'UITGESCHAKELD'}")
    if not config["enabled"]:
        return []
    print(f"  [{name}] Scraping {config['url']}...")
    print(f"  [{name}] Type: {config['type']}")
    # Placeholder - retourneer lege lijst
    return []


def scrape_all():
    """Scrape alle geconfigureerde bronnen."""
    print("\n=== Scraper Status ===")
    all_ads = []
    for name, config in SOURCES.items():
        ads = scrape_source(name, config)
        all_ads.extend(ads)
    print(f"\n  Totaal gevonden: {len(all_ads)} advertenties")
    print("  (Scrapers zijn uitgeschakeld in demo modus)")
    return all_ads
