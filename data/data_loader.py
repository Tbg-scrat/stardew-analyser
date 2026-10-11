# data/data_loader.py
# -*- coding: utf-8 -*-
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent

def load_json_catalog(filename, default_factory=dict):
    file_path = DATA_DIR / filename
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default_factory()

FISH_CATALOG = load_json_catalog("fish.json")
MUSEUM_CATALOG = load_json_catalog("museum.json")
SHIPPING_CATALOG = load_json_catalog("shipping.json")
COOKING_CATALOG = load_json_catalog("cooking.json")
ACHIEVEMENTS_CATALOG = load_json_catalog("achievements.json", default_factory=list)
OBJECTS_CATALOG = load_json_catalog("objects.json", default_factory=list)
VILLAGERS_CATALOG = load_json_catalog("villagers.json")
GRANDPA_CATALOG = load_json_catalog("grandpa_eval.json")
FESTIVALS_CATALOG = load_json_catalog("festivals.json")
TOOLS_CATALOG = load_json_catalog("tools.json")


def get_combined_objects_catalog() -> list:
    """
    Aggregates domain-specific JSON catalogs (keyed by ID) and legacy 
    OBJECTS_CATALOG (list of items) into a unified list of item dicts.
    """
    combined = []
    seen_ids = set()

    # 1. Process dict-based domain catalogs (newer modular structure)
    domain_catalogs = [
        FISH_CATALOG,
        SHIPPING_CATALOG,
        COOKING_CATALOG,
        MUSEUM_CATALOG,
    ]

    for catalog in domain_catalogs:
        if not isinstance(catalog, dict):
            continue
        for item_id, item_data in catalog.items():
            if not isinstance(item_data, dict):
                continue

            entry = {"id": str(item_id)}
            entry.update(item_data)
            combined.append(entry)
            seen_ids.add(str(item_id))

    # 2. Process legacy list catalog (objects.json) for items not yet extracted
    if isinstance(OBJECTS_CATALOG, list):
        for item in OBJECTS_CATALOG:
            if not isinstance(item, dict):
                continue
            item_id = str(item.get("id", ""))
            if item_id and item_id in seen_ids:
                continue  # Skip if domain catalog takes precedence
            combined.append(item)

    return combined
    