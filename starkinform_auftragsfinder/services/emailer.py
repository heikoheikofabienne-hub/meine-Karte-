"""Benachrichtigungsvorschau für Starkinform-Leads."""
from __future__ import annotations


def green_opportunities_digest(opportunities: list[dict]) -> str:
    hot = [item for item in opportunities if int(item.get("total_score") or item.get("score") or 0) >= 70]
    if not hot:
        return "Keine heißen Treffer für eine Benachrichtigung vorhanden."
    lines = ["Starkinform Tageszusammenfassung", "", f"Neue/heiße Treffer: {len(hot)}", "Top 5 Chancen:"]
    for item in hot[:5]:
        score = item.get("total_score") or item.get("score")
        lines.append(f"- {item['title']} ({item.get('source_name') or item.get('source')}, Score {score})")
        lines.append(f"  Ort: {item.get('location_name') or 'unbekannt'} | Aktion: {item.get('next_action') or '-'}")
        lines.append(f"  Link: {item.get('result_url') or '-'}")
    lines.extend(["", "Empfohlene Aktion: Score ≥85 sofort anrufen oder kurze Erstmail senden."])
    return "\n".join(lines)
