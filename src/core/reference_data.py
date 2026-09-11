import json
from pathlib import Path

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
