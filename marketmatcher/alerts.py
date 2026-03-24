"""HTML alerts generator en JSON export."""

import json
import os
from datetime import datetime


def generate_alerts_html(matches, output_path="output/alerts.html"):
    """Genereer een HTML alerts pagina met John Deere branding."""
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else "output", exist_ok=True)

    # Statistieken
    unique_ads = len(set(m["ad"]["id"] for m in matches))
    unique_items = len(set(m["item"]["id"] for m in matches))
    avg_score = sum(m["score"] for m in matches) / len(matches) if matches else 0
    top_matches = [m for m in matches if m["score"] >= 50]

    # Match cards HTML
    match_cards = ""
    for i, m in enumerate(matches):
        score = m["score"]
        if score >= 70:
            badge_color = "#367c2b"
            badge_text = "UITSTEKEND"
        elif score >= 50:
            badge_color = "#f5a623"
            badge_text = "GOED"
        else:
            badge_color = "#666"
            badge_text = "MOGELIJK"

        features_html = ""
        for f in m["item"].get("features", []):
            features_html += f'<span style="background:#e8f5e9;color:#367c2b;padding:2px 8px;border-radius:12px;font-size:0.8em;margin:2px;">{f}</span> '

        reasons_html = ""
        for r in m["reasons"]:
            reasons_html += f'<div style="color:#555;font-size:0.85em;">+ {r}</div>'

        match_cards += f'''
        <div style="background:white;border-radius:12px;padding:20px;margin:15px 0;box-shadow:0 2px 8px rgba(0,0,0,0.1);border-left:4px solid {badge_color};">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                <h3 style="margin:0;color:#333;">Match #{i+1}</h3>
                <div>
                    <span style="background:{badge_color};color:white;padding:4px 12px;border-radius:20px;font-weight:bold;font-size:0.9em;">{badge_text}</span>
                    <span style="background:#333;color:white;padding:4px 12px;border-radius:20px;font-size:0.9em;margin-left:5px;">{score} pts</span>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;">
                <div style="background:#fff8e1;padding:12px;border-radius:8px;">
                    <div style="font-weight:bold;color:#f57f17;margin-bottom:5px;">VRAAG ({m["ad"]["id"]})</div>
                    <div style="font-size:0.9em;color:#333;">{m["ad"]["text"][:120]}</div>
                    <div style="font-size:0.85em;color:#666;margin-top:5px;">Bron: {m["ad"]["source"]} | {m["ad"]["contact"]}</div>
                </div>
                <div style="background:#e8f5e9;padding:12px;border-radius:8px;">
                    <div style="font-weight:bold;color:#367c2b;margin-bottom:5px;">AANBOD ({m["item"]["id"]})</div>
                    <div style="font-size:0.9em;color:#333;">JD {m["item"]["model"]} ({m["item"]["year"]})</div>
                    <div style="font-size:0.85em;color:#666;">EUR {m["item"]["price"]:,} | {m["item"]["hours"]} uur | {m["item"]["location"]}</div>
                    <div style="margin-top:5px;">{features_html}</div>
                </div>
            </div>
            <div style="margin-top:10px;padding:10px;background:#f5f5f5;border-radius:8px;">
                <div style="font-weight:bold;font-size:0.85em;color:#333;margin-bottom:5px;">Scoring Details:</div>
                {reasons_html}
            </div>
            <div style="margin-top:12px;text-align:right;">
                <a href="tel:0527-272727" style="background:#367c2b;color:white;padding:8px 16px;border-radius:6px;text-decoration:none;font-size:0.9em;">Bel Kraakman</a>
                <a href="mailto:verkoop@kraakman.nl?subject=Match {m['item']['id']} - JD {m['item']['model']}" style="background:#ffde00;color:#333;padding:8px 16px;border-radius:6px;text-decoration:none;font-size:0.9em;margin-left:8px;">Email Verkoop</a>
            </div>
        </div>'''

    html = f'''<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MarketMatcher Alerts - Kraakman Mechanisatie</title>
</head>
<body style="margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f0f2f5;">
    <div style="background:linear-gradient(135deg,#367c2b 0%,#2d6b23 100%);color:white;padding:30px 40px;">
        <h1 style="margin:0;font-size:1.8em;">MarketMatcher Alerts</h1>
        <p style="margin:5px 0 0;opacity:0.9;">Kraakman Mechanisatie - John Deere Dealer</p>
        <p style="margin:5px 0 0;opacity:0.7;font-size:0.9em;">Gegenereerd: {datetime.now().strftime("%d-%m-%Y %H:%M")}</p>
    </div>

    <div style="max-width:900px;margin:20px auto;padding:0 20px;">
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin-bottom:20px;">
            <div style="background:white;padding:20px;border-radius:12px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                <div style="font-size:2em;font-weight:bold;color:#367c2b;">{len(matches)}</div>
                <div style="color:#666;font-size:0.9em;">Totaal Matches</div>
            </div>
            <div style="background:white;padding:20px;border-radius:12px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                <div style="font-size:2em;font-weight:bold;color:#367c2b;">{len(top_matches)}</div>
                <div style="color:#666;font-size:0.9em;">Top Matches (50+)</div>
            </div>
            <div style="background:white;padding:20px;border-radius:12px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                <div style="font-size:2em;font-weight:bold;color:#367c2b;">{unique_ads}</div>
                <div style="color:#666;font-size:0.9em;">Unieke Vragen</div>
            </div>
            <div style="background:white;padding:20px;border-radius:12px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                <div style="font-size:2em;font-weight:bold;color:#367c2b;">{avg_score:.0f}</div>
                <div style="color:#666;font-size:0.9em;">Gem. Score</div>
            </div>
        </div>

        {match_cards}

        <div style="text-align:center;padding:30px;color:#999;font-size:0.85em;">
            MarketMatcher v1.0 | Kraakman Mechanisatie | Powered by Traxator
        </div>
    </div>
</body>
</html>'''

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  HTML alerts opgeslagen: {output_path}")
    return output_path


def save_matches_json(matches, output_path="output/matches.json"):
    """Sla matches op als JSON."""
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else "output", exist_ok=True)

    export = []
    for m in matches:
        export.append({
            "score": m["score"],
            "ad_id": m["ad"]["id"],
            "ad_source": m["ad"]["source"],
            "ad_contact": m["ad"]["contact"],
            "ad_text": m["ad"]["text"],
            "item_id": m["item"]["id"],
            "item_model": m["item"]["model"],
            "item_year": m["item"]["year"],
            "item_price": m["item"]["price"],
            "item_hours": m["item"]["hours"],
            "item_location": m["item"]["location"],
            "reasons": m["reasons"],
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export, f, indent=2, ensure_ascii=False)
    print(f"  JSON matches opgeslagen: {output_path}")
    return output_path
