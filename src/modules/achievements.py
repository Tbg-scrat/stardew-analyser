import json
from pathlib import Path

# Load catalog metadata relative to project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CATALOG_PATH = BASE_DIR / "data" / "achievements.json"


def load_achievements_catalog():
    if not CATALOG_PATH.exists():
        return []
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_achievements(player_node, *args, **kwargs):
    achievements_catalog = load_achievements_catalog()
    
    # Parse unlocked achievement IDs from player XML
    unlocked_ids = set()
    achievements_node = player_node.find("achievements")
    if achievements_node is not None:
        for node in achievements_node.findall("int"):
            if node.text and node.text.isdigit():
                unlocked_ids.add(int(node.text))

    processed_achievements = []
    
    for catalog_item in achievements_catalog:
        item_id = catalog_item.get("id")
        is_unlocked = item_id in unlocked_ids

        processed_achievements.append({
            "id": item_id,
            "name": catalog_item.get("name"),
            "description": catalog_item.get("description"),
            "category": catalog_item.get("category"),
            "icon": catalog_item.get("icon"),
            "target": catalog_item.get("target"),
            "tip": catalog_item.get("tip"),
            "unlocked": is_unlocked,
            "link_module": catalog_item.get("link_module"),
            "link_filter": catalog_item.get("link_filter")
        })

    # Summary statistics
    total_count = len(processed_achievements)
    unlocked_count = sum(1 for a in processed_achievements if a["unlocked"])

    return {
        "list": processed_achievements,
        "total": total_count,
        "unlocked_count": unlocked_count,
        "percent": round((unlocked_count / total_count * 100), 1) if total_count > 0 else 0
    }
    