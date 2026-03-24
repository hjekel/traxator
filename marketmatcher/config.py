"""MarketMatcher configuratie voor Kraakman Mechanisatie."""

# Bronnen configuratie
SOURCES = {
    "boerenbusiness": {
        "enabled": False,
        "url": "https://www.boerenbusiness.nl/marktplaats/categorie/tractoren",
        "type": "scrape",
    },
    "marktplaats": {
        "enabled": False,
        "url": "https://www.marktplaats.nl/l/agri/tractoren/",
        "type": "scrape",
    },
    "facebook": {
        "enabled": False,
        "url": "https://www.facebook.com/marketplace/category/farm-equipment",
        "type": "api",
    },
}

# John Deere modellen die Kraakman verkoopt/onderhoudt
JD_MODELS = {
    "5075E", "5090E", "5100E", "5115M",
    "6095MC", "6105MC", "6110M", "6120M", "6130M", "6140M",
    "6150R", "6155R", "6175R", "6195R", "6215R", "6230R", "6250R",
    "6R 150", "6R 155", "6R 175", "6R 185", "6R 195", "6R 215", "6R 230", "6R 250",
    "7R 270", "7R 290", "7R 310", "7R 330", "7R 350",
    "8R 280", "8R 310", "8R 340", "8R 370", "8R 410",
    "6M 180", "6M 185", "6M 190", "6M 195", "6M 200", "6M 210",
}

# Aliassen voor veelgebruikte afkortingen
MODEL_ALIASES = {
    "6150r": "6150R",
    "6155r": "6155R",
    "6175r": "6175R",
    "6195r": "6195R",
    "6215r": "6215R",
    "6230r": "6230R",
    "6r150": "6R 150",
    "6r155": "6R 155",
    "6r175": "6R 175",
    "6r185": "6R 185",
    "6r195": "6R 195",
    "6r215": "6R 215",
    "6r230": "6R 230",
    "6r250": "6R 250",
    "7r270": "7R 270",
    "7r290": "7R 290",
    "7r310": "7R 310",
    "7r330": "7R 330",
    "8r310": "8R 310",
    "8r340": "8R 340",
    "8r370": "8R 370",
    "8r410": "8R 410",
    "6m180": "6M 180",
    "6m200": "6M 200",
    "6m210": "6M 210",
}

# Kraakman vestigingen
LOCATIONS = {
    "Creil": {"lat": 52.73, "lon": 5.65, "tel": "0527-272727"},
    "Dronten": {"lat": 52.53, "lon": 5.72, "tel": "0321-313131"},
    "Emmeloord": {"lat": 52.71, "lon": 5.75, "tel": "0527-616161"},
    "Kraggenburg": {"lat": 52.66, "lon": 5.90, "tel": "0527-252525"},
    "Marknesse": {"lat": 52.71, "lon": 5.86, "tel": "0527-242424"},
    "Nagele": {"lat": 52.64, "lon": 5.81, "tel": "0527-232323"},
    "Rutten": {"lat": 52.76, "lon": 5.77, "tel": "0527-262626"},
    "Tollebeek": {"lat": 52.72, "lon": 5.82, "tel": "0527-282828"},
}

DEALER_NAME = "Kraakman Mechanisatie"
DEALER_BRAND = "John Deere"
