"""Matching engine - koppelt zoekvragen aan voorraad met scoring."""

import re
from parser import parse_wanted_ad

# Geschat vermogen (pk) per model
MODEL_PK = {
    "5075E": 75, "5090E": 90, "5100E": 100, "5115M": 115,
    "6095MC": 95, "6105MC": 105, "6110M": 110, "6120M": 120,
    "6130M": 130, "6140M": 140,
    "6150R": 150, "6155R": 155, "6175R": 175, "6195R": 195,
    "6215R": 215, "6230R": 230, "6250R": 250,
    "6R 150": 150, "6R 155": 155, "6R 175": 175, "6R 185": 185,
    "6R 195": 195, "6R 215": 215, "6R 230": 230, "6R 250": 250,
    "7R 270": 270, "7R 290": 290, "7R 310": 310, "7R 330": 330, "7R 350": 350,
    "8R 280": 280, "8R 310": 310, "8R 340": 340, "8R 370": 370, "8R 410": 410,
    "6M 180": 180, "6M 185": 185, "6M 190": 190, "6M 195": 195,
    "6M 200": 200, "6M 210": 210,
}


def get_series(model):
    """Haal de serie uit een modelnaam, bijv. '6R 250' -> '6R', '6155R' -> '6R'."""
    m = re.match(r'^(\d[A-Za-z])', model)
    if m:
        return m.group(1).upper()
    # Voor modellen als "6155R" -> "6R"
    m2 = re.match(r'^(\d)\d+([A-Za-z])', model)
    if m2:
        return (m2.group(1) + m2.group(2)).upper()
    return None


def get_model_number(model):
    """Haal het nummer uit een model, bijv. '6R 250' -> 250, '6155R' -> 155."""
    nums = re.findall(r'(\d{2,3})', model)
    if len(nums) >= 2:
        return int(nums[-1])
    elif nums:
        return int(nums[0])
    return None


def score_match(parsed, item):
    """Bereken een matchscore tussen een geparsede zoekvraag en een voorraaditem."""
    score = 0
    reasons = []

    model = item["model"]
    model_pk = MODEL_PK.get(model, 0)
    model_series = get_series(model)
    model_number = get_model_number(model)

    # Exact model match (+40)
    if model in parsed["models"]:
        score += 40
        reasons.append(f"Exact model: {model} (+40)")

    # Model range match (+35)
    elif parsed.get("model_range"):
        r = parsed["model_range"]
        if model_series == r["series"] and r["low"] <= model_number <= r["high"]:
            score += 35
            reasons.append(f"In range {r['series']} {r['low']}-{r['high']} (+35)")

    # Zelfde serie (+20)
    if parsed.get("series"):
        target_series = parsed["series"] if isinstance(parsed["series"], list) else [parsed["series"]]
        if model_series in target_series:
            score += 20
            reasons.append(f"Serie {model_series} match (+20)")

    # PK match (+15)
    if parsed.get("min_pk") and parsed.get("max_pk"):
        if parsed["min_pk"] <= model_pk <= parsed["max_pk"]:
            score += 15
            reasons.append(f"Vermogen {model_pk}pk in range {parsed['min_pk']}-{parsed['max_pk']} (+15)")
    elif parsed.get("min_pk"):
        if model_pk >= parsed["min_pk"]:
            score += 15
            reasons.append(f"Vermogen {model_pk}pk >= {parsed['min_pk']}pk (+15)")

    # Budget match (+20)
    price = item["price"]
    if parsed.get("budget_min") and parsed.get("budget_max"):
        if parsed["budget_min"] <= price <= parsed["budget_max"]:
            score += 20
            reasons.append(f"Prijs EUR {price:,} in budget (+20)")
        elif price <= parsed["budget_max"] * 1.1:
            score += 10
            reasons.append(f"Prijs EUR {price:,} dicht bij budget (+10)")
    elif parsed.get("budget_max"):
        if price <= parsed["budget_max"]:
            score += 20
            reasons.append(f"Prijs EUR {price:,} binnen budget (+20)")
        elif price <= parsed["budget_max"] * 1.1:
            score += 10
            reasons.append(f"Prijs EUR {price:,} net boven budget (+10)")

    # Uren match (+15)
    if parsed.get("max_hours"):
        if item["hours"] <= parsed["max_hours"]:
            score += 15
            reasons.append(f"Uren {item['hours']} <= max {parsed['max_hours']} (+15)")

    # Bouwjaar match (+10)
    if parsed.get("min_year"):
        if item["year"] >= parsed["min_year"]:
            score += 10
            reasons.append(f"Bouwjaar {item['year']} >= {parsed['min_year']} (+10)")

    # Features match (+5 elk)
    if parsed.get("features"):
        for feature in parsed["features"]:
            if feature in item.get("features", []):
                score += 5
                reasons.append(f"Feature: {feature} (+5)")

    # Lange voorraad bonus (+10)
    if item.get("stock_days", 0) >= 90:
        score += 10
        reasons.append(f"Lang op voorraad: {item['stock_days']} dagen (+10)")

    return {"score": score, "reasons": reasons}


def find_matches(wanted_ads, inventory, min_score=20):
    """Vind matches tussen zoekvragen en voorraad."""
    matches = []
    for ad in wanted_ads:
        parsed = parse_wanted_ad(ad["text"])
        ad_matches = []
        for item in inventory:
            result = score_match(parsed, item)
            if result["score"] >= min_score:
                ad_matches.append({
                    "ad": ad,
                    "parsed": parsed,
                    "item": item,
                    "score": result["score"],
                    "reasons": result["reasons"],
                })
        # Sorteer op score (hoogste eerst)
        ad_matches.sort(key=lambda x: x["score"], reverse=True)
        matches.extend(ad_matches)
    return matches


def format_match(match):
    """Formatteer een match voor CLI output."""
    lines = [
        f"  Score: {match['score']} punten",
        f"  Vraag: {match['ad']['id']} - {match['ad']['contact']}",
        f"    \"{match['ad']['text'][:80]}...\"" if len(match['ad']['text']) > 80 else f"    \"{match['ad']['text']}\"",
        f"  Aanbod: {match['item']['id']} - JD {match['item']['model']} ({match['item']['year']})",
        f"    EUR {match['item']['price']:,} | {match['item']['hours']} uur | {match['item']['location']}",
        f"  Scoring:",
    ]
    for reason in match["reasons"]:
        lines.append(f"    + {reason}")
    return "\n".join(lines)
