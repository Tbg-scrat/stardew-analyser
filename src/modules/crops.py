# src/modules/crops.py

import logging
from collections import defaultdict

from src.core.reference_data import get_object_info

logger = logging.getLogger("parse")

# Standard season day limit in Stardew Valley
DAYS_IN_SEASON = 28


def calculate_days_remaining(crop_node) -> dict:
    """
    Calculates remaining days until harvest for a crop based on XML node fields.
    Returns a dict with 'days_to_harvest', 'is_recurring', 'fully_grown', and 'harvest_id'.
    """
    harvest_id = crop_node.findtext("indexOfHarvest") if crop_node is not None else None
    try:
        current_phase = int(crop_node.findtext("currentPhase", "0"))
        day_of_phase = int(crop_node.findtext("dayOfCurrentPhase", "0"))

        # Stardew Valley XML uses <fullGrown>, check both <fullGrown> and <fullyGrown>
        full_grown = (
            crop_node.findtext("fullGrown", "false").lower() == "true"
            or crop_node.findtext("fullyGrown", "false").lower() == "true"
        )

        regrow_after_harvest = int(crop_node.findtext("regrowAfterHarvest", "-1"))
        is_recurring = regrow_after_harvest != -1 or full_grown

        phase_days_nodes = crop_node.findall(".//phaseDays/int")
        phase_days = [int(p.text) for p in phase_days_nodes if p.text is not None]

        # Case 1: Fully grown regrowing crop (day_of_phase is exact countdown to next harvest)
        if full_grown:
            return {
                "days_to_harvest": day_of_phase,
                "is_recurring": True,
                "fully_grown": True,
                "harvest_id": harvest_id,
            }

        # Case 2: Final growth phase reached during initial growth (ready to harvest today)
        if phase_days and current_phase >= len(phase_days) - 1:
            return {
                "days_to_harvest": 0,
                "is_recurring": is_recurring,
                "fully_grown": False,
                "harvest_id": harvest_id,
            }

        # Case 3: In active initial growth phase
        remaining_days = 0
        if phase_days and current_phase < len(phase_days) - 1:
            remaining_days += max(0, phase_days[current_phase] - day_of_phase)
            for p_len in phase_days[current_phase + 1 : len(phase_days) - 1]:
                remaining_days += p_len

        return {
            "days_to_harvest": remaining_days,
            "is_recurring": is_recurring,
            "fully_grown": False,
            "harvest_id": harvest_id,
        }

    except Exception as e:
        logger.debug(f"Error calculating crop lifecycle: {e}")
        return {
            "days_to_harvest": 0,
            "is_recurring": False,
            "fully_grown": False,
            "harvest_id": harvest_id,
        }


# Export alias expected by unit tests
parse_crop = calculate_days_remaining


def parse_crops_from_location(
    location_node, current_day=1, is_outdoor_farm=False
) -> dict:
    """
    Parses all HoeDirt crops within a given location XML node.
    Groups identical crop types by harvest maturity time.
    """
    crop_counts = defaultdict(
        lambda: {
            "count": 0,
            "days_to_harvest": 0,
            "is_recurring": False,
            "will_wither": False,
        }
    )

    if location_node is None:
        return {
            "total_crops": 0,
            "ready_today": 0,
            "next_harvest_days": None,
            "items": [],
        }

    # Iterate through terrain features for HoeDirt crop nodes
    for item in location_node.findall(".//terrainFeatures/item"):
        crop_node = item.find(".//value/TerrainFeature/crop")
        if crop_node is None:
            continue

        harvest_id = crop_node.findtext("indexOfHarvest")

        # Skip unplanted, harvested, or invalid crop slots
        if not harvest_id or harvest_id in ("None", "-1", ""):
            continue

        lifecycle = calculate_days_remaining(crop_node)
        days_left = lifecycle["days_to_harvest"]
        is_recurring = lifecycle["is_recurring"]

        # Check season expiration warning for main farm crops
        will_wither = False
        if is_outdoor_farm and not is_recurring:
            if (current_day + days_left) > DAYS_IN_SEASON:
                will_wither = True

        group_key = (harvest_id, days_left)
        crop_counts[group_key]["count"] += 1
        crop_counts[group_key]["days_to_harvest"] = days_left
        crop_counts[group_key]["is_recurring"] = is_recurring
        crop_counts[group_key]["will_wither"] = (
            crop_counts[group_key]["will_wither"] or will_wither
        )

    items = []
    total_crops = 0
    ready_today = 0
    next_harvest_days = None

    for (harvest_id, days_left), info in crop_counts.items():
        obj_info = get_object_info(harvest_id)
        count = info["count"]
        total_crops += count

        if days_left == 0:
            ready_today += count

        if next_harvest_days is None or days_left < next_harvest_days:
            next_harvest_days = days_left

        unit_price = obj_info.get("price", 0)
        items.append(
            {
                "harvest_id": harvest_id,
                "name": obj_info.get("name", "Unknown"),
                "icon": obj_info.get("icon"),
                "price": unit_price,
                "count": count,
                "days_to_harvest": days_left,
                "is_recurring": info["is_recurring"],
                "will_wither": info["will_wither"],
                "total_value": unit_price * count,
            }
        )

    # Sort items by days remaining (ascending) then name
    items.sort(key=lambda x: (x["days_to_harvest"], x["name"]))

    return {
        "total_crops": total_crops,
        "ready_today": ready_today,
        "next_harvest_days": next_harvest_days,
        "items": items,
    }


def parse_all_crops_from_save(root, current_day=1) -> dict:
    """
    Parses crops across all primary crop locations: Main Farm, Greenhouse, and Ginger Island (IslandWest).
    """
    locations = {"farm": None, "greenhouse": None, "ginger_island": None}

    if root is None:
        return {
            "summary": {"total_crops": 0, "ready_today": 0},
            "locations": {
                "farm": parse_crops_from_location(None),
                "greenhouse": parse_crops_from_location(None),
                "ginger_island": parse_crops_from_location(None),
            },
        }

    for loc in root.findall(".//locations/GameLocation"):
        loc_name = loc.findtext("name", "")
        loc_type = loc.get("{http://www.w3.org/2001/XMLSchema-instance}type", "")

        if loc_name == "Farm" or loc_type == "Farm":
            locations["farm"] = loc
        elif loc_name == "Greenhouse" or loc_type == "Greenhouse":
            locations["greenhouse"] = loc
        elif loc_name == "IslandWest" or loc_type == "IslandWest":
            locations["ginger_island"] = loc

    farm_data = parse_crops_from_location(
        locations["farm"], current_day=current_day, is_outdoor_farm=True
    )
    greenhouse_data = parse_crops_from_location(
        locations["greenhouse"], current_day=current_day, is_outdoor_farm=False
    )
    island_data = parse_crops_from_location(
        locations["ginger_island"], current_day=current_day, is_outdoor_farm=False
    )

    total_crops = (
        farm_data["total_crops"]
        + greenhouse_data["total_crops"]
        + island_data["total_crops"]
    )
    ready_today = (
        farm_data["ready_today"]
        + greenhouse_data["ready_today"]
        + island_data["ready_today"]
    )

    return {
        "summary": {"total_crops": total_crops, "ready_today": ready_today},
        "locations": {
            "farm": farm_data,
            "greenhouse": greenhouse_data,
            "ginger_island": island_data,
        },
    }
