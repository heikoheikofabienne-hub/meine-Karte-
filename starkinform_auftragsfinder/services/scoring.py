"""Transparente Akquise-Score-Logik für Starkinform-Leads."""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

RELEVANCE_TERMS = {
    "graffiti", "wandgestaltung", "fassade", "fassadengestaltung", "street art", "mural",
    "wandmalerei", "trafostation", "trafo", "energiehaus", "verteilerkasten", "stromkasten",
    "schule", "kita", "schulhof", "workshop", "kunst am bau", "innenraum", "stadtwerke",
}
HIGH_SIGNAL_TERMS = {
    "ausschreibung", "vergabe", "interessenbekundung", "angebot einholen", "künstler gesucht",
    "gestaltung geplant", "sanierung geplant", "aufwertung", "verschönerung", "vandalismus",
    "schmierereien", "graffiti entfernen", "prävention", "stadtbild", "fördermittel",
    "quartiersmanagement", "bürgerprojekt", "kunst am bau",
}
BUDGET_TERMS = {"fassade", "fassadensanierung", "stadtwerke", "trafostation", "kunst am bau", "neubau", "sanierung", "quartier", "showroom", "hotel"}
PRESTIGE_TERMS = {"stadt", "gemeinde", "kommune", "stadtwerke", "schule", "kita", "öffentlich", "bahnhof", "unterführung", "wohnungsbau"}
CONTACT_TERMS = {"kontakt", "ansprechpartner", "presse", "rathaus", "stadtwerke", "impressum", "ausschreibung"}

CATEGORY_HINTS = {
    "Stadtwerke / Energieversorger": {"stadtwerke", "trafostation", "trafo", "energiehaus", "netzstation", "ladesäule"},
    "Kommunen / Städte / Gemeinden": {"stadt", "gemeinde", "kommune", "stadtbild", "unterführung", "bahnhof", "amtsblatt"},
    "Schulen / Kitas / Jugendclubs": {"schule", "kita", "jugendclub", "schulhof", "workshop", "jugendprojekt"},
    "Firmen / Gewerbe": {"firma", "unternehmen", "büro", "showroom", "hotel", "gastronomie", "autohaus", "fitnessstudio"},
    "Ausschreibungen": {"ausschreibung", "vergabe", "leistungsverzeichnis", "angebot"},
    "Fassadengestaltung": {"fassade", "fassadengestaltung", "mural"},
    "Graffiti-Prävention": {"schmierereien", "vandalismus", "graffiti entfernen", "prävention"},
}


def _text(lead: dict) -> str:
    fields = ["title", "description", "category", "organization_name", "location_name", "source_name"]
    return " ".join(str(lead.get(field) or "").lower() for field in fields)


def count_terms(text: str, terms: set[str]) -> int:
    return sum(1 for term in terms if term in text)


def distance_score(distance_km: Optional[float]) -> int:
    if distance_km is None:
        return 7
    if distance_km <= 50:
        return 15
    if distance_km <= 100:
        return 12
    if distance_km <= 150:
        return 9
    if distance_km <= 300:
        return 5
    return 1


def urgency_score(lead: dict) -> int:
    text = _text(lead)
    points = 4 + min(4, count_terms(text, HIGH_SIGNAL_TERMS))
    published_at = lead.get("published_at") or lead.get("discovered_at")
    if published_at:
        try:
            age = (date.today() - datetime.fromisoformat(published_at[:10]).date()).days
            if age <= 2:
                points += 2
            elif age <= 14:
                points += 1
        except ValueError:
            pass
    return min(10, points)


def categorize(lead: dict) -> str:
    text = _text(lead)
    for category, hints in CATEGORY_HINTS.items():
        if any(hint in text for hint in hints):
            return category
    return lead.get("category") or "Sonstiges"


def score_breakdown(lead: dict) -> dict[str, int]:
    text = _text(lead)
    relevance = min(25, 6 + count_terms(text, RELEVANCE_TERMS) * 4 + count_terms(text, HIGH_SIGNAL_TERMS) * 2)
    probability = min(20, 5 + count_terms(text, HIGH_SIGNAL_TERMS) * 4 + (4 if "gesucht" in text or "plant" in text else 0))
    budget = min(15, 4 + count_terms(text, BUDGET_TERMS) * 3)
    prestige = min(10, 2 + count_terms(text, PRESTIGE_TERMS) * 2)
    contactability = min(5, (3 if lead.get("organization_website") or lead.get("source_url") else 1) + count_terms(text, CONTACT_TERMS))
    return {
        "relevance_score": relevance,
        "distance_score": distance_score(lead.get("distance_from_greiz_km")),
        "probability_score": probability,
        "budget_score": budget,
        "urgency_score": urgency_score(lead),
        "prestige_score": prestige,
        "contactability_score": contactability,
    }


def calculate_total_score(lead: dict) -> int:
    parts = score_breakdown(lead)
    return max(0, min(100, sum(parts.values())))


def traffic_light(score: int) -> str:
    if score >= 85:
        return "Rot"
    if score >= 70:
        return "Orange"
    if score >= 50:
        return "Gelb"
    return "Grau"


def recommended_action(score: int) -> str:
    if score >= 85:
        return "Sofort anrufen oder kurze Erstmail senden"
    if score >= 70:
        return "Kurzfristig recherchieren und kontaktieren"
    if score >= 50:
        return "Beobachten oder weich mit Referenzen ansprechen"
    if score >= 30:
        return "Niedrige Priorität, nur bei Kapazität prüfen"
    return "Archivieren"
