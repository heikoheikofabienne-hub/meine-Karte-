"""Rechtssichere Quellen- und Suchcluster-Konfiguration.

Die Live-Suche nutzt bevorzugt öffentliche RSS-/API-Endpunkte und gespeicherte
Suchlinks. Es werden keine Logins, Captchas oder technische Sperren umgangen.
"""
from __future__ import annotations

from urllib.parse import quote_plus

SEARCH_CLUSTERS = {
    "Direkte Aufträge": [
        "Graffiti Künstler gesucht", "Wandgestaltung gesucht", "Fassadengestaltung gesucht",
        "Street Art Auftrag", "Mural Künstler gesucht", "Wandmalerei Firma", "Trafostation gestalten",
        "Trafohaus gestalten", "Energiehaus gestalten", "Schulhof gestalten", "Kita Wandgestaltung",
        "Graffiti Workshop", "Graffiti Projekt Schule", "Fassadenkunst", "Künstler für Wandgestaltung",
        "Gestaltung Verteilerkasten", "Stromkasten gestalten",
    ],
    "Frühe Bedarfssignale": [
        "Schmierereien Stadt", "illegale Graffiti entfernen", "Vandalismus Trafostation",
        "Graffiti an Schule", "Graffiti Unterführung", "Stadtbild verschönern", "graue Verteilerkästen",
        "triste Fassade", "Verschönerung Innenstadt", "Bürger beschweren sich über Graffiti",
        "Graffiti Prävention", "saubere Stadt", "Jugendliche Kunstprojekt", "Kunst im öffentlichen Raum",
        "Stadtmöbel Gestaltung", "Ortsbild verbessern",
    ],
    "Stadtwerke und Energie": [
        "Stadtwerke Trafostation", "Stadtwerke Energiehaus", "Netzstation Gestaltung", "Trafohäuschen",
        "E-Mobilität Stadtwerke", "Ladesäule Stadtwerke", "Energieversorgung Gestaltung",
        "Stadtwerke Nachhaltigkeit Projekt", "Stadtwerke Imagekampagne", "Stadtwerke Stadtbild",
        "Stadtwerke Sponsoring Kunst", "Stadtwerke Graffiti", "Stadtwerke Vandalismus",
    ],
    "Kommunale Bau- und Sanierungsprojekte": [
        "Sanierung Schule", "Neubau Kita", "Jugendclub Sanierung", "Schwimmbad Sanierung",
        "Sporthalle Sanierung", "Wohngebiet Aufwertung", "Quartiersentwicklung", "Stadtumbau",
        "Fördermittel Stadtentwicklung", "Fassadensanierung öffentliches Gebäude", "Spielplatz Neugestaltung",
        "Unterführung Sanierung", "Bahnhofsumfeld Gestaltung", "Bushaltestelle Gestaltung",
    ],
    "Firmen und Innenräume": [
        "Firmengebäude Neugestaltung", "Bürogestaltung", "Wandgestaltung Büro",
        "Innenraumgestaltung Unternehmen", "Showroom Gestaltung", "Empfangsbereich gestalten",
        "Werkhalle Gestaltung", "Kantine Wandgestaltung", "Fitnessstudio Wandgestaltung",
        "Autohaus Wandgestaltung", "Hotel Wandgestaltung", "Gastronomie Wandgestaltung",
    ],
}

PREPARED_SOURCES = [
    ("Google News RSS", "RSS", "https://news.google.com/rss/search?q=Graffiti+Th%C3%BCringen&hl=de&gl=DE&ceid=DE:de", "Öffentlicher News-RSS-Feed für legale Live-Suche."),
    ("Bing Web Search API", "API", "https://api.bing.microsoft.com/v7.0/search", "Optional: BING_API_KEY in Einstellungen/Umgebung hinterlegen."),
    ("Service Bund / Vergaben", "Suchlink", "https://www.service.bund.de/", "Offizielle Vergaben und Ausschreibungen prüfen."),
    ("TED EU Ausschreibungen", "Suchlink", "https://ted.europa.eu/de/", "Öffentliches EU-Vergabeportal."),
    ("Kommunale Pressemitteilungen", "Suchlink", "https://www.google.com/search?q=site%3A.de+Pressemitteilung+Stadtbild+Graffiti+Th%C3%BCringen", "Kommunale Webseiten/Pressebereiche rechtssicher manuell oder per RSS anbinden."),
    ("Stadtwerke-Webseiten", "Suchlink", "https://www.google.com/search?q=Stadtwerke+Trafostation+Graffiti+Th%C3%BCringen", "Stadtwerke-Projekte, Pressebereiche und RSS-Feeds."),
    ("Wohnungsbaugesellschaften", "Suchlink", "https://www.google.com/search?q=Wohnungsbaugesellschaft+Fassadengestaltung+Sachsen", "Quartiersaufwertung und Fassadenprojekte."),
    ("Kleinanzeigen", "Manuell zu prüfen", "https://www.kleinanzeigen.de/s-graffiti/k0", "Nur öffentliche Suchseiten/Benachrichtigungen nutzen; kein Scraping."),
    ("MyHammer", "Manuell zu prüfen", "https://www.my-hammer.de/", "Nur legale Schnittstellen oder manuelle Recherche nutzen."),
]


def google_search_url(keyword: str, region: str = "Thüringen Sachsen Sachsen-Anhalt Bayern Hessen") -> str:
    return "https://www.google.com/search?q=" + quote_plus(f"{keyword} {region}")


def google_news_rss_url(keyword: str, region: str = "Thüringen Sachsen Sachsen-Anhalt Bayern Hessen") -> str:
    return "https://news.google.com/rss/search?q=" + quote_plus(f"{keyword} {region}") + "&hl=de&gl=DE&ceid=DE:de"
