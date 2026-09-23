# -*- coding: utf-8 -*-
import json
import logging
import xml.etree.ElementTree as ET
from pathlib import Path

logger = logging.getLogger(__name__)

# Load artisan color mapping
ARTISAN_COLORS_FILE = Path("data/artisan_colors.json")
ARTISAN_COLORS = {}
if ARTISAN_COLORS_FILE.exists():
    try:
        with open(ARTISAN_COLORS_FILE, "r", encoding="utf-8") as f:
            ARTISAN_COLORS = json.load(f)
    except Exception as e:
        logger.warning(f"Could not load artisan colors map: {e}")

QUALITY_MAP = {
    0: "Normal",
    1: "Silver",
    2: "Gold",
    4: "Iridium"
}

def resolve_item_icon(item_name):
    """
    Returns local sprite filename for color-mapped artisan goods or 
    defaults to standard Wiki filename formatting.
    """
    name_lower = item_name.lower().strip()
    
    if name_lower in ARTISAN_COLORS:
        return ARTISAN_COLORS[name_lower]
    
    return item_name.replace(" ", "_").replace("'", "%27")


def parse_casks(location_elem):
    """
    Parses active Cask objects inside a Cellar location element.
    """
    total_casks = 0
    empty_casks = 0
    ready_today = 0
    ready_tomorrow = 0
    aging_count = 0

    parsed_items = []

    objects_node = location_elem.find("objects")
    if objects_node is None:
        return None

    for item in objects_node.findall("item"):
        val = item.find("value")
        if val is None:
            continue

        obj = val.find("Object")
        if obj is None:
            continue

        obj_type = obj.get("{http://www.w3.org/2001/XMLSchema-instance}type", "")
        is_big_craftable = obj.findtext("bigCraftable", "").lower() == "true"
        parent_index = obj.findtext("parentSheetIndex", "")

        # Genuine aging Casks have xsi:type="Cask" or (bigCraftable=true AND parentSheetIndex=163)
        if obj_type != "Cask" and not (is_big_craftable and parent_index == "163"):
            continue

        total_casks += 1

        held = obj.find("heldObject")
        is_nil = held is not None and held.get("{http://www.w3.org/2001/XMLSchema-instance}nil") == "true"

        if held is None or is_nil:
            empty_casks += 1
            continue

        item_name = held.findtext("displayName") or held.findtext("name") or "Unknown Product"
        
        try:
            quality_raw = int(held.findtext("quality", "0"))
        except ValueError:
            quality_raw = 0
        quality_name = QUALITY_MAP.get(quality_raw, "Normal")

        try:
            days_to_mature_raw = float(obj.findtext("daysToMature", "0"))
            days_remaining = max(0, int(round(days_to_mature_raw)))
        except ValueError:
            days_remaining = 0

        if days_remaining == 0 or quality_raw == 4:
            ready_today += 1
            is_ready = True
            days_remaining = 0
        else:
            aging_count += 1
            is_ready = False
            if days_remaining == 1:
                ready_tomorrow += 1

        parsed_items.append({
            "name": item_name,
            "quality": quality_raw,
            "quality_name": quality_name,
            "days_remaining": days_remaining,
            "is_ready": is_ready,
            "wiki_icon": resolve_item_icon(item_name)
        })

    if total_casks == 0:
        return None

    batch_map = {}
    for cask_item in parsed_items:
        batch_key = (cask_item["name"], cask_item["quality"], cask_item["days_remaining"])
        if batch_key not in batch_map:
            batch_map[batch_key] = {
                "name": cask_item["name"],
                "quality": cask_item["quality"],
                "quality_name": cask_item["quality_name"],
                "days_remaining": cask_item["days_remaining"],
                "is_ready": cask_item["is_ready"],
                "wiki_icon": cask_item["wiki_icon"],
                "count": 0
            }
        batch_map[batch_key]["count"] += 1

    batches = sorted(
        list(batch_map.values()),
        key=lambda b: (b["days_remaining"], b["name"])
    )

    return {
        "total_casks": total_casks,
        "empty_casks": empty_casks,
        "ready_today": ready_today,
        "ready_tomorrow": ready_tomorrow,
        "aging_count": aging_count,
        "batches": batches
    }


def parse_all_casks_from_save(root, player=None):
    """
    Parses active Cellar casks for the main host player.
    Secondary template cellars (Cellar2..Cellar8) are disregarded.
    """
    aggregated_result = {
        "total_casks": 0,
        "empty_casks": 0,
        "ready_today": 0,
        "ready_tomorrow": 0,
        "aging_count": 0,
        "batches": []
    }

    # Verify Host House Upgrade Level (Level 3 = Cellar Upgrade)
    house_level = 0
    if player is not None:
        try:
            house_level = int(player.findtext("houseUpgradeLevel", "0"))
        except ValueError:
            house_level = 0

    if house_level < 3:
        logger.debug("[casks.py] Primary player houseUpgradeLevel < 3. Cellar is not built.")
        return aggregated_result

    locations_node = root.find("locations")
    if locations_node is None:
        return aggregated_result

    for loc in locations_node.findall("GameLocation"):
        loc_type = loc.get("{http://www.w3.org/2001/XMLSchema-instance}type", "")
        loc_name = loc.findtext("name", "")

        # Target primary host cellar only
        if loc_name != "Cellar" or loc_type != "Cellar":
            continue

        cask_data = parse_casks(loc)
        if cask_data:
            aggregated_result["total_casks"] += cask_data["total_casks"]
            aggregated_result["empty_casks"] += cask_data["empty_casks"]
            aggregated_result["ready_today"] += cask_data["ready_today"]
            aggregated_result["ready_tomorrow"] += cask_data["ready_tomorrow"]
            aggregated_result["aging_count"] += cask_data["aging_count"]
            aggregated_result["batches"].extend(cask_data["batches"])

    final_batch_map = {}
    for b in aggregated_result["batches"]:
        key = (b["name"], b["quality"], b["days_remaining"])
        if key not in final_batch_map:
            final_batch_map[key] = dict(b)
        else:
            final_batch_map[key]["count"] += b["count"]

    aggregated_result["batches"] = sorted(
        list(final_batch_map.values()),
        key=lambda b: (b["days_remaining"], b["name"])
    )

    return aggregated_result
    