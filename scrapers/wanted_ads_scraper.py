#!/usr/bin/env python3
"""
WantedAdsScraper - Collects "wanted" advertisements for John Deere tractors.

Supports manual entry and placeholder methods for Boerenbusiness and Marktplaats.
Data is saved to JSON for integration with TraxaTor.

Usage:
    python wanted_ads_scraper.py --add                  # Add ad manually (interactive)
    python wanted_ads_scraper.py --list                  # List all saved ads
    python wanted_ads_scraper.py --export json           # Export to JSON
    python wanted_ads_scraper.py --export csv            # Export to CSV
    python wanted_ads_scraper.py --delete <id>           # Delete ad by ID
    python wanted_ads_scraper.py --scan boerenbusiness   # Placeholder scan
    python wanted_ads_scraper.py --scan marktplaats      # Placeholder scan
"""

import argparse
import csv
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


KRAAKMAN_LOCATIONS = [
    'Steenbergen', 'Maasdam', 'Dronten', 'Oldehove',
    'Lieshout', 'Reusel', 'Hillegom', 'Koudekerk a/d Rijn'
]


class WantedAdsScraper:
    """Collects wanted/gevraagd advertisements for John Deere tractors."""

    def __init__(self, data_dir: str = "./output"):
        self.data_dir = data_dir
        self.data_file = os.path.join(data_dir, "wanted_ads.json")
        self.ads: List[Dict] = []
        os.makedirs(data_dir, exist_ok=True)
        self.load()

    def load(self) -> List[Dict]:
        """Load existing ads from JSON."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.ads = data.get('ads', [])
                logger.info(f"Loaded {len(self.ads)} existing ads")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Could not load existing data: {e}")
                self.ads = []
        return self.ads

    def save(self):
        """Save ads to JSON."""
        data = {
            'updated_at': datetime.now().isoformat(),
            'count': len(self.ads),
            'ads': self.ads
        }
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(self.ads)} ads to {self.data_file}")

    def _next_id(self) -> int:
        """Get next available ID."""
        if not self.ads:
            return 1
        return max(ad.get('id', 0) for ad in self.ads) + 1

    def add_manual_ad(
        self,
        model: str,
        year_min: int = 0,
        year_max: int = 0,
        hours_max: int = 0,
        budget_max: int = 0,
        buyer_name: str = "",
        buyer_phone: str = "",
        buyer_email: str = "",
        region: str = "",
        source: str = "handmatig",
        notes: str = "",
        url: str = ""
    ) -> Dict:
        """
        Add a wanted ad manually.

        Args:
            model: Tractor model (e.g., "6R 150-185" or "7R 310")
            year_min: Minimum year wanted
            year_max: Maximum year wanted
            hours_max: Maximum hours acceptable
            budget_max: Maximum budget in EUR
            buyer_name: Buyer contact name
            buyer_phone: Buyer phone number
            buyer_email: Buyer email
            region: Buyer region/location
            source: Ad source (handmatig, boerenbusiness, marktplaats, etc.)
            notes: Additional notes
            url: URL of original ad (if from website)

        Returns:
            The created ad dictionary
        """
        ad = {
            'id': self._next_id(),
            'model': model,
            'year_min': year_min,
            'year_max': year_max,
            'hours_max': hours_max,
            'budget_max': budget_max,
            'buyer_name': buyer_name,
            'buyer_phone': buyer_phone,
            'buyer_email': buyer_email,
            'region': region,
            'source': source,
            'notes': notes,
            'url': url,
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        self.ads.append(ad)
        self.save()
        logger.info(f"Added ad #{ad['id']}: {model} (bron: {source})")
        return ad

    def delete_ad(self, ad_id: int) -> bool:
        """Delete an ad by ID."""
        original_count = len(self.ads)
        self.ads = [ad for ad in self.ads if ad.get('id') != ad_id]
        if len(self.ads) < original_count:
            self.save()
            logger.info(f"Deleted ad #{ad_id}")
            return True
        logger.warning(f"Ad #{ad_id} not found")
        return False

    def update_status(self, ad_id: int, status: str) -> bool:
        """Update ad status (active, matched, expired, closed)."""
        for ad in self.ads:
            if ad.get('id') == ad_id:
                ad['status'] = status
                ad['updated_at'] = datetime.now().isoformat()
                self.save()
                logger.info(f"Updated ad #{ad_id} status to '{status}'")
                return True
        return False

    def list_ads(self, status: Optional[str] = None) -> List[Dict]:
        """List all ads, optionally filtered by status."""
        if status:
            return [ad for ad in self.ads if ad.get('status') == status]
        return self.ads

    def match_inventory(self, inventory: List[Dict]) -> List[Dict]:
        """
        Match wanted ads against inventory.

        Args:
            inventory: List of inventory items (from TraxaTor/Mascus)

        Returns:
            List of matches: [{'ad': ad, 'matches': [inventory_items]}]
        """
        results = []
        for ad in self.ads:
            if ad.get('status') != 'active':
                continue

            matches = []
            model_pattern = ad.get('model', '').lower()

            for item in inventory:
                item_model = item.get('model', '').lower()

                # Model match (fuzzy)
                if model_pattern and model_pattern not in item_model:
                    # Try partial match
                    model_parts = model_pattern.split()
                    if not any(part in item_model for part in model_parts):
                        continue

                # Year filter
                year = item.get('year', 0)
                if ad.get('year_min') and year < ad['year_min']:
                    continue
                if ad.get('year_max') and year > ad['year_max']:
                    continue

                # Hours filter
                hours = item.get('hours', 0)
                if ad.get('hours_max') and hours > ad['hours_max']:
                    continue

                # Budget filter
                price = item.get('price', 0)
                if ad.get('budget_max') and price > ad['budget_max']:
                    continue

                matches.append(item)

            if matches:
                results.append({
                    'ad': ad,
                    'matches': matches
                })

        return results

    def export_csv(self, filename: str = "wanted_ads.csv") -> str:
        """Export ads to CSV."""
        filepath = os.path.join(self.data_dir, filename)
        if not self.ads:
            logger.warning("No ads to export")
            return filepath

        fieldnames = [
            'id', 'model', 'year_min', 'year_max', 'hours_max',
            'budget_max', 'buyer_name', 'region', 'source', 'status',
            'notes', 'created_at'
        ]
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(self.ads)

        logger.info(f"Exported CSV: {filepath}")
        return filepath

    # ==========================================
    # Placeholder scrapers (not implemented)
    # ==========================================

    def scan_boerenbusiness(self, max_pages: int = 1) -> List[Dict]:
        """
        Placeholder: Scan Boerenbusiness.nl for wanted tractor ads.

        NOTE: Not implemented - Boerenbusiness has complex auth/session
        requirements and dynamic content loading. Manual entry recommended.
        """
        logger.warning(
            "Boerenbusiness scraper is a placeholder. "
            "Site uses complex authentication and dynamic loading. "
            "Use --add for manual entry of found ads."
        )
        print("\n--- Boerenbusiness Scan (Placeholder) ---")
        print("Automatisch scrapen van Boerenbusiness.nl is niet")
        print("geimplementeerd vanwege complexe authenticatie.")
        print("")
        print("Tip: Zoek handmatig op boerenbusiness.nl/gevraagd")
        print("en voeg gevonden advertenties toe met --add")
        print("-------------------------------------------\n")
        return []

    def scan_marktplaats(self, max_pages: int = 1) -> List[Dict]:
        """
        Placeholder: Scan Marktplaats.nl for wanted tractor ads.

        NOTE: Not implemented - Marktplaats uses heavy anti-bot
        protection (Akamai) and requires API access.
        Manual entry recommended.
        """
        logger.warning(
            "Marktplaats scraper is a placeholder. "
            "Site uses heavy anti-bot protection. "
            "Use --add for manual entry of found ads."
        )
        print("\n--- Marktplaats Scan (Placeholder) ---")
        print("Automatisch scrapen van Marktplaats.nl is niet")
        print("geimplementeerd vanwege anti-bot beveiliging (Akamai).")
        print("")
        print("Tip: Zoek handmatig op marktplaats.nl")
        print("categorie: Agrarisch > Tractoren")
        print("en voeg gevonden advertenties toe met --add")
        print("--------------------------------------\n")
        return []


def interactive_add(scraper: WantedAdsScraper):
    """Interactive mode to add a wanted ad."""
    print("\n=== Nieuwe gevraagd-advertentie toevoegen ===\n")

    model = input("Model (bijv. 6R 155, 7R 270-310): ").strip()
    if not model:
        print("Model is verplicht.")
        return

    year_min = input("Bouwjaar vanaf (leeg = geen min): ").strip()
    year_min = int(year_min) if year_min.isdigit() else 0

    year_max = input("Bouwjaar t/m (leeg = geen max): ").strip()
    year_max = int(year_max) if year_max.isdigit() else 0

    hours_max = input("Max draaiuren (leeg = geen max): ").strip()
    hours_max = int(hours_max) if hours_max.isdigit() else 0

    budget_max = input("Max budget EUR (leeg = geen max): ").strip()
    budget_max = int(budget_max) if budget_max.isdigit() else 0

    buyer_name = input("Naam koper (optioneel): ").strip()
    buyer_phone = input("Telefoon koper (optioneel): ").strip()
    buyer_email = input("Email koper (optioneel): ").strip()
    region = input("Regio koper (optioneel): ").strip()

    print("\nBron: 1=Handmatig  2=Boerenbusiness  3=Marktplaats  4=Anders")
    source_choice = input("Keuze [1]: ").strip()
    sources = {'1': 'handmatig', '2': 'boerenbusiness', '3': 'marktplaats', '4': 'anders'}
    source = sources.get(source_choice, 'handmatig')

    notes = input("Notities (optioneel): ").strip()
    url = input("URL advertentie (optioneel): ").strip()

    ad = scraper.add_manual_ad(
        model=model,
        year_min=year_min,
        year_max=year_max,
        hours_max=hours_max,
        budget_max=budget_max,
        buyer_name=buyer_name,
        buyer_phone=buyer_phone,
        buyer_email=buyer_email,
        region=region,
        source=source,
        notes=notes,
        url=url
    )

    print(f"\nAdvertentie #{ad['id']} toegevoegd!")
    print(f"  Model: {ad['model']}")
    if year_min or year_max:
        print(f"  Bouwjaar: {year_min or '?'} - {year_max or '?'}")
    if hours_max:
        print(f"  Max uren: {hours_max:,}")
    if budget_max:
        print(f"  Max budget: \u20ac {budget_max:,}")
    print()


def print_ads(ads: List[Dict]):
    """Print ads in a formatted table."""
    if not ads:
        print("Geen advertenties gevonden.\n")
        return

    print(f"\n{'ID':>4}  {'Model':<20} {'Jaar':<12} {'Max uren':>10} {'Budget':>12} {'Bron':<15} {'Status':<10}")
    print("-" * 95)

    for ad in ads:
        year_range = ""
        if ad.get('year_min') or ad.get('year_max'):
            year_range = f"{ad.get('year_min', '?')}-{ad.get('year_max', '?')}"

        hours = f"{ad['hours_max']:,}" if ad.get('hours_max') else "-"
        budget = f"\u20ac {ad['budget_max']:,}" if ad.get('budget_max') else "-"

        print(f"{ad['id']:>4}  {ad['model']:<20} {year_range:<12} {hours:>10} {budget:>12} {ad.get('source', '-'):<15} {ad.get('status', '-'):<10}")

    print(f"\nTotaal: {len(ads)} advertenties\n")


def main():
    parser = argparse.ArgumentParser(
        description='Wanted Ads Scraper - Gevraagd advertenties voor John Deere tractoren'
    )
    parser.add_argument(
        '--add', action='store_true',
        help='Advertentie handmatig toevoegen (interactief)'
    )
    parser.add_argument(
        '--list', action='store_true',
        help='Alle advertenties tonen'
    )
    parser.add_argument(
        '--active', action='store_true',
        help='Alleen actieve advertenties tonen'
    )
    parser.add_argument(
        '--delete', type=int, metavar='ID',
        help='Advertentie verwijderen (op ID)'
    )
    parser.add_argument(
        '--close', type=int, metavar='ID',
        help='Advertentie sluiten (op ID)'
    )
    parser.add_argument(
        '--scan', choices=['boerenbusiness', 'marktplaats'],
        help='Scan bron (placeholder - niet volledig geimplementeerd)'
    )
    parser.add_argument(
        '--export', choices=['json', 'csv'],
        help='Exporteer advertenties'
    )
    parser.add_argument(
        '--output', type=str, default='./output',
        help='Output directory (default: ./output)'
    )
    parser.add_argument(
        '--match', type=str, metavar='INVENTORY_JSON',
        help='Match advertenties tegen inventaris JSON bestand'
    )

    args = parser.parse_args()

    scraper = WantedAdsScraper(data_dir=args.output)

    if args.add:
        interactive_add(scraper)

    elif args.list or args.active:
        status = 'active' if args.active else None
        ads = scraper.list_ads(status=status)
        print_ads(ads)

    elif args.delete is not None:
        if scraper.delete_ad(args.delete):
            print(f"Advertentie #{args.delete} verwijderd.")
        else:
            print(f"Advertentie #{args.delete} niet gevonden.")

    elif args.close is not None:
        if scraper.update_status(args.close, 'closed'):
            print(f"Advertentie #{args.close} gesloten.")
        else:
            print(f"Advertentie #{args.close} niet gevonden.")

    elif args.scan:
        if args.scan == 'boerenbusiness':
            scraper.scan_boerenbusiness()
        elif args.scan == 'marktplaats':
            scraper.scan_marktplaats()

    elif args.export:
        if args.export == 'csv':
            path = scraper.export_csv()
            print(f"Exported to: {path}")
        elif args.export == 'json':
            scraper.save()
            print(f"Exported to: {scraper.data_file}")

    elif args.match:
        if not os.path.exists(args.match):
            print(f"Bestand niet gevonden: {args.match}")
            return
        with open(args.match, 'r', encoding='utf-8') as f:
            inv_data = json.load(f)
        inventory = inv_data.get('listings', inv_data) if isinstance(inv_data, dict) else inv_data

        matches = scraper.match_inventory(inventory)
        if matches:
            print(f"\n=== {len(matches)} Matches gevonden ===\n")
            for m in matches:
                ad = m['ad']
                print(f"Advertentie #{ad['id']}: {ad['model']}")
                if ad.get('buyer_name'):
                    print(f"  Koper: {ad['buyer_name']}")
                print(f"  Matches: {len(m['matches'])} machines")
                for item in m['matches']:
                    print(f"    - {item.get('model', '?')} ({item.get('year', '?')}) "
                          f"{item.get('hours', 0):,} uur "
                          f"\u20ac {item.get('price', 0):,}")
                print()
        else:
            print("Geen matches gevonden.")

    else:
        # Default: show summary
        ads = scraper.list_ads()
        active = [a for a in ads if a.get('status') == 'active']
        print(f"\n=== Wanted Ads Overzicht ===")
        print(f"Totaal: {len(ads)} advertenties ({len(active)} actief)")
        if ads:
            print_ads(active if active else ads)
        else:
            print("Geen advertenties. Gebruik --add om te beginnen.\n")
        parser.print_help()


if __name__ == '__main__':
    main()
