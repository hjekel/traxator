# MarketMatcher

Proactief verkoopsysteem voor Kraakman Mechanisatie / John Deere.

Matcht tractoren op voorraad met zoekvragen van potentiele kopers op Boerenbusiness, Marktplaats en Facebook Marketplace.

## Gebruik

```bash
pip install -r requirements.txt
python main.py --demo
python main.py --matches
python main.py --alerts
```

## Features

- Parsed zoekvragen (model, bouwjaar, uren, budget, features)
- Scoring-engine met gewogen matching
- HTML alerts dashboard met John Deere branding
- JSON export voor verdere integratie
