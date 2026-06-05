"""Konfiguration für den Starkinform Auftragsfinder."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database" / "auftragsfinder.sqlite3"
IMPORT_DIR = BASE_DIR / "imports"
DEMO_DATA_PATH = BASE_DIR / "demo_data" / "demo_opportunities.csv"
SECRET_KEY = "dev-local-change-me"
GREIZ_LAT = 50.6578
GREIZ_LON = 12.1997
DEFAULT_STATE = "Thüringen"
