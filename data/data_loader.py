import json
from pathlib import Path

DATA_DIR = Path(__file__).parent

def load_catalog(filename: str) -> dict:
    file_path = DATA_DIR / filename
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

FISH_CATALOG = load_catalog("fish.json")
MUSEUM_CATALOG = load_catalog("museum.json")
SHIPPING_CATALOG = load_catalog("shipping.json")
