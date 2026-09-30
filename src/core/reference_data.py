import json
from pathlib import Path

_OBJECT_LOOKUP_CACHE = None

def _get_object_lookup():
    """Builds an in-memory index mapping string IDs, (O)IDs, and string names to object metadata."""
    global _OBJECT_LOOKUP_CACHE
    if _OBJECT_LOOKUP_CACHE is not None:
        return _OBJECT_LOOKUP_CACHE

    from data.data_loader import OBJECTS_CATALOG

    lookup = {}
    catalog = OBJECTS_CATALOG if isinstance(OBJECTS_CATALOG, list) else []

    for item in catalog:
        if not isinstance(item, dict):
            continue

        item_id = str(item.get("id", ""))
        names = item.get("names", {})
        name = names.get("data-en-US") or names.get("en-US") or item.get("name") or "Unknown"
        price = item.get("price", 0)

        clean_name = name.replace(" ", "_").replace("'", "")
        wiki_filename = name.replace(" ", "_")

        # Set primary local icon using ID convention (O_{id}.png) if ID exists, otherwise O_{Name}.png
        if item_id:
            primary_icon = f"/static/img/items/O_{item_id}.png"
        else:
            primary_icon = f"/static/img/items/O_{clean_name}.png"

        info = {
            "id": item_id,
            "name": name,
            "price": price,
            "icon": primary_icon,
            "wiki_icon": f"https://stardewvalleywiki.com/Special:Redirect/file/{wiki_filename}.png"
        }

        if item_id:
            lookup[item_id] = info
            lookup[f"(O){item_id}"] = info

        if name:
            lookup[name] = info
            lookup[name.lower()] = info

    _OBJECT_LOOKUP_CACHE = lookup
    return lookup


def get_object_info(harvest_id: str) -> dict:
    """
    Look up item metadata (display name, sprite icon, base price)
    by numeric ID ("412"), qualified ID ("(O)412"), or 1.6 string key ("Powdermelon").
    """
    if not harvest_id or str(harvest_id).strip() in ("None", "-1", ""):
        return {
            "name": "Wild / Unknown",
            "icon": "/static/img/items/placeholder.png",
            "wiki_icon": "https://stardewvalleywiki.com/Special:Redirect/file/Tile.png",
            "price": 0
        }

    raw_key = str(harvest_id).replace("(O)", "").strip()
    lookup = _get_object_lookup()

    if raw_key in lookup:
        return dict(lookup[raw_key])

    if raw_key.lower() in lookup:
        return dict(lookup[raw_key.lower()])

    formatted_name = raw_key.replace("_", " ")
    return {
        "id": raw_key,
        "name": formatted_name,
        "price": 0,
        "icon": f"/static/img/items/O_{raw_key}.png",
        "wiki_icon": f"https://stardewvalleywiki.com/Special:Redirect/file/{raw_key}.png"
    }


def load_object_map(json_path="data/objects.json"):
    """Load object names mapping ID -> Display Name."""
    path = Path(json_path)
    object_map = {}
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "id" in item:
                        item_id = str(item["id"])
                        names = item.get("names", {})
                        name = names.get("data-en-US") or names.get("en-US") or "Unknown"
                        object_map[item_id] = name
                        object_map[f"(O){item_id}"] = name
    return object_map
    