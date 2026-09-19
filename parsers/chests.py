# parsers/chests.py
from src.core.reference_data import load_object_map

def parse_chests(root):
    """
    Extracts raw chest objects and items using core reference data for item names/qualities.
    """
    object_map = load_object_map()
    locations_node = root.find("locations")
    
    if locations_node is None:
        return {"total_chests": 0, "total_items": 0, "chests": []}

    chests_data = []
    total_items_found = 0

    for loc in locations_node.findall("GameLocation"):
        loc_name = loc.findtext("name") or "Unknown Location"
        objects = loc.find("objects")
        if objects is None:
            continue

        for item in objects.findall("item"):
            obj = item.find("value/Object")
            if obj is None:
                continue

            obj_type = obj.findtext("type")
            name = obj.findtext("name")
            qualified_id = obj.findtext("QualifiedItemId")

            is_chest = (
                obj_type == "Chest"
                or name in ["Chest", "Stone Chest", "Big Chest", "Big Stone Chest"]
                or (qualified_id and qualified_id.startswith("(BC)130"))
                or (qualified_id and qualified_id.startswith("(BC)232"))
            )

            if not is_chest:
                continue

            items_node = obj.find("items")
            chest_items = []

            if items_node is not None:
                for chest_item in items_node.findall("Item"):
                    item_id = chest_item.findtext("itemId") or chest_item.findtext("QualifiedItemId") or "0"
                    
                    raw_name = chest_item.findtext("name") or chest_item.findtext("DisplayName")
                    
                    # Safely handle object_map whether it returns a dict or direct str
                    mapped_entry = object_map.get(item_id)
                    if isinstance(mapped_entry, dict):
                        resolved_name = mapped_entry.get("name", raw_name or "Unknown Item")
                    elif isinstance(mapped_entry, str):
                        resolved_name = mapped_entry
                    else:
                        resolved_name = raw_name or "Unknown Item"

                    try:
                        stack = int(chest_item.findtext("stack") or 1)
                    except ValueError:
                        stack = 1

                    try:
                        quality = int(chest_item.findtext("quality") or 0)
                    except ValueError:
                        quality = 0

                    chest_items.append({
                        "id": item_id,
                        "name": resolved_name,
                        "stack": stack,
                        "quality": quality
                    })
                    total_items_found += 1

            chests_data.append({
                "location": loc_name,
                "chest_name": name or "Chest",
                "item_count": len(chest_items),
                "chest_items": chest_items
            })

    return {
        "total_chests": len(chests_data),
        "total_items": total_items_found,
        "chests": chests_data
    }
    