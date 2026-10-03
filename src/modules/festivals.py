# src/modules/festivals.py
# -*- coding: utf-8 -*-
"""
Festivals module for Stardew Valley save file parsing.
Determines the current date and calculates upcoming seasonal festivals using FESTIVALS_CATALOG.
"""

import logging
import time
from data.data_loader import FESTIVALS_CATALOG

logger = logging.getLogger(__name__)


def parse_festivals(root, catalog=None):
    """
    Parses current date and identifies the next upcoming festival in the season.

    :param root: xml.etree.ElementTree Element representing <SaveGame>
    :param catalog: dict optional override for FESTIVALS_CATALOG
    :return: dict containing current date info and next festival details
    """
    start_time = time.perf_counter()

    festivals_catalog = catalog if catalog is not None else FESTIVALS_CATALOG
    if catalog is None:
        logger.debug("Using default FESTIVALS_CATALOG")

    if root is None:
        logger.warning("SaveGame root is None. Defaulting to Spring Day 1 festival status.")
        return {"current_day": 1, "season": "spring", "next_festival": None, "status_text": "None"}

    season_node = root.find("currentSeason")
    day_node = root.find("dayOfMonth")

    season = season_node.text.lower() if season_node is not None and season_node.text else "spring"
    try:
        day = int(day_node.text) if day_node is not None and day_node.text else 1
    except ValueError:
        logger.debug(f"Invalid dayOfMonth text '{day_node.text if day_node is not None else None}'; defaulting to 1")
        day = 1

    seasonal_festivals = festivals_catalog.get(season, [])
    
    # Find next festival today or later in current season
    upcoming = [f for f in seasonal_festivals if f.get("day", 0) >= day]

    if upcoming:
        next_event = upcoming[0]
        days_away = next_event["day"] - day
        status_text = "Today!" if days_away == 0 else f"In {days_away} day{'s' if days_away > 1 else ''} (Day {next_event['day']})"
        logger.debug(f"Next festival: {next_event['name']} on {season.capitalize()} {next_event['day']} ({status_text})")
    else:
        next_event = None
        status_text = "None remaining this season"
        logger.debug(f"No remaining festivals in {season.capitalize()} after day {day}")

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    logger.debug(f"Festivals module parsed in {elapsed_ms:.2f}ms")

    return {
        "season": season.capitalize(),
        "day": day,
        "next_festival": next_event,
        "status_text": status_text
    }
    