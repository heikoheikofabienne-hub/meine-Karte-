"""Vorbereitete E-Mail-Benachrichtigungen.

Im MVP werden keine E-Mails verschickt. Die Funktionen zeigen nur an, welche
Treffer später versendet würden. SMTP-Daten werden lokal in SQLite gespeichert.
"""
from __future__ import annotations


def green_opportunities_digest(opportunities: list[dict]) -> str:
    lines = ["Starkinform Auftragsfinder - Demo-Benachrichtigung", ""]
    green = [item for item in opportunities if item.get("traffic_light") == "Grün"]
    if not green:
        return "Keine grünen Treffer für eine Benachrichtigung vorhanden."
    for item in green:
        lines.append(f"- {item['title']} ({item['source']}, Score {item['score']})")
        lines.append(f"  Ort: {item.get('location') or 'unbekannt'} | Aktion: {item.get('next_action') or '-'}")
        lines.append(f"  Link: {item.get('link') or '-'}")
    return "\n".join(lines)
