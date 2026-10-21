# src/modules/chests.py

import logging
import time

from src.core.reference_data import get_object_info

logger = logging.getLogger(__name__)


def _parse_item_node(item_node):
    """
    Extract detailed item metadata from an XML <Item> node.
    Returns a dictionary with is_empty=True for nil or empty slots.
    """
    if (
        item_node is None
        or item_node.tag != "Item"
        or item_node.get("{http://www.w3.org/2001/XMLSchema-instance}nil") == "true"
    ):
        return {"is_empty": True}

    item_id = (
        item_node.findtext("itemId") or item_node.findtext("parentSheetIndex") or "0"
    )

    # Detect item types strictly from XML xsi:type or tags (no ID fallback collisions)
    item_xsi_type = item_node.get("{http://www.w3.org/2001/XMLSchema-instance}type", "")
    is_big_craftable = item_node.findtext("bigCraftable", "").lower() == "true"
    
    is_weapon = (
        "Weapon" in item_xsi_type 
        or item_xsi_type in ["MeleeWeapon", "Slingshot"]
    )
    
    is_tool = (
        item_node.tag == "Tool"
        or "Tool" in item_xsi_type
        or "Rod" in item_xsi_type
        or item_xsi_type in ["FishingRod", "Pan", "Shears", "MilkPail", "Wand", "Axe", "Pickaxe", "Hoe", "WateringCan", "GenericTool"]
    )

    # Explicit namespace prefix mapping based strictly on xsi:type or tags
    if is_tool:
        default_prefix = "(T)"
    elif is_weapon:
        default_prefix = "(W)"
    elif is_big_craftable or item_xsi_type == "BigCraftable":
        default_prefix = "(BC)"
    elif item_xsi_type in ["Object", "ColoredObject", "Torch"]:
        default_prefix = "(O)"
    elif item_xsi_type == "Ring":
        default_prefix = "(R)"
    elif item_xsi_type == "Boots":
        default_prefix = "(B)"
    elif item_xsi_type == "Hat":
        default_prefix = "(H)"
    elif item_xsi_type == "Furniture":
        default_prefix = "(F)"
    elif item_xsi_type == "Wallpaper":
        default_prefix = "(WP)"
    elif item_xsi_type == "Flooring":
        default_prefix = "(FL)"
    elif item_xsi_type == "Clothing":
        default_prefix = "(S)"
    else:
        raise ValueError(f"Unrecognized item xsi:type '{item_xsi_type}' for item ID: {item_id}")

    xml_name = item_node.findtext("name")
    identifier = item_id if item_id else (xml_name or "0")

    qualified_id = item_node.findtext("QualifiedItemId") or f"{default_prefix}{identifier}"

    # Extract the prefix strictly for image routing
    raw_prefix = "items"
    if qualified_id.startswith("(") and ")" in qualified_id:
        raw_prefix = qualified_id.split(")")[0].replace("(", "")

    # Pass strictly qualified_id into reference_data lookup
    obj_info = get_object_info(qualified_id, fallback_name=xml_name)
    name = obj_info.get("name")

    sprite_key = obj_info.get("sprite_key")
    resolved_prefix = obj_info.get("prefix") or raw_prefix
    icon = obj_info.get("icon")

    if not name:
        logger.debug(
            f"Missing item name for ID '{qualified_id}'; defaulting to 'Unknown Item'"
        )
        name = "Unknown Item"

    try:
        stack = int(item_node.findtext("Stack") or item_node.findtext("stack") or 1)
    except ValueError:
        logger.debug(f"Invalid stack value for '{qualified_id}'; defaulting to 1")
        stack = 1

    try:
        quality = int(
            item_node.findtext("quality") or item_node.findtext("Quality") or 0
        )
    except ValueError:
        logger.debug(f"Invalid quality value for '{qualified_id}'; defaulting to 0")
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
        "prefix": resolved_prefix,
        "sprite_key": sprite_key,
        "icon": icon,
        "name": name,
        "stack": stack,
        "quality": quality,
        "quality_name": quality_map.get(quality, "normal"),
        "category": category,
    }


def _extract_raw_chests(root):
    """
    Parses chest objects across all GameLocations in the save file.
    """
    chests_data = []
    total_chests = 0
    total_items = 0
    empty_slots = 0

    locations = root.findall(".//GameLocation")
    logger.debug(f"Searching for chests across {len(locations)} GameLocation nodes")

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
                    chest_color = f"rgba({r}, {g}, {b}, {int(a) / 255})"

            chest_items = []
            items_container = obj.find("items")
            if items_container is not None:
                for item_node in items_container.findall("Item"):
                    parsed_item = _parse_item_node(item_node)
                    chest_items.append(parsed_item)
                    if not parsed_item.get("is_empty"):
                        total_items += parsed_item.get("stack", 1)
                    else:
                        empty_slots += 1

            while len(chest_items) < target_capacity:
                chest_items.append({"is_empty": True})
                empty_slots += 1

            chests_data.append(
                {
                    "location": loc_name,
                    "tile_location": {"x": int(float(tile_x)), "y": int(float(tile_y))},
                    "chest_name": obj_name
                    or ("Big Chest" if is_big_chest else "Chest"),
                    "chest_color": chest_color,
                    "is_big_chest": is_big_chest,
                    "chest_items": chest_items,
                }
            )

    return {
        "total_chests": total_chests,
        "total_items": total_items,
        "chests": chests_data,
    }


def parse_chests(root, object_map=None):
    """
    Main entry point for parsing chest data from save XML.
    Uses get_object_info via reference_data for item metadata lookups.
    """
    start_time = time.perf_counter()

    raw_chests = _extract_raw_chests(root)
    material_totals = {}

    for chest in raw_chests.get("chests", []):
        for item in chest.get("chest_items", []):
            if item.get("is_empty"):
                continue

            item_name = item.get("name", "Unknown Item")
            stack = item.get("stack", 1)
            sprite_key = item.get("sprite_key", "")
            prefix = item.get("prefix", "items")
            icon = item.get("icon", "")

            if item_name not in material_totals:
                material_totals[item_name] = {
                    "name": item_name,
                    "count": 0,
                    "prefix": prefix,
                    "sprite_key": sprite_key,
                    "icon": icon,
                }

            material_totals[item_name]["count"] += stack

    sorted_materials = sorted(
        material_totals.values(), key=lambda x: x["count"], reverse=True
    )

    return {
        "total_chests": raw_chests.get("total_chests", 0),
        "total_items": raw_chests.get("total_items", 0),
        "chests": raw_chests.get("chests", []),
        "material_totals": sorted_materials,
    }
    