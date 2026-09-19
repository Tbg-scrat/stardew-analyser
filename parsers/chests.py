# parsers/chests.py

import xml.etree.ElementTree as ET


def _parse_item_node(item_node, object_map=None):
    """
    Extract detailed item metadata from an XML <Item> node.
    Returns a dictionary with is_empty=True for nil or empty slots.
    """
    # 1. Preserve empty / nil slots explicitly
    if (
        item_node is None
        or item_node.tag != "Item"
        or item_node.get("{http://www.w3.org/2001/XMLSchema-instance}nil") == "true"
    ):
        return {"is_empty": True}

    # 2. Extract item IDs
    item_id = (
        item_node.findtext("itemId")
        or item_node.findtext("parentSheetIndex")
        or "0"
    )
    qualified_id = item_node.findtext("QualifiedItemId") or f"(O){item_id}"

    sprite_key = (
        qualified_id.replace("(", "")
        .replace(")", "_")
        .replace(":", "_")
        .replace(" ", "_")
    )

    # 3. Defensive Name Resolution from object_map
    name = item_node.findtext("name")

    if object_map and isinstance(object_map, dict):
        map_entry = object_map.get(qualified_id) or object_map.get(str(item_id))
        
        if isinstance(map_entry, dict):
            # Dict type entry: safely retrieve 'name'
            name = map_entry.get("name") or name
        elif isinstance(map_entry, str):
            # String type entry: the string value IS the name
            name = map_entry

    if not name:
        name = "Unknown Item"

    # 4. Extract numeric properties safely
    try:
        stack = int(item_node.findtext("Stack") or item_node.findtext("stack") or 1)
    except ValueError:
        stack = 1

    try:
        quality = int(item_node.findtext("quality") or item_node.findtext("Quality") or 0)
    except ValueError:
        quality = 0

    quality_map = {0: "normal", 1: "silver", 2: "gold", 4: "iridium"}

    try:
        category = int(item_node.findtext("category") or 0)
    except ValueError:
        category = 0

    return {
        "is_empty": False,
        "id": item_id,
        "qualified_id": qualified_id,
        "sprite_key": sprite_key,
        "name": name,
        "stack": stack,
        "quality": quality,
        "quality_name": quality_map.get(quality, "normal"),
        "category": category,
    }


def parse_chests(root, object_map=None):
    """
    Parses chest objects across all GameLocations in the save file,
    retaining full inventory slot structures (36 or 70 slots).
    """
    chests_data = []
    total_chests = 0
    total_items = 0

    locations = root.findall(".//GameLocation")

    for loc in locations:
        loc_name = (
            loc.findtext("name")
            or loc.get("{http://www.w3.org/2001/XMLSchema-instance}type")
            or "Unknown Location"
        )

        objects = loc.find("objects")
        if objects is None:
            continue

        for item_entry in objects.findall("item"):
            obj = item_entry.find("value/Object")
            if obj is None:
                continue

            obj_type = obj.findtext("bigCraftable")
            obj_name = obj.findtext("name") or ""
            q_id = obj.findtext("QualifiedItemId") or ""

            is_chest = (
                "Chest" in obj_name
                or q_id in ["(BC)130", "(BC)232"]
                or (obj_type == "true" and obj.find("items") is not None)
            )

            if not is_chest:
                continue

            total_chests += 1
            is_big_chest = (q_id == "(BC)232") or ("Big Chest" in obj_name)
            target_capacity = 70 if is_big_chest else 36

            tile_x = obj.findtext("tileLocation/X") or "0"
            tile_y = obj.findtext("tileLocation/Y") or "0"

            color_node = obj.find("playerChoiceColor")
            chest_color = None
            if color_node is not None:
                r = color_node.findtext("R") or "0"
                g = color_node.findtext("G") or "0"
                b = color_node.findtext("B") or "0"
                a = color_node.findtext("A") or "255"
                if (r, g, b) != ("0", "0", "0"):
                    chest_color = f"rgba({r}, {g}, {b}, {int(a)/255})"

            chest_items = []
            items_container = obj.find("items")
            if items_container is not None:
                for item_node in items_container.findall("Item"):
                    parsed_item = _parse_item_node(item_node, object_map)
                    chest_items.append(parsed_item)
                    if not parsed_item.get("is_empty"):
                        total_items += parsed_item.get("stack", 1)

            # Pad remaining empty slots up to capacity (36 or 70)
            while len(chest_items) < target_capacity:
                chest_items.append({"is_empty": True})

            chests_data.append({
                "location": loc_name,
                "tile_location": {"x": int(float(tile_x)), "y": int(float(tile_y))},
                "chest_name": obj_name or ("Big Chest" if is_big_chest else "Chest"),
                "chest_color": chest_color,
                "is_big_chest": is_big_chest,
                "chest_items": chest_items,
            })

    return {
        "total_chests": total_chests,
        "total_items": total_items,
        "chests": chests_data,
    }
    