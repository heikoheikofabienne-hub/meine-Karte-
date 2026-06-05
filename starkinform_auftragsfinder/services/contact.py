"""Erstellt professionelle Erstkontakt-Texte für Starkinform."""
from __future__ import annotations


def build_contact_text(opportunity: dict) -> str:
    category = opportunity.get("category") or "Wandgestaltung"
    client = opportunity.get("client") or "Ihr Team"
    title = opportunity.get("title") or "Ihr Projekt"
    location = opportunity.get("location") or "Ihrer Region"

    return f"""Guten Tag {client},

wir sind Starkinform aus Greiz in Thüringen und auf professionelle Graffiti-, Fassaden- und Wandgestaltung spezialisiert. Ihr Projekt „{title}“ in {location} klingt sehr passend zu unseren bisherigen Arbeiten im Bereich {category}.

Gern würden wir kurz prüfen, wie wir Ihr Vorhaben gestalterisch, organisatorisch und budgetgerecht unterstützen können. Starkinform entwickelt individuelle Entwürfe, begleitet die Abstimmung mit Auftraggebern und setzt Projekte sauber, termintreu und mit Blick auf langlebige Wirkung um.

Wenn das Projekt noch offen ist, freuen wir uns über weitere Informationen zu Fläche, Zeitplan, Budgetrahmen und gewünschten Motiven. Auf Wunsch senden wir Ihnen gern Referenzen und erste Ideen zu.

Mit freundlichen Grüßen
Starkinform
Greiz, Thüringen"""
