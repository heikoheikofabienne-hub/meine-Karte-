"""Live-Suche über öffentliche RSS-Feeds und optionale Such-APIs."""
from __future__ import annotations

import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

from services.db import active_keywords, create_search_run, finish_search_run, get_settings, upsert_lead
from services.sources import google_news_rss_url

REGION_BATCHES = [
    "Greiz Thüringen", "Gera Zwickau Plauen", "Thüringen", "Sachsen", "Sachsen-Anhalt", "Bayern", "Hessen",
    "Stadtwerke Thüringen Sachsen", "Kommune Schule Kita Greiz",
]


def run_live_search(trigger_type: str = "manual", max_queries: int = 16) -> dict:
    """Führt einen rechtssicheren Suchlauf aus und speichert neue/aktualisierte Leads."""
    run_id = create_search_run(trigger_type)
    errors: list[str] = []
    results_found = new_leads = updated_leads = sources_checked = 0
    settings = get_settings()
    keywords = active_keywords(max_queries)
    for index, keyword in enumerate(keywords):
        region = REGION_BATCHES[index % len(REGION_BATCHES)]
        query = f"{keyword['term']} {region}"
        try:
            items = fetch_google_news_rss(query)
            sources_checked += 1
            for item in items:
                results_found += 1
                _, is_new = upsert_lead({
                    "title": item["title"],
                    "source_name": "Google News RSS",
                    "source_url": google_news_rss_url(keyword["term"], region),
                    "result_url": item["link"],
                    "published_at": item.get("published_at"),
                    "description": item.get("description") or f"Gefunden über Suchcluster {keyword.get('cluster_name')}: {query}",
                    "category": keyword.get("cluster_name") or "Frühe Bedarfssignale",
                    "organization_name": item.get("publisher") or "",
                })
                if is_new:
                    new_leads += 1
                else:
                    updated_leads += 1
        except Exception as exc:  # noqa: BLE001 - Fehler werden im Suchlauf-Protokoll gespeichert.
            errors.append(f"{query}: {exc}")
    bing_key = settings.get("bing_api_key") or os.environ.get("BING_API_KEY")
    if bing_key and keywords:
        try:
            query = f"{keywords[0]['term']} Greiz Thüringen Starkinform"
            for item in fetch_bing(query, bing_key):
                results_found += 1
                _, is_new = upsert_lead({
                    "title": item["title"], "source_name": "Bing Web Search API", "source_url": "https://api.bing.microsoft.com/v7.0/search",
                    "result_url": item["link"], "description": item.get("description"), "category": "Direkte Aufträge",
                })
                new_leads += 1 if is_new else 0
                updated_leads += 0 if is_new else 1
            sources_checked += 1
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Bing API: {exc}")
    finish_search_run(run_id, sources_checked, results_found, new_leads, updated_leads, errors)
    return {"run_id": run_id, "sources_checked": sources_checked, "results_found": results_found, "new_leads": new_leads, "updated_leads": updated_leads, "errors": errors}


def fetch_google_news_rss(query: str, limit: int = 5) -> list[dict]:
    url = google_news_rss_url(query, "")
    request = urllib.request.Request(url, headers={"User-Agent": "Starkinform-Auftragsfinder/1.0 (+https://starkinform.de)"})
    with urllib.request.urlopen(request, timeout=12) as response:  # noqa: S310 - öffentliche RSS-URL aus eigener Konfiguration.
        xml_data = response.read()
    root = ET.fromstring(xml_data)
    items = []
    for item in root.findall("./channel/item")[:limit]:
        title = item.findtext("title") or "Ohne Titel"
        link = item.findtext("link") or ""
        description = strip_html(item.findtext("description") or "")
        published = item.findtext("pubDate")
        publisher = item.findtext("source") or ""
        items.append({"title": title, "link": link, "description": description, "published_at": parse_rss_date(published), "publisher": publisher})
    return items


def fetch_bing(query: str, api_key: str, limit: int = 5) -> list[dict]:
    url = "https://api.bing.microsoft.com/v7.0/search?" + urllib.parse.urlencode({"q": query, "mkt": "de-DE", "count": limit})
    request = urllib.request.Request(url, headers={"Ocp-Apim-Subscription-Key": api_key, "User-Agent": "Starkinform-Auftragsfinder/1.0"})
    import json
    with urllib.request.urlopen(request, timeout=12) as response:  # noqa: S310 - offizielle API mit Schlüssel.
        payload = json.loads(response.read().decode("utf-8"))
    return [{"title": row.get("name"), "link": row.get("url"), "description": row.get("snippet")} for row in payload.get("webPages", {}).get("value", [])]


def parse_rss_date(value: str | None) -> str:
    if not value:
        return datetime.utcnow().date().isoformat()
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(value).date().isoformat()
    except Exception:  # noqa: BLE001
        return datetime.utcnow().date().isoformat()


def strip_html(value: str) -> str:
    import re
    return re.sub(r"<[^>]+>", " ", value).replace("&nbsp;", " ").strip()
