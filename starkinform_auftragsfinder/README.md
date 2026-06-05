# Starkinform Auftragsfinder

Lokale Web-App für Starkinform aus Greiz, Thüringen. Die Anwendung hilft dabei, potenzielle Aufträge für Graffiti-Auftragsarbeiten, Fassadengestaltung, Wandgestaltung, Trafostationen, Schul- und Kita-Projekte, Workshops, kommunale Kunstprojekte, Stadtwerke, Wohnungsbaugesellschaften und Firmen-Innenraumgestaltung zu sammeln, zu bewerten und nachzuverfolgen.

## Warum dieses MVP rechtssicher startet

Der Auftragsfinder enthält bewusst **keine aggressiven Scraper** und keine Umgehung technischer Sperren. Quellen wie Kleinanzeigen, MyHammer oder Ausschreibungsportale werden zunächst als gespeicherte Suchlinks und manuelle Prüfpunkte verwaltet. Unterstützt werden im MVP:

- manuell eingetragene Treffer
- gespeicherte Such-URLs
- vorbereitete Google-Suchlinks
- CSV-Import aus eigener Recherche
- eine Adapter-Struktur für spätere erlaubte RSS-Feeds, offizielle APIs oder freigegebene Quellen

## Funktionen

- Dashboard mit Kennzahlen, Top-Chancen, Ampelstatus und filterbarer Tabelle
- Trefferverwaltung mit Detailseite, Notizen, Statusänderung und Quellenlink
- automatische Bewertung von 1 bis 100
- Ampellogik: Grün ab 75, Gelb ab 45, Rot bis 44
- professionelle Kontakttext-Vorbereitung für Starkinform
- Keyword-Verwaltung mit aktivierbaren/deaktivierbaren Startbegriffen
- Quellenverwaltung für Suchlinks, RSS-Hinweise und manuell zu prüfende Plattformen
- CSV-Import mit den Spalten `Titel, Quelle, Link, Auftraggeber, Ort, Beschreibung, Kategorie, Deadline`
- Demo-Daten für realistische Beispielaufträge
- vorbereitete, aber deaktivierte E-Mail-Benachrichtigung für grüne Treffer

## Projektstruktur

```text
starkinform_auftragsfinder/
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── database/
├── services/
│   ├── contact.py
│   ├── db.py
│   ├── emailer.py
│   ├── scoring.py
│   └── sources.py
├── templates/
├── static/
├── imports/
└── demo_data/
```

## Python installieren

### Windows

1. Öffne <https://www.python.org/downloads/>.
2. Lade Python 3.11 oder neuer herunter.
3. Beim Installer unbedingt **Add python.exe to PATH** aktivieren.
4. Installation abschließen.
5. In PowerShell prüfen:

```powershell
python --version
```

### macOS

Mit Homebrew:

```bash
brew install python
python3 --version
```

### Linux

Debian/Ubuntu:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
python3 --version
```

## Installation

Im Projektordner ausführen:

```bash
cd starkinform_auftragsfinder
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Unter Windows PowerShell:

```powershell
cd starkinform_auftragsfinder
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## App starten

```bash
python app.py
```

Danach im Browser öffnen:

```text
http://127.0.0.1:5000
```

Beim ersten Start legt die App automatisch die SQLite-Datenbank unter `database/auftragsfinder.sqlite3` an und befüllt Keywords sowie vorbereitete Quellen.

## Demo-Daten laden

In der Web-App oben rechts auf **Demo-Daten laden** klicken. Alternativ kann die Datei `demo_data/demo_opportunities.csv` über die CSV-Importseite hochgeladen werden.

Die Demo-Daten enthalten unter anderem:

- Stadtwerke suchen Gestaltung für Trafostation
- Schule plant Schulhofgestaltung
- Kommune sucht Künstler für Jugendprojekt
- Wohnungsbaugesellschaft möchte Fassade aufwerten
- Firma sucht Innenraumgestaltung

## CSV-Import

Die Importdatei muss UTF-8-codiert sein und diese Kopfzeile verwenden:

```csv
Titel,Quelle,Link,Auftraggeber,Ort,Beschreibung,Kategorie,Deadline
```

`Deadline` wird als Datum im Format `YYYY-MM-DD` erwartet, z. B. `2026-07-15`.

## Bewertungslogik

Die Scoring-Logik liegt in `services/scoring.py` und bewertet transparent:

1. Entfernung zu Greiz
2. Relevanz für Starkinform
3. geschätztes Budgetpotenzial
4. Wahrscheinlichkeit eines Auftrags
5. Prestige- oder Referenzwert
6. Passung zu bisherigen Starkinform-Projekten
7. Dringlichkeit / Deadline

Ampelstatus:

- **Grün:** Score 75–100, sofort prüfen oder kontaktieren
- **Gelb:** Score 45–74, beobachten oder später prüfen
- **Rot:** Score 1–44, geringe Priorität

## E-Mail-Benachrichtigung

Unter **Benachrichtigung** können SMTP-Felder vorbereitet werden. Im MVP wird nichts automatisch versendet. Die Demo-Vorschau zeigt nur, welche grünen Treffer später in eine automatische E-Mail aufgenommen würden.

## Später echte Quellen ergänzen

Für neue Quellen sollte ein eigener Adapter in `services/` ergänzt werden, z. B. `rss_adapter.py` oder `official_api_adapter.py`. Wichtig:

1. Nutzungsbedingungen der Quelle prüfen.
2. Nur öffentliche RSS-Feeds, offizielle APIs oder ausdrücklich erlaubte Abrufe verwenden.
3. Keine Captcha-Umgehung, Login-Umgehung oder technische Blockade umgehen.
4. Treffer über `create_opportunity()` speichern, damit Bewertung und Ampel automatisch berechnet werden.
5. Quellen, deren Scraping verboten ist, weiterhin als Suchlink unter **Quellen** pflegen und manuell prüfen.

## Startbefehl kurz

```bash
cd starkinform_auftragsfinder
source .venv/bin/activate
python app.py
```
