# src/modules/artisan/kegs.py

import json
import math
import logging
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

QUALITY_MAP = {0: "Normal", 1: "Silver", 2: "Gold", 4: "Iridium"}


def resolve_item_icon(item_name):
    """
    Returns local sprite filename for color-mapped artisan goods or 
    defaults to standard Wiki filename formatting.
    """
    name_lower = item_name.lower().strip()
    if name_lower in ARTISAN_COLORS:
        return ARTISAN_COLORS[name_lower]
    return item_name.replace(" ", "_").replace("'", "%27") + ".png"


def _get_all_locations(root):
    """
    Recursively scans all GameLocations, including building interiors
    (Sheds, Barns, Coops, Cellar).
    """
    locations_node = root.find("locations")
    if locations_node is None:
        return

    def _traverse_location(loc_elem, default_name="Unknown"):
        loc_name = loc_elem.findtext("name") or default_name
        yield loc_name, loc_elem

        buildings = loc_elem.find("buildings")
        if buildings is not None:
            for b_idx, building in enumerate(buildings.findall("Building")):
                b_type = building.findtext("buildingType") or "Building"
                indoors = building.find("indoors")
                if indoors is not None:
                    indoor_name = indoors.findtext("name") or f"{b_type} #{b_idx + 1}"
                    yield from _traverse_location(indoors, indoor_name)

    for loc in locations_node.findall("GameLocation"):
        yield from _traverse_location(loc)


def parse_all_kegs_from_save(root):
    """
    Parses all Keg objects across all locations in the save.
    Keg QualifiedItemId: (BC)12 or name=="Keg" or parentSheetIndex=="12".
    """
    total = 0
    idle = 0
    ready_today = 0
    ready_tomorrow = 0
    processing = 0

    batch_map = {}
    idle_locations = {}
    location_stats = {}

    for loc_name, loc_elem in _get_all_locations(root):
        objects_node = loc_elem.find("objects")
        if objects_node is None:
            continue

        loc_total, loc_idle, loc_ready, loc_proc = 0, 0, 0, 0

        for item in objects_node.findall("item"):
            val = item.find("value")
            if val is None:
                continue

            obj = val.find("Object")
            if obj is None:
                continue

            obj_name = obj.findtext("name", "")
            parent_index = obj.findtext("parentSheetIndex", "")
            q_id = obj.findtext("QualifiedItemId", "")
            is_big_craftable = obj.findtext("bigCraftable", "").lower() == "true"

            # Explicitly exclude Furnaces and non-keg machinery
            if obj_name in ["Furnace", "Heavy Furnace"] or q_id in ["(BC)13", "(BC)HeavyFurnace"]:
                continue

            # Keg Identification: (BC)12 or name == "Keg"
            is_keg = (
                obj_name == "Keg"
                or q_id in ["(BC)12", "(BC)Keg"]
                or (is_big_craftable and parent_index == "12")
            )

            if not is_keg:
                continue

            total += 1
            loc_total += 1

            held = obj.find("heldObject")
            is_nil = (
                held is None
                or held.get("{http://www.w3.org/2001/XMLSchema-instance}nil") == "true"
            )

            if is_nil:
                idle += 1
                loc_idle += 1
                idle_locations[loc_name] = idle_locations.get(loc_name, 0) + 1
                continue

            item_name = (
                held.findtext("displayName") or held.findtext("name") or "Unknown Product"
            )

            try:
                quality_raw = int(held.findtext("quality", "0"))
            except ValueError:
                quality_raw = 0
            quality_name = QUALITY_MAP.get(quality_raw, "Normal")

            ready_for_harvest = (
                obj.findtext("readyForHarvest", "false").lower() == "true"
            )

            try:
                minutes_until_ready = int(obj.findtext("minutesUntilReady", "0"))
            except ValueError:
                minutes_until_ready = 0

            if ready_for_harvest or minutes_until_ready <= 0:
                days_remaining = 0
                is_ready = True
            else:
                is_ready = False
                days_remaining = max(1, math.ceil(minutes_until_ready / 1600))

            if days_remaining == 0:
                ready_today += 1
                loc_ready += 1
            elif days_remaining == 1:
                ready_tomorrow += 1
                loc_proc += 1
            else:
                processing += 1
                loc_proc += 1

            batch_key = (item_name, quality_raw, days_remaining)
            if batch_key not in batch_map:
                batch_map[batch_key] = {
                    "name": item_name,
                    "quality": quality_raw,
                    "quality_name": quality_name,
                    "days_remaining": days_remaining,
                    "is_ready": is_ready,
                    "wiki_icon": resolve_item_icon(item_name),
                    "count": 0,
                }
            batch_map[batch_key]["count"] += 1

        if loc_total > 0:
            location_stats[loc_name] = {
                "total": loc_total,
                "idle": loc_idle,
                "ready": loc_ready,
                "processing": loc_proc,
            }
            print(
                f"[DEBUG kegs.py] {loc_name}: {loc_total} Kegs "
                f"({loc_proc} processing, {loc_idle} idle, {loc_ready} ready)"
            )

    sorted_batches = sorted(
        list(batch_map.values()),
        key=lambda b: (b["days_remaining"], b["name"])
    )

    return {
        "total": total,
        "idle": idle,
        "ready_today": ready_today,
        "ready_tomorrow": ready_tomorrow,
        "processing": processing,
        "idle_locations": idle_locations,
        "location_stats": location_stats,
        "batches": sorted_batches,
    }
    