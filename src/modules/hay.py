# src/modules/hay.py

import math
import xml.etree.ElementTree as ET


def parse_hay_data(save_root: ET.Element) -> dict:
    """
    Parses stored pieces of hay, silo capacity, and farm animals to calculate
    winter feed requirements and warning flags.
    """
    # 1. Stored Hay Count
    current_hay = 0
    farm_node = save_root.find(".//locations/GameLocation[name='Farm']")
    if farm_node is not None:
        hay_elem = farm_node.find("piecesOfHay")
        if hay_elem is not None and hay_elem.text:
            try:
                current_hay = int(hay_elem.text)
            except ValueError:
                current_hay = 0

    # 2. Count Silos & Total Capacity (240 hay per Silo)
    silos_built = 0
    if farm_node is not None:
        silos_built = len(farm_node.findall(".//buildings/Building[buildingType='Silo']"))

    max_capacity = silos_built * 240

    # 3. Count Total Farm Animals across all locations & building interiors
    total_animals = len(save_root.findall(".//FarmAnimal"))

    # 4. Seasonal Feed Logic (1 hay per animal per day)
    season_elem = save_root.find("currentSeason")
    day_elem = save_root.find("dayOfMonth")

    season = (season_elem.text or "").lower() if season_elem is not None else "spring"
    try:
        day_of_month = int(day_elem.text) if day_elem is not None and day_elem.text else 1
    except ValueError:
        day_of_month = 1

    daily_consumption = total_animals * 1

    if season == "winter":
        winter_days_remaining = max(0, 28 - day_of_month + 1)
    else:
        winter_days_remaining = 28

    required_winter_hay = daily_consumption * winter_days_remaining

    # 5. Deficits and Warnings
    deficit_amount = max(0, required_winter_hay - current_hay)
    capacity_shortfall = max(0, required_winter_hay - max_capacity)

    days_of_feed_left = (
        math.floor(current_hay / daily_consumption) if daily_consumption > 0 else 999
    )

    has_deficit_warning = total_animals > 0 and deficit_amount > 0
    has_capacity_warning = total_animals > 0 and capacity_shortfall > 0

    return {
        "current_hay": current_hay,
        "silos_built": silos_built,
        "max_capacity": max_capacity,
        "total_animals": total_animals,
        "daily_consumption": daily_consumption,
        "required_winter_hay": required_winter_hay,
        "deficit_amount": deficit_amount,
        "capacity_shortfall": capacity_shortfall,
        "days_of_feed_left": days_of_feed_left,
        "has_deficit_warning": has_deficit_warning,
        "has_capacity_warning": has_capacity_warning,
    }
