"""MarketMatcher CLI - proactief verkoopsysteem voor Kraakman Mechanisatie."""

import argparse
import sys
import os

# Voeg huidige directory toe aan path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DEALER_NAME, DEALER_BRAND, LOCATIONS
from demo_data import INVENTORY, WANTED_ADS
from parser import parse_wanted_ad, format_parsed
from matcher import find_matches, format_match
from alerts import generate_alerts_html, save_matches_json
from scraper import scrape_all


BANNER = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ███╗   ███╗ █████╗ ██████╗ ██╗  ██╗███████╗████████╗      ║
║   ████╗ ████║██╔══██╗██╔══██╗██║ ██╔╝██╔════╝╚══██╔══╝      ║
║   ██╔████╔██║███████║██████╔╝█████╔╝ █████╗     ██║         ║
║   ██║╚██╔╝██║██╔══██║██╔══██╗██╔═██╗ ██╔══╝     ██║         ║
║   ██║ ╚═╝ ██║██║  ██║██║  ██║██║  ██╗███████╗   ██║         ║
║   ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝         ║
║                                                              ║
║   MarketMatcher v1.0 - Proactief Verkoopsysteem              ║
║   Kraakman Mechanisatie | John Deere Dealer                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""


def show_inventory():
    """Toon de huidige voorraad."""
    print("\n" + "=" * 70)
    print("  VOORRAAD KRAAKMAN MECHANISATIE")
    print("=" * 70)
    print(f"  {'ID':<8} {'Model':<12} {'Jaar':<6} {'Uren':<7} {'Prijs':<12} {'Locatie':<12} {'Dagen'}")
    print("  " + "-" * 66)
    for item in INVENTORY:
        print(f"  {item['id']:<8} {item['model']:<12} {item['year']:<6} {item['hours']:<7} EUR {item['price']:<9,} {item['location']:<12} {item['stock_days']}")
    print(f"\n  Totaal: {len(INVENTORY)} tractoren op voorraad")


def show_wanted_ads():
    """Toon en parse zoekvragen."""
    print("\n" + "=" * 70)
    print("  ZOEKVRAGEN (WANTED ADS)")
    print("=" * 70)
    for ad in WANTED_ADS:
        print(f"\n  [{ad['id']}] {ad['source'].upper()} - {ad['date']}")
        print(f"  Contact: {ad['contact']}")
        print(f"  \"{ad['text']}\"")
        parsed = parse_wanted_ad(ad["text"])
        print(f"  --- Extracted specs ---")
        print(format_parsed(parsed))


def show_matches(matches):
    """Toon gevonden matches."""
    print("\n" + "=" * 70)
    print("  MATCHES")
    print("=" * 70)
    if not matches:
        print("  Geen matches gevonden.")
        return
    for i, match in enumerate(matches):
        print(f"\n  --- Match #{i+1} ---")
        print(format_match(match))
    print(f"\n  Totaal: {len(matches)} matches gevonden")


def show_summary(matches):
    """Toon samenvatting met actie-items."""
    print("\n" + "=" * 70)
    print("  SAMENVATTING & ACTIE-ITEMS")
    print("=" * 70)

    top = [m for m in matches if m["score"] >= 50]
    urgent = [m for m in matches if m["item"]["stock_days"] >= 90 and m["score"] >= 40]

    print(f"\n  Totaal matches: {len(matches)}")
    print(f"  Top matches (score >= 50): {len(top)}")
    print(f"  Urgente verkoop (lang op voorraad + match): {len(urgent)}")

    if top:
        print("\n  TOP ACTIE-ITEMS:")
        for i, m in enumerate(top[:5]):
            print(f"  {i+1}. Bel {m['ad']['contact']} over {m['item']['id']} JD {m['item']['model']}")
            print(f"     Score: {m['score']} | Bron: {m['ad']['source']} | Vestiging: {m['item']['location']}")

    if urgent:
        print("\n  URGENTE VOORRAAD-MATCHES (lang op voorraad):")
        for m in urgent:
            print(f"  ! {m['item']['id']} JD {m['item']['model']} ({m['item']['stock_days']} dagen) -> {m['ad']['contact']}")

    print("\n  Vestigingen:")
    for name, info in LOCATIONS.items():
        print(f"    {name}: {info['tel']}")


def run_demo():
    """Voer de volledige demo uit."""
    print(BANNER)
    print(f"  Dealer: {DEALER_NAME}")
    print(f"  Merk: {DEALER_BRAND}")
    print(f"  Vestigingen: {len(LOCATIONS)}")

    # Scraper status
    scrape_all()

    # Voorraad tonen
    show_inventory()

    # Zoekvragen tonen en parsen
    show_wanted_ads()

    # Matches berekenen
    matches = find_matches(WANTED_ADS, INVENTORY)
    show_matches(matches)

    # Output genereren
    print("\n" + "=" * 70)
    print("  OUTPUT GENEREREN")
    print("=" * 70)
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)
    save_matches_json(matches, os.path.join(output_dir, "matches.json"))
    generate_alerts_html(matches, os.path.join(output_dir, "alerts.html"))

    # Samenvatting
    show_summary(matches)

    print("\n  Demo compleet! Bekijk output/alerts.html voor het dashboard.\n")


def main():
    parser = argparse.ArgumentParser(description="MarketMatcher - Proactief verkoopsysteem")
    parser.add_argument("--demo", action="store_true", help="Draai volledige demo met voorbeelddata")
    parser.add_argument("--matches", action="store_true", help="Toon alleen matches")
    parser.add_argument("--alerts", action="store_true", help="Genereer alerts HTML")
    parser.add_argument("--add", metavar="TEXT", help="Voeg een zoekvraag toe en parse direct")

    args = parser.parse_args()

    if args.demo:
        run_demo()
    elif args.matches:
        matches = find_matches(WANTED_ADS, INVENTORY)
        show_matches(matches)
    elif args.alerts:
        matches = find_matches(WANTED_ADS, INVENTORY)
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        os.makedirs(output_dir, exist_ok=True)
        generate_alerts_html(matches, os.path.join(output_dir, "alerts.html"))
        save_matches_json(matches, os.path.join(output_dir, "matches.json"))
        print("Alerts gegenereerd in output/")
    elif args.add:
        print(f"\nParsing: \"{args.add}\"")
        parsed = parse_wanted_ad(args.add)
        print(format_parsed(parsed))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
