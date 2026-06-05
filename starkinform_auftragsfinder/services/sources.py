"""Vorbereitete, rechtssichere Quellenstruktur.

Keine Umgehung von Scraping-Sperren: Quellen, die manuell geprüft werden müssen,
werden als Suchlink oder Recherchehinweis gepflegt.
"""
from urllib.parse import quote_plus

PREPARED_SOURCES = [
    ("Kleinanzeigen", "Manuell zu prüfen", "https://www.kleinanzeigen.de/s-graffiti/k0", "Plattformbedingungen prüfen; kein Scraping im MVP."),
    ("MyHammer", "Manuell zu prüfen", "https://www.my-hammer.de/", "Suchlink speichern und manuell prüfen; kein Scraping."),
    ("Ausschreibungsportale", "Manuell zu prüfen", "https://www.service.bund.de/", "Offizielle Ausschreibungen manuell oder später per erlaubter Schnittstelle."),
    ("Kommunale Webseiten", "Manuell zu prüfen", "https://www.google.com/search?q=site%3A.de+Kommune+Kunst+am+Bau+Graffiti", "Kommunale Bekanntmachungen und Projektseiten prüfen."),
    ("Stadtwerke-Webseiten", "Manuell zu prüfen", "https://www.google.com/search?q=Stadtwerke+Trafostation+gestalten", "Stadtwerke-Seiten und Pressebereiche prüfen."),
    ("Wohnungsbaugesellschaften", "Manuell zu prüfen", "https://www.google.com/search?q=Wohnungsbaugesellschaft+Fassadengestaltung", "Wohnungsunternehmen und Quartiersprojekte prüfen."),
    ("Google-Suche", "Suchlink", "https://www.google.com/search?q=Graffiti+K%C3%BCnstler+gesucht+Th%C3%BCringen", "Vorbereitete Suchlinks je Keyword nutzen."),
    ("Lokale Nachrichten / Amtsblätter", "Später RSS/API", "https://www.google.com/search?q=Amtsblatt+Kunstprojekt+Graffiti+Th%C3%BCringen", "RSS nur verwenden, wenn öffentlich angeboten."),
]


def google_search_url(keyword: str, region: str = "Thüringen Sachsen Sachsen-Anhalt Bayern") -> str:
    return "https://www.google.com/search?q=" + quote_plus(f"{keyword} {region} Starkinform Auftrag")
