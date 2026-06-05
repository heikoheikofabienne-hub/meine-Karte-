"""Bewertungslogik für potenzielle Aufträge.

Die Logik ist bewusst transparent und leicht anpassbar gehalten. Später können
hier Branchen-spezifische Gewichtungen oder KI-gestützte Bewertungen ergänzt
werden, ohne die Weboberfläche umbauen zu müssen.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

RELEVANCE_TERMS = {
    "graffiti", "wandgestaltung", "fassade", "fassadengestaltung",
    "fassadenkunst", "street art", "mural", "wandmalerei", "workshop",
    "schulhof", "kita", "schule", "trafostation", "trafohaus",
    "energiehaus", "stadtwerke", "kunst am bau", "jugendprojekt",
}
PRESTIGE_TERMS = {"kommune", "stadt", "stadtwerke", "schule", "kita", "öffentlich", "kunst am bau", "wohnungsbau"}
BUDGET_TERMS = {"fassade", "fassadengestaltung", "kunst am bau", "stadtwerke", "wohnungsbau", "innenraumgestaltung"}

CATEGORY_WEIGHTS = {
    "Trafostation / Energiehaus": 18,
    "Schul- und Kita-Projekt": 16,
    "Fassadengestaltung": 17,
    "Graffiti-Workshop": 13,
    "Kommunales Kunstprojekt": 18,
    "Wohnungsbaugesellschaft": 15,
    "Firmen-Innenraumgestaltung": 14,
    "Kunst am Bau": 18,
}


def _normalize(text: Optional[str]) -> str:
    return (text or "").lower()


def deadline_urgency(deadline: Optional[str]) -> int:
    """Bewertet Fristen: baldige, aber noch machbare Deadlines sind wertvoll."""
    if not deadline:
        return 6
    try:
        due = datetime.strptime(deadline, "%Y-%m-%d").date()
    except ValueError:
        return 5
    days_left = (due - date.today()).days
    if days_left < 0:
        return 1
    if days_left <= 7:
        return 10
    if days_left <= 30:
        return 13
    if days_left <= 90:
        return 9
    return 6


def distance_points(distance_km: Optional[float]) -> int:
    if distance_km is None:
        return 7
    if distance_km <= 30:
        return 20
    if distance_km <= 75:
        return 17
    if distance_km <= 150:
        return 13
    if distance_km <= 250:
        return 8
    return 4


def term_score(text: str, terms: set[str], max_points: int) -> int:
    hits = sum(1 for term in terms if term in text)
    if hits == 0:
        return 3
    return min(max_points, 4 + hits * 4)


def calculate_score(opportunity: dict) -> int:
    """Berechnet einen Score von 1 bis 100 anhand nachvollziehbarer Faktoren."""
    combined = " ".join([
        _normalize(opportunity.get("title")),
        _normalize(opportunity.get("description")),
        _normalize(opportunity.get("category")),
        _normalize(opportunity.get("client")),
    ])
    category = opportunity.get("category") or ""

    score = 0
    score += distance_points(opportunity.get("distance_km"))                 # max 20
    score += min(20, CATEGORY_WEIGHTS.get(category, 8) + term_score(combined, RELEVANCE_TERMS, 10) // 3)
    score += term_score(combined, BUDGET_TERMS, 15)                           # max 15
    score += 10 if any(x in combined for x in ["sucht", "plant", "ausschreibung", "angebot"]) else 6
    score += term_score(combined, PRESTIGE_TERMS, 13)                         # max 13
    score += 12 if any(x in combined for x in ["stark", "mural", "graffiti", "fassade", "workshop"]) else 7
    score += deadline_urgency(opportunity.get("deadline"))                    # max 13

    return max(1, min(100, int(score)))


def traffic_light(score: int) -> str:
    if score >= 75:
        return "Grün"
    if score >= 45:
        return "Gelb"
    return "Rot"


def recommended_action(score: int, deadline: Optional[str] = None) -> str:
    if score >= 75:
        return "Sofort prüfen und Erstkontakt vorbereiten"
    if score >= 45:
        return "Beobachten, Details recherchieren und bei Gelegenheit nachfassen"
    if deadline:
        return "Nur prüfen, wenn freie Kapazität vorhanden ist"
    return "Niedrige Priorität, archivieren oder später neu bewerten"
