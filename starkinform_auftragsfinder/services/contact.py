"""Erstellt Akquise-Empfehlungen und Erstmail-Texte für Starkinform."""
from __future__ import annotations


def suggested_subject(lead: dict) -> str:
    location = lead.get("location_name") or lead.get("location") or "Ihr Projekt"
    category = lead.get("category") or "Gestaltung"
    if "Graffiti" in category or "Schmier" in (lead.get("description") or ""):
        return f"Gestaltung statt Schmiererei – Idee für {location}"
    if "Stadtwerke" in category or "Trafo" in category:
        return f"Gestaltung für Trafostation/Energiefläche in {location}"
    return f"Gestaltungsidee für {location}"


def build_ai_summary(lead: dict) -> str:
    title = lead.get("title") or "Der Treffer"
    location = lead.get("location_name") or "der Region"
    service = lead.get("recommended_service") or "Wand- und Fassadengestaltung"
    reason = lead.get("opportunity_reason") or "passt zu öffentlichen und gewerblichen Gestaltungsprojekten"
    return f"{title} in {location} ist ein Akquise-Hinweis, weil {reason}. Starkinform könnte hier {service} anbieten und die Fläche hochwertig, regional passend und präventiv aufwerten."


def build_recommendation(lead: dict) -> str:
    org = lead.get("organization_name") or lead.get("client") or "den verantwortlichen Träger"
    service = lead.get("recommended_service") or "professionelle Graffiti-, Wand- oder Fassadengestaltung"
    score = lead.get("total_score") or lead.get("score") or 0
    urgency = "sehr dringend" if score >= 85 else "kurzfristig" if score >= 70 else "beobachtend"
    return (
        f"Kontakt lohnt sich, weil der Treffer ein konkretes Bedarfssignal enthält. "
        f"Ansprechen: {org}, idealerweise Bauamt, Stadtmarketing, Pressestelle, Facility Management oder Stadtwerke-Projektleitung. "
        f"Angebot: {service}. Vorgehen: {urgency} per kurzer E-Mail mit 2–3 Referenzbeispielen, bei Score über 85 zusätzlich telefonisch nachfassen."
    )


def build_contact_text(lead: dict) -> str:
    name = lead.get("contact_name") or "Damen und Herren"
    title = lead.get("title") or "Ihre Meldung / Ihr Projekt"
    location = lead.get("location_name") or lead.get("location") or "Ihrer Region"
    problem = lead.get("opportunity_reason") or lead.get("description") or "die Gestaltung oder Aufwertung der Fläche"
    service = lead.get("recommended_service") or "Trafostationen, Fassaden und öffentliche Flächen"
    subject = lead.get("suggested_subject") or suggested_subject(lead)
    return f"""Betreff: {subject}

Guten Tag {name},

ich bin auf „{title}“ in {location} aufmerksam geworden. Wir gestalten mit Starkinform aus Greiz seit vielen Jahren {service} für Stadtwerke, Kommunen, Schulen und Unternehmen.

Gerade bei {problem} kann eine hochwertige, ortsbezogene Gestaltung helfen, die Fläche sichtbar aufzuwerten und ungewollte Schmierereien zu reduzieren.

Wenn es für Sie interessant ist, sende ich Ihnen gern 2–3 passende Referenzbeispiele und eine kurze Einschätzung, wie sich das Projekt pragmatisch umsetzen ließe.

Viele Grüße
Heiko Rank
Starkinform
https://starkinform.de"""
