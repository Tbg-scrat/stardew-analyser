# cask_parser.py
import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

QUALITY_MAP = {
    0: "Normal",
    1: "Silver",
    2: "Gold",
    4: "Iridium"
}

def parse_casks(location_elem):
    """
    Parses all Cask objects within a given location XML element (e.g. Cellar).
    Returns an aggregated dictionary containing counts and batch details.
    """
    total_casks = 0
    empty_casks = 0
    ready_today = 0
    ready_tomorrow = 0
    aging_count = 0

    # Raw list of parsed cask items
    parsed_items = []

    # Locate the <objects> container in the location
    objects_node = location_elem.find("objects")
    if objects_node is None:
        logger.debug("[DEBUG cask_parser] No <objects> node found in location.")
        return None

    for item in objects_node.findall("item"):
        val = item.find("value")
        if val is None:
            continue

        obj = val.find("Object")
        if obj is None:
            continue

        # Verify if object is a Cask
        obj_type = obj.get("{http://www.w3.org/2001/XMLSchema-instance}type", "")
        obj_name = obj.findtext("name", "")

        if obj_type != "Cask" and obj_name != "Cask":
            continue

        total_casks += 1

        held = obj.find("heldObject")
        # Check if heldObject exists and is not xsi:nil
        is_nil = held is not None and held.get("{http://www.w3.org/2001/XMLSchema-instance}nil") == "true"

        if held is None or is_nil:
            empty_casks += 1
            continue

        item_name = held.findtext("displayName") or held.findtext("name") or "Unknown Product"
        
        # Read quality level
        try:
            quality_raw = int(held.findtext("quality", "0"))
        except ValueError:
            quality_raw = 0
        quality_name = QUALITY_MAP.get(quality_raw, "Normal")

        # Read remaining aging days
        try:
            time_to_mature = float(obj.findtext("timeToMature", "0"))
            days_remaining = max(0, int(round(time_to_mature)))
        except ValueError:
            days_remaining = 0

        # Status categorization
        if days_remaining == 0:
            ready_today += 1
            is_ready = True
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
            "wiki_icon": item_name.replace(" ", "_")
        })

    if total_casks == 0:
        logger.debug("[DEBUG cask_parser] No Casks detected in this location.")
        return None

    # Aggregate individual casks into batches (grouped by item name, quality, and days remaining)
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

    logger.info(
        f"[DEBUG cask_parser] Found {total_casks} total Casks "
        f"({ready_today} ready today, {ready_tomorrow} ready tomorrow, "
        f"{aging_count} aging, {empty_casks} empty)."
    )
    for b in batches:
        status_str = "Ready Today!" if b["is_ready"] else f"{b['days_remaining']} days remaining"
        logger.debug(
            f"[DEBUG cask_parser] Batch: {b['count']}x {b['name']} ({b['quality_name']}) - {status_str}"
        )

    return {
        "total_casks": total_casks,
        "empty_casks": empty_casks,
        "ready_today": ready_today,
        "ready_tomorrow": ready_tomorrow,
        "aging_count": aging_count,
        "batches": batches
    }


def parse_all_casks_from_save(root):
    """
    Searches all locations in the save XML for Casks and aggregates the total.
    """
    aggregated_result = {
        "total_casks": 0,
        "empty_casks": 0,
        "ready_today": 0,
        "ready_tomorrow": 0,
        "aging_count": 0,
        "batches": []
    }

    locations_node = root.find("locations")
    if locations_node is None:
        return aggregated_result

    for loc in locations_node.findall("GameLocation"):
        loc_type = loc.get("{http://www.w3.org/2001/XMLSchema-instance}type", "")
        
        # Scan Cellars specifically (or any location containing objects)
        cask_data = parse_casks(loc)
        if cask_data:
            aggregated_result["total_casks"] += cask_data["total_casks"]
            aggregated_result["empty_casks"] += cask_data["empty_casks"]
            aggregated_result["ready_today"] += cask_data["ready_today"]
            aggregated_result["ready_tomorrow"] += cask_data["ready_tomorrow"]
            aggregated_result["aging_count"] += cask_data["aging_count"]
            aggregated_result["batches"].extend(cask_data["batches"])

    # Re-aggregate batches across multiple locations if necessary
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
    