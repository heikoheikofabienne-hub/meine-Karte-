"""SQLite-Datenbank, Migrationen und Repository-Funktionen für Starkinform."""
from __future__ import annotations

import csv
import hashlib
import math
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from config import DATABASE_PATH, DEFAULT_STATE, GREIZ_LAT, GREIZ_LON
from services.contact import build_ai_summary, build_contact_text, build_recommendation, suggested_subject
from services.scoring import calculate_total_score, categorize, recommended_action, score_breakdown, traffic_light
from services.sources import PREPARED_SOURCES, SEARCH_CLUSTERS, google_search_url

CATEGORIES = [
    "Direkte Aufträge", "Frühe Bedarfssignale", "Stadtwerke / Energieversorger",
    "Kommunen / Städte / Gemeinden", "Schulen / Kitas / Jugendclubs", "Firmen / Gewerbe",
    "Ausschreibungen", "Fassadengestaltung", "Graffiti-Prävention", "Sonstiges",
]
STATUSES = ["neu", "geprüft", "kontaktiert", "Angebot gesendet", "gewonnen", "verloren", "archiviert"]
TRAFFIC_LIGHTS = ["Rot", "Orange", "Gelb", "Grau"]
REGION_TERMS = ["Greiz", "Thüringen", "Sachsen", "Sachsen-Anhalt", "Bayern", "Hessen", "Gera", "Zwickau", "Plauen", "Jena", "Erfurt", "Chemnitz", "Leipzig", "Hof"]

START_KEYWORDS = [term for terms in SEARCH_CLUSTERS.values() for term in terms]

LOCATION_COORDS = {
    "greiz": (50.6578, 12.1997, "Thüringen"), "gera": (50.8772, 12.0790, "Thüringen"),
    "jena": (50.9271, 11.5892, "Thüringen"), "erfurt": (50.9848, 11.0299, "Thüringen"),
    "zwickau": (50.7189, 12.4930, "Sachsen"), "plauen": (50.4973, 12.1378, "Sachsen"),
    "chemnitz": (50.8278, 12.9214, "Sachsen"), "leipzig": (51.3397, 12.3731, "Sachsen"),
    "dresden": (51.0504, 13.7373, "Sachsen"), "hof": (50.3135, 11.9128, "Bayern"),
    "bayreuth": (49.9456, 11.5713, "Bayern"), "bamberg": (49.8988, 10.9028, "Bayern"),
    "halle": (51.4969, 11.9688, "Sachsen-Anhalt"), "weimar": (50.9795, 11.3235, "Thüringen"),
    "suhl": (50.6091, 10.6940, "Thüringen"), "fulda": (50.5558, 9.6808, "Hessen"),
}


def get_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    return round(radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 1)


def infer_location(text: str) -> tuple[str, Optional[float], Optional[float], Optional[float], str]:
    lowered = (text or "").lower()
    for name, (lat, lon, state) in LOCATION_COORDS.items():
        if name in lowered:
            return name.title(), lat, lon, haversine_km(GREIZ_LAT, GREIZ_LON, lat, lon), state
    for region in ["thüringen", "sachsen-anhalt", "sachsen", "bayern", "hessen"]:
        if region in lowered:
            return region.title(), None, None, None, region.title()
    return "", None, None, None, DEFAULT_STATE


def duplicate_hash(title: str, result_url: str, source_name: str) -> str:
    raw = "|".join([(result_url or "").strip().lower(), (title or "").strip().lower(), (source_name or "").strip().lower()])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                source_name TEXT NOT NULL,
                source_url TEXT,
                result_url TEXT,
                published_at TEXT,
                discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                location_name TEXT,
                latitude REAL,
                longitude REAL,
                distance_from_greiz_km REAL,
                state TEXT,
                category TEXT,
                description TEXT,
                ai_summary TEXT,
                opportunity_reason TEXT,
                recommended_service TEXT,
                estimated_budget TEXT,
                urgency TEXT,
                relevance_score INTEGER DEFAULT 0,
                distance_score INTEGER DEFAULT 0,
                probability_score INTEGER DEFAULT 0,
                budget_score INTEGER DEFAULT 0,
                prestige_score INTEGER DEFAULT 0,
                contactability_score INTEGER DEFAULT 0,
                urgency_score INTEGER DEFAULT 0,
                total_score INTEGER NOT NULL DEFAULT 0,
                traffic_light TEXT NOT NULL DEFAULT 'Grau',
                contact_name TEXT,
                contact_role TEXT,
                contact_email TEXT,
                contact_phone TEXT,
                organization_name TEXT,
                organization_website TEXT,
                next_action TEXT,
                suggested_subject TEXT,
                suggested_email TEXT,
                status TEXT NOT NULL DEFAULT 'neu',
                notes TEXT,
                follow_up_date TEXT,
                duplicate_hash TEXT UNIQUE
            );

            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                source_type TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                notes TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS search_terms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term TEXT NOT NULL UNIQUE,
                cluster_name TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS search_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                finished_at TEXT,
                trigger_type TEXT,
                sources_checked INTEGER DEFAULT 0,
                results_found INTEGER DEFAULT 0,
                new_leads INTEGER DEFAULT 0,
                updated_leads INTEGER DEFAULT 0,
                errors TEXT
            );

            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                name TEXT,
                role TEXT,
                email TEXT,
                phone TEXT,
                website TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                body TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                channel TEXT,
                subject TEXT,
                body TEXT,
                status TEXT DEFAULT 'geplant',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                sent_at TEXT
            );

            CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);

            CREATE TABLE IF NOT EXISTS outreach_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                subject TEXT,
                body TEXT,
                active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        seed_defaults(conn)


def seed_defaults(conn: sqlite3.Connection) -> None:
    for cluster, terms in SEARCH_CLUSTERS.items():
        for term in terms:
            conn.execute("INSERT OR IGNORE INTO search_terms(term, cluster_name, active) VALUES (?, ?, 1)", (term, cluster))
    for name, source_type, url, notes in PREPARED_SOURCES:
        conn.execute("INSERT OR IGNORE INTO sources(name, source_type, url, notes) VALUES (?, ?, ?, ?)", (name, source_type, url, notes))
    for term in START_KEYWORDS[:20]:
        conn.execute(
            "INSERT OR IGNORE INTO sources(name, source_type, url, notes) VALUES (?, ?, ?, ?)",
            (f"Google News: {term}", "RSS/Suchlink", google_search_url(term), "Öffentlicher Such-/News-Link; keine Login- oder Scraping-Umgehung."),
        )
    defaults = {
        "smtp_enabled": "false", "smtp_host": "", "smtp_port": "587", "smtp_user": "", "smtp_password": "",
        "notification_recipient": "", "daily_search_enabled": "true", "daily_search_time": "07:30",
        "search_provider": "google_news_rss", "bing_api_key": "", "openai_api_key": "",
        "region_terms": ", ".join(REGION_TERMS),
    }
    for key, value in defaults.items():
        conn.execute("INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)", (key, value))
    conn.execute(
        "INSERT OR IGNORE INTO outreach_templates(id, name, subject, body, active) VALUES (1, ?, ?, ?, 1)",
        ("Starkinform Kurz-Erstmail", "Gestaltung statt Schmiererei – Idee für [Ort/Objekt]", "Kurze regionale Erstmail mit Referenzangebot."),
    )


def normalize_lead(data: dict) -> dict:
    text = " ".join(str(data.get(k) or "") for k in ["title", "description", "location_name", "state"])
    loc, lat, lon, dist, state = infer_location(text)
    lead = {
        "title": data.get("title") or "Ohne Titel",
        "source_name": data.get("source_name") or data.get("source") or "Manuell",
        "source_url": data.get("source_url") or data.get("link") or data.get("result_url") or "",
        "result_url": data.get("result_url") or data.get("link") or "",
        "published_at": data.get("published_at") or data.get("found_date") or date.today().isoformat(),
        "location_name": data.get("location_name") or data.get("location") or loc,
        "latitude": _float_or_none(data.get("latitude")) if data.get("latitude") not in (None, "") else lat,
        "longitude": _float_or_none(data.get("longitude")) if data.get("longitude") not in (None, "") else lon,
        "distance_from_greiz_km": _float_or_none(data.get("distance_from_greiz_km") or data.get("distance_km")) if (data.get("distance_from_greiz_km") or data.get("distance_km")) not in (None, "") else dist,
        "state": data.get("state") or state,
        "category": data.get("category") or "Sonstiges",
        "description": data.get("description") or "",
        "opportunity_reason": data.get("opportunity_reason") or infer_opportunity_reason(data),
        "recommended_service": data.get("recommended_service") or infer_service(data),
        "estimated_budget": data.get("estimated_budget") or data.get("potential") or infer_budget(data),
        "urgency": data.get("urgency") or "normal",
        "contact_name": data.get("contact_name") or "",
        "contact_role": data.get("contact_role") or "",
        "contact_email": data.get("contact_email") or "",
        "contact_phone": data.get("contact_phone") or "",
        "organization_name": data.get("organization_name") or data.get("client") or "",
        "organization_website": data.get("organization_website") or "",
        "status": data.get("status") or "neu",
        "notes": data.get("notes") or "",
        "follow_up_date": data.get("follow_up_date") or None,
    }
    lead["category"] = categorize(lead)
    parts = score_breakdown(lead)
    lead.update(parts)
    lead["total_score"] = int(data.get("total_score") or data.get("score") or calculate_total_score(lead))
    lead["traffic_light"] = traffic_light(lead["total_score"])
    lead["next_action"] = data.get("next_action") or recommended_action(lead["total_score"])
    lead["suggested_subject"] = data.get("suggested_subject") or suggested_subject(lead)
    lead["ai_summary"] = data.get("ai_summary") or build_ai_summary(lead)
    lead["suggested_email"] = data.get("suggested_email") or build_contact_text(lead)
    lead["duplicate_hash"] = data.get("duplicate_hash") or duplicate_hash(lead["title"], lead["result_url"], lead["source_name"])
    return lead


def _float_or_none(value) -> Optional[float]:
    if value in (None, ""):
        return None
    return float(str(value).replace(",", "."))


def infer_opportunity_reason(data: dict) -> str:
    text = " ".join(str(data.get(k) or "").lower() for k in ["title", "description"])
    if any(word in text for word in ["schmiererei", "vandalismus", "graffiti entfernen"]):
        return "wiederholte Schmierereien oder Vandalismus ein präventives Gestaltungskonzept nahelegen"
    if any(word in text for word in ["trafostation", "trafo", "stadtwerke", "netzstation"]):
        return "technische Infrastruktur sichtbar im Stadtbild steht und gestalterisch aufgewertet werden kann"
    if any(word in text for word in ["sanierung", "neubau", "quartier", "stadtumbau"]):
        return "ein Bau- oder Sanierungsprojekt frühzeitig Gestaltungsbedarf auslösen kann"
    return "das Thema zu Starkinform-Leistungen wie Graffiti, Wandgestaltung, Fassadenkunst oder Workshops passt"


def infer_service(data: dict) -> str:
    text = " ".join(str(data.get(k) or "").lower() for k in ["title", "description", "category"])
    if any(word in text for word in ["trafostation", "trafo", "stadtwerke", "netzstation"]):
        return "Gestaltung von Trafostationen, Energiehäusern und Verteilerkästen"
    if any(word in text for word in ["schule", "kita", "schulhof", "jugend"]):
        return "Schulhof-, Kita- oder Workshop-Gestaltung mit pädagogischem Bezug"
    if any(word in text for word in ["innenraum", "büro", "showroom", "hotel", "gastronomie"]):
        return "hochwertige Innenraum- und Firmenflächengestaltung"
    if "fassade" in text:
        return "Fassadengestaltung und großformatige Murals"
    return "professionelle Graffiti-, Wand- und Fassadengestaltung"


def infer_budget(data: dict) -> str:
    text = " ".join(str(data.get(k) or "").lower() for k in ["title", "description", "category"])
    if any(word in text for word in ["fassade", "stadtwerke", "kunst am bau", "quartier", "neubau"]):
        return "hoch"
    if any(word in text for word in ["schule", "kita", "workshop", "trafostation"]):
        return "mittel"
    return "niedrig bis mittel"


def create_lead(data: dict) -> int:
    lead = normalize_lead(data)
    columns = ", ".join(lead.keys())
    placeholders = ", ".join(f":{key}" for key in lead.keys())
    with get_connection() as conn:
        cursor = conn.execute(f"INSERT INTO leads({columns}) VALUES ({placeholders})", lead)
        create_notification_if_hot(conn, cursor.lastrowid, lead)
        return int(cursor.lastrowid)


def upsert_lead(data: dict) -> tuple[int, bool]:
    lead = normalize_lead(data)
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM leads WHERE duplicate_hash = ?", (lead["duplicate_hash"],)).fetchone()
        if existing:
            lead["id"] = existing["id"]
            assignments = ", ".join(f"{key}=:{key}" for key in lead.keys() if key != "duplicate_hash")
            conn.execute(f"UPDATE leads SET {assignments}, updated_at=CURRENT_TIMESTAMP WHERE duplicate_hash=:duplicate_hash", lead)
            return int(existing["id"]), False
        columns = ", ".join(lead.keys())
        placeholders = ", ".join(f":{key}" for key in lead.keys())
        cursor = conn.execute(f"INSERT INTO leads({columns}) VALUES ({placeholders})", lead)
        create_notification_if_hot(conn, cursor.lastrowid, lead)
        return int(cursor.lastrowid), True


def create_notification_if_hot(conn: sqlite3.Connection, lead_id: int, lead: dict) -> None:
    if lead.get("total_score", 0) >= 85:
        conn.execute(
            "INSERT INTO notifications(lead_id, channel, subject, body, status) VALUES (?, 'app', ?, ?, 'neu')",
            (lead_id, f"Heißer Starkinform-Lead: {lead['title']}", lead.get("ai_summary") or ""),
        )


def update_lead(lead_id: int, data: dict) -> None:
    current = get_lead(lead_id) or {}
    lead = normalize_lead({**current, **data})
    lead["id"] = lead_id
    assignments = ", ".join(f"{key}=:{key}" for key in lead.keys() if key != "duplicate_hash")
    with get_connection() as conn:
        conn.execute(f"UPDATE leads SET {assignments}, updated_at=CURRENT_TIMESTAMP WHERE id=:id", lead)


def get_lead(lead_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        return row_to_dict(row) if row else None


def delete_lead(lead_id: int) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE leads SET status='archiviert', updated_at=CURRENT_TIMESTAMP WHERE id = ?", (lead_id,))


def list_leads(filters: dict | None = None, sort: str = "score") -> list[dict]:
    filters = filters or {}
    clauses, params = [], []
    for field in ["source_name", "status", "category", "traffic_light"]:
        if filters.get(field):
            clauses.append(f"{field} = ?")
            params.append(filters[field])
    if filters.get("max_distance"):
        clauses.append("distance_from_greiz_km <= ?")
        params.append(float(filters["max_distance"]))
    if filters.get("q"):
        clauses.append("(title LIKE ? OR description LIKE ? OR organization_name LIKE ? OR location_name LIKE ?)")
        q = f"%{filters['q']}%"
        params.extend([q, q, q, q])
    if filters.get("section"):
        section = filters["section"]
        if section == "today":
            clauses.append("datetime(discovered_at) >= datetime('now', '-1 day')")
        elif section == "hot":
            clauses.append("total_score >= 70")
        elif section == "watchlist":
            clauses.append("status IN ('geprüft', 'kontaktiert', 'Angebot gesendet')")
        else:
            clauses.append("category = ?")
            params.append(section)
    query = "SELECT * FROM leads"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    sort_map = {"score": "total_score DESC, published_at DESC", "date": "published_at DESC, discovered_at DESC", "distance": "distance_from_greiz_km IS NULL, distance_from_greiz_km ASC"}
    query += " ORDER BY " + sort_map.get(sort, sort_map["score"])
    with get_connection() as conn:
        return [row_to_dict(row) for row in conn.execute(query, params).fetchall()]


def dashboard_stats() -> dict:
    all_items = list_leads({}, "score")
    return {
        "total": len(all_items),
        "new_today": sum(1 for item in all_items if (item.get("discovered_at") or "")[:10] == date.today().isoformat()),
        "hot": sum(1 for item in all_items if item.get("total_score", 0) >= 70),
        "instant": sum(1 for item in all_items if item.get("total_score", 0) >= 85),
        "top": all_items[:5],
        "energy": [item for item in all_items if item.get("category") == "Stadtwerke / Energieversorger"][:5],
        "municipal": [item for item in all_items if item.get("category") == "Kommunen / Städte / Gemeinden"][:5],
    }


def create_search_run(trigger_type: str = "manual") -> int:
    with get_connection() as conn:
        cur = conn.execute("INSERT INTO search_runs(trigger_type) VALUES (?)", (trigger_type,))
        return int(cur.lastrowid)


def finish_search_run(run_id: int, sources_checked: int, results_found: int, new_leads: int, updated_leads: int, errors: list[str]) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE search_runs SET finished_at=CURRENT_TIMESTAMP, sources_checked=?, results_found=?, new_leads=?, updated_leads=?, errors=? WHERE id=?",
            (sources_checked, results_found, new_leads, updated_leads, "\n".join(errors), run_id),
        )


def latest_search_runs(limit: int = 10) -> list[dict]:
    with get_connection() as conn:
        return [row_to_dict(row) for row in conn.execute("SELECT * FROM search_runs ORDER BY started_at DESC LIMIT ?", (limit,)).fetchall()]


def import_csv(path: Path) -> int:
    count = 0
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            create_lead({
                "title": row.get("Titel") or row.get("title"), "source_name": row.get("Quelle") or row.get("source_name"),
                "result_url": row.get("Link") or row.get("result_url"), "organization_name": row.get("Auftraggeber"),
                "location_name": row.get("Ort"), "description": row.get("Beschreibung"), "category": row.get("Kategorie"),
                "published_at": row.get("Datum") or row.get("Deadline"),
            })
            count += 1
    return count


def load_demo_data(path: Path) -> int:
    return import_csv(path)


def list_keywords() -> list[dict]:
    with get_connection() as conn:
        return [row_to_dict(row) for row in conn.execute("SELECT * FROM search_terms ORDER BY active DESC, cluster_name, term").fetchall()]


def active_keywords(limit: int = 40) -> list[dict]:
    with get_connection() as conn:
        return [row_to_dict(row) for row in conn.execute("SELECT * FROM search_terms WHERE active=1 ORDER BY cluster_name, term LIMIT ?", (limit,)).fetchall()]


def save_keyword(term: str, cluster_name: str = "Eigene Begriffe") -> None:
    term = term.strip()
    if not term:
        return
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO search_terms(term, cluster_name, active) VALUES (?, ?, 1)", (term, cluster_name))


def update_keyword(keyword_id: int, term: str, active: bool, cluster_name: str = "Eigene Begriffe") -> None:
    with get_connection() as conn:
        conn.execute("UPDATE search_terms SET term=?, cluster_name=?, active=? WHERE id=?", (term.strip(), cluster_name, 1 if active else 0, keyword_id))


def list_sources() -> list[dict]:
    with get_connection() as conn:
        return [row_to_dict(row) for row in conn.execute("SELECT * FROM sources ORDER BY active DESC, name").fetchall()]


def active_sources() -> list[dict]:
    with get_connection() as conn:
        return [row_to_dict(row) for row in conn.execute("SELECT * FROM sources WHERE active=1 ORDER BY name").fetchall()]


def save_source(name: str, source_type: str, url: str, notes: str = "") -> None:
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO sources(name, source_type, url, notes) VALUES (?, ?, ?, ?)", (name, source_type, url, notes))


def get_settings() -> dict:
    with get_connection() as conn:
        return {row["key"]: row["value"] for row in conn.execute("SELECT key, value FROM settings").fetchall()}


def update_settings(settings: dict) -> None:
    with get_connection() as conn:
        for key, value in settings.items():
            conn.execute("INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))


def distinct_values(column: str) -> list[str]:
    allowed = {"source_name", "status", "category", "traffic_light"}
    if column not in allowed:
        return []
    with get_connection() as conn:
        return [row[0] for row in conn.execute(f"SELECT DISTINCT {column} FROM leads WHERE {column} IS NOT NULL AND {column} != '' ORDER BY {column}").fetchall()]

# Rückwärtskompatible Namen für bestehende Templates/Routen.
create_opportunity = create_lead
update_opportunity = update_lead
get_opportunity = get_lead
delete_opportunity = delete_lead
list_opportunities = list_leads
