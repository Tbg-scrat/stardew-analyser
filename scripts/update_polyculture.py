import json
from pathlib import Path

# Path to shipping catalog relative to repo root
catalog_path = Path("data/shipping.json")

# The exact 28 core crops required for the Polyculture achievement
POLYCULTURE_CROPS = {
    "Parsnip", "Green Bean", "Cauliflower", "Potato", "Tomato", 
    "Kale", "Rhubarb", "Garlic", "Strawberry", "Blueberry", 
    "Hot Pepper", "Melon", "Radish", "Red Cabbage", "Starfruit", 
    "Corn", "Eggplant", "Wheat", "Hops", "Pumpkin", 
    "Yam", "Cranberries", "Beet", "Amaranth", "Artichoke", "Bok Choy"
}

if not catalog_path.exists():
    print(f"Error: Could not find {catalog_path}")
    exit(1)

with open(catalog_path, "r", encoding="utf-8") as f:
    data = json.load(f)

updated_count = 0

# Case 1: Catalog is a list of objects
if isinstance(data, list):
    for item in data:
        if isinstance(item, dict):
            name = item.get("name")
            is_poly = name in POLYCULTURE_CROPS
            item["is_polyculture"] = is_poly
            if is_poly:
                updated_count += 1

# Case 2: Catalog is a dict (e.g. {"16": {"name": "Wild Horseradish", ...}} or {"Parsnip": {...}})
elif isinstance(data, dict):
    for key, val in data.items():
        if isinstance(val, dict):
            name = val.get("name", key)
            is_poly = name in POLYCULTURE_CROPS or key in POLYCULTURE_CROPS
            val["is_polyculture"] = is_poly
            if is_poly:
                updated_count += 1

with open(catalog_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Successfully updated {catalog_path}! Marked {updated_count} polyculture crops.")
