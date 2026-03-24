"""Parser voor zoekvragen - extraheert specificaties uit vrije tekst."""

import re
from config import JD_MODELS, MODEL_ALIASES


def parse_wanted_ad(text):
    """Parse een zoekvraag en extraheer gestructureerde specificaties."""
    text_lower = text.lower()
    parsed = {
        "models": [],
        "series": None,
        "min_year": None,
        "max_hours": None,
        "budget_min": None,
        "budget_max": None,
        "min_pk": None,
        "max_pk": None,
        "features": [],
        "raw_text": text,
    }

    # Exacte modellen zoeken
    for model in JD_MODELS:
        if model.lower() in text_lower:
            parsed["models"].append(model)

    # Aliassen checken
    for alias, model in MODEL_ALIASES.items():
        if alias in text_lower and model not in parsed["models"]:
            parsed["models"].append(model)

    # Model range: "6R 150-185", "7R 270-310"
    range_match = re.search(r'(\d[A-Za-z])\s*(\d{2,3})\s*[-–]\s*(\d{2,3})', text)
    if range_match:
        series_prefix = range_match.group(1).upper()
        range_low = int(range_match.group(2))
        range_high = int(range_match.group(3))
        parsed["model_range"] = {
            "series": series_prefix,
            "low": range_low,
            "high": range_high,
        }
    else:
        parsed["model_range"] = None

    # Serie: "6M serie", "7R serie", "5E serie", "8R serie"
    series_match = re.search(r'(\d[A-Za-z])\s*serie', text_lower)
    if series_match:
        parsed["series"] = series_match.group(1).upper()

    # Specifieke serie referenties: "7R of 8R serie"
    multi_series = re.findall(r'(\d[A-Za-z])\s*(?:of|en|/)\s*(\d[A-Za-z])\s*serie', text_lower)
    if multi_series:
        parsed["series"] = [s.upper() for pair in multi_series for s in pair]

    # Bouwjaar: "niet ouder dan 2020", "bouwjaar 2018-2021", "2020+"
    year_match = re.search(r'niet ouder dan\s*(\d{4})', text_lower)
    if year_match:
        parsed["min_year"] = int(year_match.group(1))
    year_range = re.search(r'bouwjaar\s*(\d{4})\s*[-–]\s*(\d{4})', text_lower)
    if year_range:
        parsed["min_year"] = int(year_range.group(1))
    year_plus = re.search(r'(\d{4})\+', text_lower)
    if year_plus:
        parsed["min_year"] = int(year_plus.group(1))

    # Uren: "max 3000 uur", "maximaal 2000 uur"
    hours_match = re.search(r'max(?:imaal)?\s*(\d+)\s*uur', text_lower)
    if hours_match:
        parsed["max_hours"] = int(hours_match.group(1))

    # Budget: "budget 100-140k", "max 130k", "tot 65k", "budget 60-80k"
    budget_range = re.search(r'budget\s*(\d+)\s*[-–]\s*(\d+)\s*k', text_lower)
    if budget_range:
        parsed["budget_min"] = int(budget_range.group(1)) * 1000
        parsed["budget_max"] = int(budget_range.group(2)) * 1000
    budget_max = re.search(r'(?:max|tot)\s*(\d+)\s*k', text_lower)
    if budget_max and not budget_range:
        parsed["budget_max"] = int(budget_max.group(1)) * 1000
    budget_range_full = re.search(r'budget\s*(\d+)\s*[-–]\s*(\d+)k', text_lower)
    if budget_range_full:
        parsed["budget_min"] = int(budget_range_full.group(1)) * 1000
        parsed["budget_max"] = int(budget_range_full.group(2)) * 1000

    # PK/vermogen: "180+ pk", "120-140 pk", "280-350 pk"
    pk_range = re.search(r'(\d+)\s*[-–]\s*(\d+)\s*pk', text_lower)
    if pk_range:
        parsed["min_pk"] = int(pk_range.group(1))
        parsed["max_pk"] = int(pk_range.group(2))
    pk_min = re.search(r'(\d+)\+\s*pk', text_lower)
    if pk_min:
        parsed["min_pk"] = int(pk_min.group(1))

    # Features
    feature_keywords = {
        "gps": "GPS",
        "frontloader": "frontloader",
        "frontlader": "frontloader",
        "airco": "airco",
        "commandpro": "CommandPRO",
        "commandcenter": "CommandCenter",
        "autotrac": "AutoTrac",
        "ivt": "IVT",
        "kruipversnelling": "kruipversnelling",
        "pto": "frontPTO",
    }
    for keyword, feature in feature_keywords.items():
        if keyword in text_lower and feature not in parsed["features"]:
            parsed["features"].append(feature)

    return parsed


def format_parsed(parsed):
    """Formatteer geparsede specificaties voor weergave."""
    lines = []
    if parsed["models"]:
        lines.append(f"  Modellen: {', '.join(parsed['models'])}")
    if parsed.get("model_range"):
        r = parsed["model_range"]
        lines.append(f"  Model range: {r['series']} {r['low']}-{r['high']}")
    if parsed["series"]:
        if isinstance(parsed["series"], list):
            lines.append(f"  Serie: {', '.join(parsed['series'])}")
        else:
            lines.append(f"  Serie: {parsed['series']}")
    if parsed["min_year"]:
        lines.append(f"  Min. bouwjaar: {parsed['min_year']}")
    if parsed["max_hours"]:
        lines.append(f"  Max. uren: {parsed['max_hours']}")
    if parsed["budget_min"] and parsed["budget_max"]:
        lines.append(f"  Budget: EUR {parsed['budget_min']:,} - {parsed['budget_max']:,}")
    elif parsed["budget_max"]:
        lines.append(f"  Budget: tot EUR {parsed['budget_max']:,}")
    if parsed["min_pk"] and parsed["max_pk"]:
        lines.append(f"  Vermogen: {parsed['min_pk']}-{parsed['max_pk']} pk")
    elif parsed["min_pk"]:
        lines.append(f"  Vermogen: {parsed['min_pk']}+ pk")
    if parsed["features"]:
        lines.append(f"  Features: {', '.join(parsed['features'])}")
    return "\n".join(lines) if lines else "  (geen specificaties herkend)"
