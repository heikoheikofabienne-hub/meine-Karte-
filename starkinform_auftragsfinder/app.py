"""Starkinform Akquise- und Marktbeobachtungs-App."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

from flask import Flask, Response, flash, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename

from config import DEMO_DATA_PATH, IMPORT_DIR, SECRET_KEY
from services.contact import build_contact_text, build_recommendation
from services.db import (
    CATEGORIES, STATUSES, TRAFFIC_LIGHTS, active_sources, create_lead, dashboard_stats, delete_lead,
    distinct_values, get_lead, get_settings, import_csv, init_db, latest_search_runs, list_keywords,
    list_leads, list_sources, load_demo_data, save_keyword, save_source, update_keyword, update_lead,
    update_settings,
)
from services.emailer import green_opportunities_digest
from services.live_search import run_live_search


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    init_db()

    @app.context_processor
    def inject_options():
        return {"categories": CATEGORIES, "statuses": STATUSES, "traffic_lights": TRAFFIC_LIGHTS}

    @app.route("/")
    def dashboard():
        filters = {
            "source_name": request.args.get("source_name", ""),
            "status": request.args.get("status", ""),
            "category": request.args.get("category", ""),
            "traffic_light": request.args.get("traffic_light", ""),
            "max_distance": request.args.get("max_distance", ""),
            "q": request.args.get("q", ""),
            "section": request.args.get("section", ""),
        }
        sort = request.args.get("sort", "score")
        return render_template(
            "dashboard.html",
            leads=list_leads(filters, sort),
            stats=dashboard_stats(),
            runs=latest_search_runs(5),
            filters=filters,
            sort=sort,
            filter_options={
                "sources": distinct_values("source_name"),
                "statuses": distinct_values("status") or STATUSES,
                "categories": distinct_values("category") or CATEGORIES,
                "traffic_lights": distinct_values("traffic_light") or TRAFFIC_LIGHTS,
            },
        )

    @app.post("/search/run")
    def search_run():
        summary = run_live_search("manual")
        if summary["errors"]:
            flash(f"Live-Suche abgeschlossen: {summary['new_leads']} neu, {summary['updated_leads']} aktualisiert. Fehler siehe Protokoll.", "warning")
        else:
            flash(f"Live-Suche abgeschlossen: {summary['new_leads']} neue Leads, {summary['updated_leads']} aktualisiert.", "success")
        return redirect(url_for("dashboard"))

    @app.route("/leads/new", methods=["GET", "POST"])
    @app.route("/opportunities/new", methods=["GET", "POST"])
    def lead_new():
        if request.method == "POST":
            lead_id = create_lead(request.form.to_dict())
            flash("Lead wurde gespeichert, bewertet und mit E-Mail-Vorschlag vorbereitet.", "success")
            return redirect(url_for("lead_detail", lead_id=lead_id))
        return render_template("opportunity_form.html", opportunity=None)

    @app.route("/leads/<int:lead_id>", methods=["GET", "POST"])
    @app.route("/opportunities/<int:lead_id>", methods=["GET", "POST"])
    def lead_detail(lead_id: int):
        lead = get_lead(lead_id)
        if not lead:
            flash("Lead nicht gefunden.", "warning")
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            update_lead(lead_id, request.form.to_dict())
            flash("Lead wurde aktualisiert, neu bewertet und der Mailvorschlag wurde angepasst.", "success")
            return redirect(url_for("lead_detail", lead_id=lead_id))
        return render_template("opportunity_detail.html", opportunity=lead, contact_text=build_contact_text(lead), recommendation=build_recommendation(lead))

    @app.post("/leads/<int:lead_id>/delete")
    @app.post("/opportunities/<int:lead_id>/delete")
    def lead_delete(lead_id: int):
        delete_lead(lead_id)
        flash("Lead wurde archiviert.", "info")
        return redirect(url_for("dashboard"))

    @app.route("/keywords", methods=["GET", "POST"])
    def keywords():
        if request.method == "POST":
            save_keyword(request.form.get("term", ""), request.form.get("cluster_name", "Eigene Begriffe"))
            flash("Suchbegriff wurde gespeichert.", "success")
            return redirect(url_for("keywords"))
        return render_template("keywords.html", keywords=list_keywords())

    @app.post("/keywords/<int:keyword_id>")
    def keyword_update(keyword_id: int):
        update_keyword(keyword_id, request.form.get("term", ""), request.form.get("active") == "on", request.form.get("cluster_name", "Eigene Begriffe"))
        flash("Suchbegriff wurde aktualisiert.", "success")
        return redirect(url_for("keywords"))

    @app.route("/sources", methods=["GET", "POST"])
    def sources():
        if request.method == "POST":
            save_source(request.form.get("name", ""), request.form.get("source_type", "Suchlink"), request.form.get("url", ""), request.form.get("notes", ""))
            flash("Quelle wurde gespeichert.", "success")
            return redirect(url_for("sources"))
        return render_template("sources.html", sources=list_sources())

    @app.route("/import", methods=["GET", "POST"])
    def import_view():
        if request.method == "POST":
            file = request.files.get("csv_file")
            if not file or not file.filename:
                flash("Bitte eine CSV-Datei auswählen.", "warning")
                return redirect(url_for("import_view"))
            IMPORT_DIR.mkdir(parents=True, exist_ok=True)
            target = IMPORT_DIR / secure_filename(file.filename)
            file.save(target)
            count = import_csv(target)
            flash(f"{count} Leads wurden importiert.", "success")
            return redirect(url_for("dashboard"))
        return render_template("import.html")

    @app.get("/export/leads.csv")
    def export_csv():
        leads = list_leads({}, "score")
        fieldnames = ["id", "title", "source_name", "result_url", "published_at", "location_name", "state", "distance_from_greiz_km", "category", "total_score", "status", "next_action", "suggested_subject", "contact_email", "organization_name"]
        def generate():
            from io import StringIO
            buffer = StringIO()
            writer = csv.DictWriter(buffer, fieldnames=fieldnames)
            writer.writeheader(); yield buffer.getvalue(); buffer.seek(0); buffer.truncate(0)
            for lead in leads:
                writer.writerow({key: lead.get(key, "") for key in fieldnames})
                yield buffer.getvalue(); buffer.seek(0); buffer.truncate(0)
        return Response(generate(), mimetype="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=starkinform-leads.csv"})

    @app.post("/demo/load")
    def demo_load():
        count = load_demo_data(DEMO_DATA_PATH)
        flash(f"{count} Demo-Leads wurden geladen.", "success")
        return redirect(url_for("dashboard"))

    @app.route("/notifications", methods=["GET", "POST"])
    def notifications():
        if request.method == "POST":
            update_settings(request.form.to_dict())
            flash("Benachrichtigungseinstellungen gespeichert. SMTP/WhatsApp/Telegram bleiben im MVP vorbereitete Kanäle.", "success")
            return redirect(url_for("notifications"))
        leads = list_leads({}, "score")
        return render_template("notifications.html", settings=get_settings(), demo_digest=green_opportunities_digest(leads), sources=active_sources(), runs=latest_search_runs(10))

    @app.get("/demo/sample-csv")
    def sample_csv():
        return send_from_directory(Path(DEMO_DATA_PATH).parent, Path(DEMO_DATA_PATH).name, as_attachment=True)

    return app


app = create_app()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run-search":
        init_db()
        print(run_live_search("cron"))
    else:
        app.run(debug=True)
