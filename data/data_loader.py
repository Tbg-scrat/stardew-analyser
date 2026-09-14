# -*- coding: utf-8 -*-
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent

def load_json_catalog(filename):
    file_path = DATA_DIR / filename
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

FISH_CATALOG = load_json_catalog("fish.json")
MUSEUM_CATALOG = load_json_catalog("museum.json")
SHIPPING_CATALOG = load_json_catalog("shipping.json")
COOKING_CATALOG = load_json_catalog("cooking.json")
