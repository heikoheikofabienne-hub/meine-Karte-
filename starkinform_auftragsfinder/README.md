# Starkinform Akquise- und Marktbeobachtungs-App

Professionelle lokale MVP-Web-App für **Starkinform** aus Greiz, Thüringen. Die App arbeitet als digitaler Akquise-Agent für Graffiti-Kunst, Fassadengestaltung, Wandgestaltung, Trafostationen, Energiehäuser, Schul-/Kita-Projekte, kommunale Verschönerung, Firmenflächen und Innenräume.

## MVP-Funktionen

- modernes Dashboard mit neuen Chancen, heißen Leads, Sofort-Kontakt-Hinweisen und Top-5-Liste
- manuelle Live-Suche über öffentliche Google-News-RSS-Feeds und optionale Bing-Web-Search-API
- täglicher Suchlauf per Cron/Task Scheduler über `python app.py run-search`
- umfangreiche Suchcluster für direkte Aufträge, Frühwarnsignale, Stadtwerke/Energie, kommunale Bauprojekte und Firmeninnenräume
- SQLite-Datenmodell mit den Tabellen `leads`, `sources`, `search_terms`, `search_runs`, `contacts`, `notes`, `notifications`, `settings` und `outreach_templates`
- Lead-Detailseite mit KI-ähnlicher regelbasierter Zusammenfassung, Akquise-Empfehlung, Score-Aufschlüsselung und Erstmail-Vorschlag
- Score von 0 bis 100 nach Relevanz, Nähe zu Greiz, Abschlusswahrscheinlichkeit, Budget, Dringlichkeit, Prestige und Kontaktierbarkeit
- Duplikaterkennung per Hash aus Titel, Quelle und Link
- Statusverwaltung: `neu`, `geprüft`, `kontaktiert`, `Angebot gesendet`, `gewonnen`, `verloren`, `archiviert`
- Beobachtungsliste über Statusfilter
- Karten-MVP mit farbiger Prioritätsdarstellung; spätere Leaflet/OpenStreetMap-Anbindung vorbereitet
- CSV-Import und CSV-Export der wichtigsten Lead-Felder
- Benachrichtigungsbereich mit Tageszusammenfassung und vorbereiteten Kanälen für App/SMTP/WhatsApp/Telegram

## Rechtssichere Quellenstrategie

Die App verwendet im MVP nur öffentlich zugängliche Suchlinks/RSS-Feeds und optionale offizielle APIs. Sie enthält keine aggressiven Scraper, keine Login-Umgehung, keine Captcha-Umgehung und keine Umgehung technischer Sperren. Plattformen wie Kleinanzeigen, MyHammer oder Social Media werden als manuelle Quellen oder spätere legale Schnittstellen geführt.

## Installation

```bash
cd starkinform_auftragsfinder
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Danach öffnen:

```text
http://127.0.0.1:5000
```

## Live-Suche starten

In der App auf **Live-Suche starten** klicken oder im Terminal:

```bash
cd starkinform_auftragsfinder
python app.py run-search
```

Für eine tägliche Suche kann dieser Befehl per Cron ausgeführt werden, z. B. täglich um 07:30 Uhr:

```cron
30 7 * * * cd /pfad/zum/projekt/starkinform_auftragsfinder && /pfad/zur/.venv/bin/python app.py run-search
```

## Optionale Bing-API

Ohne API-Key nutzt die App Google-News-RSS. Für zusätzliche Web-Suchergebnisse kann in **Benachrichtigung & tägliche Suche** ein Bing-Search-API-Key hinterlegt oder `BING_API_KEY` als Umgebungsvariable gesetzt werden.

## CSV-Import

Unterstützt werden unter anderem diese Spalten:

```csv
Titel,Quelle,Link,Auftraggeber,Ort,Beschreibung,Kategorie,Datum
```

## Weiterer Ausbau nach dem MVP

- echte Leaflet/OpenStreetMap-Karte mit Marker-Clustering
- zusätzliche offizielle RSS-/API-Adapter für Städte, Stadtwerke, Vergabeportale und Amtsblätter
- echte SMTP-/Telegram-/WhatsApp-Benachrichtigung nach hinterlegter Konfiguration
- PDF-/Excel-Export und Wochenbericht
- optionale LLM-Auswertung über eine serverseitig hinterlegte API
