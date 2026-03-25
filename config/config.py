from pathlib import Path

DIR = Path(__file__).resolve().parent.parent
JSON_PATH = Path.joinpath(DIR, "json")
XLSX_PATH = Path.joinpath(DIR, "xlsx")

IDX_JSON = Path.joinpath(JSON_PATH, "idx.json")
HOSTS_JSON = Path.joinpath(JSON_PATH, "hosts.json")
XLSX_FILE = Path.joinpath(XLSX_PATH, "result.xlsx")

DB_NAME = "wb.db"
