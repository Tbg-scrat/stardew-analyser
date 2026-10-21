# src/modules/artisan/bee_houses.py

import logging
import math
import time

from src.modules.artisan.utils import (
    QUALITY_MAP,
    get_all_locations,
    resolve_item_icon,
)

logger = logging.getLogger(__name__)


def parse_all_bee_houses_from_save(root):
    """
    Parses all Bee House objects across all locations in the save.
    In Winter, outdoor farm Bee Houses enter hibernation unless holding unharvested honey.
    Ginger Island (IslandWest, etc.) produces year-round.
    """
    start_time = time.perf_counter()

    current_season = (root.findtext("currentSeason") or "spring").lower().strip()
    is_winter = current_season == "winter"

    total = 0
    idle = 0
    hibernating = 0
    ready_today = 0
    ready_tomorrow = 0
    processing = 0

    batch_map = {}
    idle_locations = {}
    location_stats = {}

    all_locs = list(get_all_locations(root))
    logger.debug(
        f"Scanning {len(all_locs)} location nodes for Bee Houses "
        f"(Season: {current_season.capitalize()}, Winter Hibernation Active: {is_winter})"
    )

    for loc_name, loc_elem, is_outdoor in all_locs:
        objects_node = loc_elem.find("objects")
        if objects_node is None:
            continue

        loc_total, loc_idle, loc_hibernating, loc_ready, loc_ready_tomorrow, loc_proc = (
            0,
            0,
            0,
            0,
            0,
            0,
        )

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

            is_bee_house = (
                obj_name == "Bee House"
                or q_id in ["(BC)10", "(BC)BeeHouse"]
                or (is_big_craftable and parent_index == "10")
            )

            if not is_bee_house:
                continue

            total += 1
            loc_total += 1

            held = obj.find("heldObject")
            is_nil = (
                held is None
                or held.get("{http://www.w3.org/2001/XMLSchema-instance}nil") == "true"
            )

            is_ginger_island = loc_name in [
                "IslandWest",
                "IslandNorth",
                "IslandEast",
                "IslandSouth",
            ]

            ready_for_harvest = (
                obj.findtext("readyForHarvest", "false").lower() == "true"
            )

            try:
                minutes_until_ready = int(obj.findtext("minutesUntilReady", "0"))
            except ValueError:
                minutes_until_ready = 0

            # Preserve unharvested honey produced prior to Winter
            if not is_nil and (ready_for_harvest or minutes_until_ready <= 0):
                days_remaining = 0
                is_ready = True
            elif is_winter and is_outdoor and not is_ginger_island:
                hibernating += 1
                loc_hibernating += 1
                continue
            elif is_nil:
                idle += 1
                loc_idle += 1
                idle_locations[loc_name] = idle_locations.get(loc_name, 0) + 1
                continue
            else:
                is_ready = False
                days_remaining = max(1, math.ceil(minutes_until_ready / 1600))

            item_name = held.findtext("displayName") or held.findtext("name") or "Honey"

            try:
                quality_raw = int(held.findtext("quality", "0"))
            except ValueError:
                quality_raw = 0
            quality_name = QUALITY_MAP.get(quality_raw, "Normal")

            if days_remaining == 0:
                ready_today += 1
                loc_ready += 1
            elif days_remaining == 1:
                ready_tomorrow += 1
                loc_ready_tomorrow += 1
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
                    "image": resolve_item_icon(item_name),
                    "count": 0,
                }
            batch_map[batch_key]["count"] += 1

        if loc_total > 0:
            location_stats[loc_name] = {
                "total": loc_total,
                "idle": loc_idle,
                "hibernating": loc_hibernating,
                "ready": loc_ready,
                "ready_tomorrow": loc_ready_tomorrow,
                "processing": loc_proc,
            }

    sorted_batches = sorted(
        list(batch_map.values()), key=lambda b: (b["days_remaining"], b["name"])
    )

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    logger.debug(
        f"Bee Houses summary: {total} total Bee Houses parsed "
        f"({hibernating} hibernating) across all locations in {elapsed_ms:.2f}ms"
    )

    return {
        "total": total,
        "idle": idle,
        "hibernating": hibernating,
        "ready_today": ready_today,
        "ready_tomorrow": ready_tomorrow,
        "processing": processing,
        "idle_locations": idle_locations,
        "location_stats": location_stats,
        "batches": sorted_batches,
    }
    