"""Starkinform Auftragsfinder - lokale Flask-Web-App."""
from __future__ import annotations

from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename

from config import DEMO_DATA_PATH, IMPORT_DIR, SECRET_KEY
from services.contact import build_contact_text
from services.db import (
    CATEGORIES, STATUSES, TRAFFIC_LIGHTS, create_opportunity, delete_opportunity, distinct_values,
    get_opportunity, get_settings, import_csv, init_db, list_keywords, list_opportunities, list_sources,
    load_demo_data, save_keyword, save_source, update_keyword, update_opportunity, update_settings,
)
from services.emailer import green_opportunities_digest


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
            "source": request.args.get("source", ""),
            "status": request.args.get("status", ""),
            "category": request.args.get("category", ""),
            "traffic_light": request.args.get("traffic_light", ""),
            "max_distance": request.args.get("max_distance", ""),
        }
        sort = request.args.get("sort", "score")
        opportunities = list_opportunities(filters, sort)
        all_items = list_opportunities({}, "score")
        stats = {
            "new": sum(1 for item in all_items if item["status"] == "Neu"),
            "green": sum(1 for item in all_items if item["traffic_light"] == "Grün"),
            "total": len(all_items),
            "top": all_items[:5],
        }
        return render_template(
            "dashboard.html",
            opportunities=opportunities,
            stats=stats,
            filters=filters,
            sort=sort,
            filter_options={
                "sources": distinct_values("source"),
                "statuses": distinct_values("status") or STATUSES,
                "categories": distinct_values("category") or CATEGORIES,
                "traffic_lights": distinct_values("traffic_light") or TRAFFIC_LIGHTS,
            },
        )

    @app.route("/opportunities/new", methods=["GET", "POST"])
    def opportunity_new():
        if request.method == "POST":
            opportunity_id = create_opportunity(request.form.to_dict())
            flash("Treffer wurde gespeichert und automatisch bewertet.", "success")
            return redirect(url_for("opportunity_detail", opportunity_id=opportunity_id))
        return render_template("opportunity_form.html", opportunity=None)

    @app.route("/opportunities/<int:opportunity_id>", methods=["GET", "POST"])
    def opportunity_detail(opportunity_id: int):
        opportunity = get_opportunity(opportunity_id)
        if not opportunity:
            flash("Treffer nicht gefunden.", "warning")
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            update_opportunity(opportunity_id, request.form.to_dict())
            flash("Treffer wurde aktualisiert und neu bewertet.", "success")
            return redirect(url_for("opportunity_detail", opportunity_id=opportunity_id))
        return render_template("opportunity_detail.html", opportunity=opportunity, contact_text=build_contact_text(opportunity))

    @app.post("/opportunities/<int:opportunity_id>/delete")
    def opportunity_delete(opportunity_id: int):
        delete_opportunity(opportunity_id)
        flash("Treffer wurde gelöscht.", "info")
        return redirect(url_for("dashboard"))

    @app.route("/keywords", methods=["GET", "POST"])
    def keywords():
        if request.method == "POST":
            save_keyword(request.form.get("term", ""))
            flash("Keyword wurde gespeichert.", "success")
            return redirect(url_for("keywords"))
        return render_template("keywords.html", keywords=list_keywords())

    @app.post("/keywords/<int:keyword_id>")
    def keyword_update(keyword_id: int):
        update_keyword(keyword_id, request.form.get("term", ""), request.form.get("active") == "on")
        flash("Keyword wurde aktualisiert.", "success")
        return redirect(url_for("keywords"))

    @app.route("/sources", methods=["GET", "POST"])
    def sources():
        if request.method == "POST":
            save_source(
                request.form.get("name", ""),
                request.form.get("source_type", "Manuell zu prüfen"),
                request.form.get("url", ""),
                request.form.get("notes", ""),
            )
            flash("Quelle/Suchlink wurde gespeichert.", "success")
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
            flash(f"{count} Treffer wurden importiert.", "success")
            return redirect(url_for("dashboard"))
        return render_template("import.html")

    @app.post("/demo/load")
    def demo_load():
        count = load_demo_data(DEMO_DATA_PATH)
        flash(f"{count} Demo-Treffer wurden geladen.", "success")
        return redirect(url_for("dashboard"))

    @app.route("/notifications", methods=["GET", "POST"])
    def notifications():
        if request.method == "POST":
            update_settings(request.form.to_dict())
            flash("SMTP-Konfiguration gespeichert. Versand bleibt im MVP deaktiviert.", "success")
            return redirect(url_for("notifications"))
        opportunities = list_opportunities({}, "score")
        return render_template(
            "notifications.html",
            settings=get_settings(),
            demo_digest=green_opportunities_digest(opportunities),
        )

    @app.get("/demo/sample-csv")
    def sample_csv():
        return send_from_directory(Path(DEMO_DATA_PATH).parent, Path(DEMO_DATA_PATH).name, as_attachment=True)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
