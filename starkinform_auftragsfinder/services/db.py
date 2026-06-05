"""SQLite-Zugriff und Initialisierung für den lokalen Auftragsfinder."""
from __future__ import annotations

import csv
import math
import sqlite3
from datetime import date
from pathlib import Path
from typing import Iterable, Optional

from config import DATABASE_PATH, DEFAULT_STATE, GREIZ_LAT, GREIZ_LON
from services.scoring import calculate_score, recommended_action, traffic_light
from services.sources import PREPARED_SOURCES, google_search_url

START_KEYWORDS = [
    "Graffiti", "Wandgestaltung", "Fassadengestaltung", "Fassadenkunst", "Street Art", "Mural",
    "Wandmalerei", "Künstler gesucht", "Graffiti-Künstler", "Graffiti Workshop", "Schulhof gestalten",
    "Kita Wandgestaltung", "Schule Wandgestaltung", "Innenraumgestaltung", "Trafostation gestalten",
    "Trafohaus gestalten", "Energiehaus Gestaltung", "Stadtwerke Gestaltung", "Kunst am Bau",
    "Fassadenkünstler", "öffentliche Ausschreibung Kunst", "Jugendprojekt Graffiti",
]

CATEGORIES = [
    "Graffiti-Auftragsarbeit", "Fassadengestaltung", "Wandgestaltung innen/außen",
    "Trafostation / Energiehaus", "Schul- und Kita-Projekt", "Graffiti-Workshop",
    "Kommunales Kunstprojekt", "Stadtwerke / Energieversorger", "Wohnungsbaugesellschaft",
    "Firmen-Innenraumgestaltung", "Kunst am Bau", "Sonstiges",
]
STATUSES = ["Neu", "Prüfen", "Interessant", "Kontaktiert", "Abgelehnt", "Gewonnen"]
TRAFFIC_LIGHTS = ["Grün", "Gelb", "Rot"]


def get_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    return round(radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 1)


LOCATION_COORDS = {
    "greiz": (50.6578, 12.1997), "gera": (50.8772, 12.0790), "jena": (50.9271, 11.5892),
    "erfurt": (50.9848, 11.0299), "zwickau": (50.7189, 12.4930), "plauen": (50.4973, 12.1378),
    "chemnitz": (50.8278, 12.9214), "hof": (50.3135, 11.9128), "leipzig": (51.3397, 12.3731),
}


def estimate_distance(location: Optional[str]) -> Optional[float]:
    if not location:
        return None
    lowered = location.lower()
    for name, coords in LOCATION_COORDS.items():
        if name in lowered:
            return haversine_km(GREIZ_LAT, GREIZ_LON, coords[0], coords[1])
    return None


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                link TEXT,
                client TEXT,
                location TEXT,
                state TEXT,
                distance_km REAL,
                found_date TEXT NOT NULL,
                deadline TEXT,
                description TEXT,
                category TEXT,
                potential TEXT,
                score INTEGER NOT NULL,
                traffic_light TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Neu',
                notes TEXT,
                next_action TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term TEXT NOT NULL UNIQUE,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS source_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                source_type TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                notes TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            """
        )
        seed_defaults(conn)


def seed_defaults(conn: sqlite3.Connection) -> None:
    for keyword in START_KEYWORDS:
        conn.execute("INSERT OR IGNORE INTO keywords(term, active) VALUES (?, 1)", (keyword,))
    for name, source_type, url, notes in PREPARED_SOURCES:
        conn.execute(
            "INSERT OR IGNORE INTO source_links(name, source_type, url, notes) VALUES (?, ?, ?, ?)",
            (name, source_type, url, notes),
        )
    for keyword in START_KEYWORDS[:8]:
        conn.execute(
            "INSERT OR IGNORE INTO source_links(name, source_type, url, notes) VALUES (?, ?, ?, ?)",
            (f"Google: {keyword}", "Suchlink", google_search_url(keyword), "Vorbereitete Google-Suche, manuell prüfen."),
        )
    defaults = {
        "smtp_enabled": "false", "smtp_host": "", "smtp_port": "587", "smtp_user": "",
        "smtp_password": "", "notification_recipient": "",
    }
    for key, value in defaults.items():
        conn.execute("INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)", (key, value))


def row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


def list_opportunities(filters: dict | None = None, sort: str = "score") -> list[dict]:
    filters = filters or {}
    clauses = []
    params = []
    for field, column in [("source", "source"), ("status", "status"), ("category", "category"), ("traffic_light", "traffic_light")]:
        if filters.get(field):
            clauses.append(f"{column} = ?")
            params.append(filters[field])
    if filters.get("max_distance"):
        clauses.append("distance_km <= ?")
        params.append(float(filters["max_distance"]))
    query = "SELECT * FROM opportunities"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    sort_map = {
        "score": "score DESC, found_date DESC",
        "date": "found_date DESC, score DESC",
        "deadline": "deadline IS NULL, deadline ASC, score DESC",
    }
    query += " ORDER BY " + sort_map.get(sort, sort_map["score"])
    with get_connection() as conn:
        return [row_to_dict(row) for row in conn.execute(query, params).fetchall()]


def get_opportunity(opportunity_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM opportunities WHERE id = ?", (opportunity_id,)).fetchone()
        return row_to_dict(row) if row else None


def normalize_opportunity(data: dict) -> dict:
    distance = data.get("distance_km")
    if distance in (None, ""):
        distance = estimate_distance(data.get("location"))
    elif isinstance(distance, str):
        distance = float(distance.replace(",", "."))
    normalized = {
        "title": data.get("title") or "Ohne Titel",
        "source": data.get("source") or "Manuell",
        "link": data.get("link") or "",
        "client": data.get("client") or data.get("auftraggeber") or "",
        "location": data.get("location") or data.get("ort") or "",
        "state": data.get("state") or data.get("bundesland") or DEFAULT_STATE,
        "distance_km": distance,
        "found_date": data.get("found_date") or date.today().isoformat(),
        "deadline": data.get("deadline") or None,
        "description": data.get("description") or "",
        "category": data.get("category") or "Sonstiges",
        "potential": data.get("potential") or "Mittel",
        "status": data.get("status") or "Neu",
        "notes": data.get("notes") or "",
    }
    score = int(data.get("score") or calculate_score(normalized))
    normalized["score"] = score
    normalized["traffic_light"] = data.get("traffic_light") or traffic_light(score)
    normalized["next_action"] = data.get("next_action") or recommended_action(score, normalized.get("deadline"))
    return normalized


def create_opportunity(data: dict) -> int:
    item = normalize_opportunity(data)
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO opportunities(title, source, link, client, location, state, distance_km, found_date,
            deadline, description, category, potential, score, traffic_light, status, notes, next_action)
            VALUES (:title, :source, :link, :client, :location, :state, :distance_km, :found_date,
            :deadline, :description, :category, :potential, :score, :traffic_light, :status, :notes, :next_action)
            """,
            item,
        )
        return int(cursor.lastrowid)


def update_opportunity(opportunity_id: int, data: dict) -> None:
    current = get_opportunity(opportunity_id) or {}
    merged = {**current, **data}
    item = normalize_opportunity(merged)
    item["id"] = opportunity_id
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE opportunities SET title=:title, source=:source, link=:link, client=:client, location=:location,
            state=:state, distance_km=:distance_km, found_date=:found_date, deadline=:deadline,
            description=:description, category=:category, potential=:potential, score=:score,
            traffic_light=:traffic_light, status=:status, notes=:notes, next_action=:next_action,
            updated_at=CURRENT_TIMESTAMP WHERE id=:id
            """,
            item,
        )


def delete_opportunity(opportunity_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM opportunities WHERE id = ?", (opportunity_id,))


def import_csv(path: Path) -> int:
    count = 0
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            create_opportunity({
                "title": row.get("Titel"), "source": row.get("Quelle"), "link": row.get("Link"),
                "client": row.get("Auftraggeber"), "location": row.get("Ort"),
                "description": row.get("Beschreibung"), "category": row.get("Kategorie"),
                "deadline": row.get("Deadline"),
            })
            count += 1
    return count


def load_demo_data(path: Path) -> int:
    return import_csv(path)


def list_keywords() -> list[dict]:
    with get_connection() as conn:
        return [row_to_dict(row) for row in conn.execute("SELECT * FROM keywords ORDER BY active DESC, term").fetchall()]


def save_keyword(term: str) -> None:
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO keywords(term, active) VALUES (?, 1)", (term.strip(),))


def update_keyword(keyword_id: int, term: str, active: bool) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE keywords SET term = ?, active = ? WHERE id = ?", (term.strip(), 1 if active else 0, keyword_id))


def list_sources() -> list[dict]:
    with get_connection() as conn:
        return [row_to_dict(row) for row in conn.execute("SELECT * FROM source_links ORDER BY active DESC, name").fetchall()]


def save_source(name: str, source_type: str, url: str, notes: str = "") -> None:
    with get_connection() as conn:
        conn.execute("INSERT INTO source_links(name, source_type, url, notes) VALUES (?, ?, ?, ?)", (name, source_type, url, notes))


def get_settings() -> dict:
    with get_connection() as conn:
        return {row["key"]: row["value"] for row in conn.execute("SELECT key, value FROM settings").fetchall()}


def update_settings(settings: dict) -> None:
    with get_connection() as conn:
        for key, value in settings.items():
            conn.execute("INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))


def distinct_values(column: str) -> list[str]:
    if column not in {"source", "status", "category", "traffic_light"}:
        return []
    with get_connection() as conn:
        return [row[0] for row in conn.execute(f"SELECT DISTINCT {column} FROM opportunities WHERE {column} IS NOT NULL AND {column} != '' ORDER BY {column}").fetchall()]
