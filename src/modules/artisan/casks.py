# src/modules/artisan/casks.py

import logging
import time

from src.modules.artisan.utils import (
    QUALITY_MAP,
    get_all_locations,
    resolve_item_icon,
)

logger = logging.getLogger(__name__)


def parse_casks(location_elem):
    """
    Parses active Cask objects inside a Cellar location element.
    """
    total = 0
    idle = 0
    ready_today = 0
    ready_tomorrow = 0
    processing = 0

    parsed_items = []

    objects_node = location_elem.find("objects")
    if objects_node is None:
        logger.debug("No <objects> node found inside Cellar location")
        return None

    items = objects_node.findall("item")
    logger.debug(
        f"Parsing Cellar <objects> node containing {len(items)} raw item entries"
    )

    for item in items:
        val = item.find("value")
        if val is None:
            continue

        obj = val.find("Object")
        if obj is None:
            continue

        obj_type = obj.get("{http://www.w3.org/2001/XMLSchema-instance}type", "")
        is_big_craftable = obj.findtext("bigCraftable", "").lower() == "true"
        parent_index = obj.findtext("parentSheetIndex", "")

        if obj_type != "Cask" and not (is_big_craftable and parent_index == "163"):
            continue

        total += 1

        held = obj.find("heldObject")
        is_nil = (
            held is not None
            and held.get("{http://www.w3.org/2001/XMLSchema-instance}nil") == "true"
        )

        if held is None or is_nil:
            idle += 1
            continue

        item_name = (
            held.findtext("displayName") or held.findtext("name") or "Unknown Product"
        )

        try:
            quality_raw = int(held.findtext("quality", "0"))
        except ValueError:
            logger.debug("Invalid quality value in Cask; defaulting to 0")
            quality_raw = 0
        quality_name = QUALITY_MAP.get(quality_raw, "Normal")

        try:
            days_to_mature_raw = float(obj.findtext("daysToMature", "0"))
            days_remaining = max(0, int(round(days_to_mature_raw)))
        except ValueError:
            logger.debug(
                f"Invalid daysToMature float for '{item_name}'; defaulting to 0"
            )
            days_remaining = 0

        if days_remaining == 0 or quality_raw == 4:
            ready_today += 1
            is_ready = True
            days_remaining = 0
        else:
            is_ready = False
            if days_remaining == 1:
                ready_tomorrow += 1
            else:
                processing += 1

        parsed_items.append(
            {
                "name": item_name,
                "quality": quality_raw,
                "quality_name": quality_name,
                "days_remaining": days_remaining,
                "is_ready": is_ready,
                "image": resolve_item_icon(item_name),
            }
        )

    if total == 0:
        logger.debug("No valid Cask objects found inside Cellar")
        return None

    batch_map = {}
    for cask_item in parsed_items:
        batch_key = (
            cask_item["name"],
            cask_item["quality"],
            cask_item["days_remaining"],
        )
        if batch_key not in batch_map:
            batch_map[batch_key] = {
                "name": cask_item["name"],
                "quality": cask_item["quality"],
                "quality_name": cask_item["quality_name"],
                "days_remaining": cask_item["days_remaining"],
                "is_ready": cask_item["is_ready"],
                "image": cask_item["image"],
                "count": 0,
            }
        batch_map[batch_key]["count"] += 1

    batches = sorted(
        list(batch_map.values()), key=lambda b: (b["days_remaining"], b["name"])
    )

    return {
        "total": total,
        "idle": idle,
        "ready_today": ready_today,
        "ready_tomorrow": ready_tomorrow,
        "processing": processing,
        "batches": batches,
    }


def parse_all_casks_from_save(root, player=None):
    """
    Parses active Cellar casks for the main host player.
    Standardized schema matching kegs, jars, dehydrators, and bee houses.
    """
    start_time = time.perf_counter()
    aggregated_result = {
        "total": 0,
        "idle": 0,
        "ready_today": 0,
        "ready_tomorrow": 0,
        "processing": 0,
        "idle_locations": {},
        "location_stats": {},
        "batches": [],
    }

    house_level = 0
    if player is not None:
        try:
            house_level = int(player.findtext("houseUpgradeLevel", "0"))
        except ValueError:
            house_level = 0

    if house_level < 3:
        logger.debug(
            f"Primary player houseUpgradeLevel is {house_level} (< 3). Cellar is not built."
        )
        return aggregated_result

    locations_node = root.find("locations")
    if locations_node is None:
        logger.debug("No <locations> node found in save root")
        return aggregated_result

    for loc in locations_node.findall("GameLocation"):
        loc_type = loc.get("{http://www.w3.org/2001/XMLSchema-instance}type", "")
        loc_name = loc.findtext("name", "")

        if loc_name != "Cellar" or loc_type != "Cellar":
            continue

        cask_data = parse_casks(loc)
        if cask_data:
            aggregated_result["total"] += cask_data["total"]
            aggregated_result["idle"] += cask_data["idle"]
            aggregated_result["ready_today"] += cask_data["ready_today"]
            aggregated_result["ready_tomorrow"] += cask_data["ready_tomorrow"]
            aggregated_result["processing"] += cask_data["processing"]
            aggregated_result["batches"].extend(cask_data["batches"])

            if cask_data["idle"] > 0:
                aggregated_result["idle_locations"]["Cellar"] = cask_data["idle"]

            aggregated_result["location_stats"]["Cellar"] = {
                "total": cask_data["total"],
                "idle": cask_data["idle"],
                "ready": cask_data["ready_today"],
                "ready_tomorrow": cask_data["ready_tomorrow"],
                "processing": cask_data["processing"],
            }

    final_batch_map = {}
    for b in aggregated_result["batches"]:
        key = (b["name"], b["quality"], b["days_remaining"])
        if key not in final_batch_map:
            final_batch_map[key] = dict(b)
        else:
            final_batch_map[key]["count"] += b["count"]

    aggregated_result["batches"] = sorted(
        list(final_batch_map.values()), key=lambda b: (b["days_remaining"], b["name"])
    )

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    logger.debug(
        f"Cellar: {aggregated_result['total']} Casks "
        f"({aggregated_result['processing']} aging, {aggregated_result['idle']} empty, "
        f"{aggregated_result['ready_today']} ready) parsed in {elapsed_ms:.2f}ms"
    )

    return aggregated_result
    