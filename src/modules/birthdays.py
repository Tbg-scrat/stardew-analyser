# src/modules/birthdays.py
# -*- coding: utf-8 -*-
"""
Birthdays module for Stardew Valley save file parsing.
Tracks villager birthdays, identifies the next upcoming birthday, and attaches loved gifts.
"""

import logging
import time
from data.data_loader import VILLAGERS_CATALOG
from src.core.gift_data import get_loved_gifts

logger = logging.getLogger(__name__)


def get_seasonal_birthdays(season_name):
    """Builds a sorted list of birthday dicts for a given season from VILLAGERS_CATALOG."""
    villagers_map = VILLAGERS_CATALOG.get("villagers", {})
    seasonal_list = []

    for name, meta in villagers_map.items():
        bday_info = meta.get("birthday")
        if bday_info and bday_info.get("season") == season_name.lower():
            seasonal_list.append({
                "day": bday_info.get("day"),
                "name": name,
                "icon": "\U0001F382"
            })

    return sorted(seasonal_list, key=lambda b: b["day"])


def parse_birthdays(root):
    """
    Parses current date, identifies the next upcoming birthday in the season,
    and attaches loved gift details.

    :param root: xml.etree.ElementTree Element representing <SaveGame>
    :return: dict containing next birthday details, status text, and loved gifts
    """
    start_time = time.perf_counter()

    if root is None:
        logger.warning("SaveGame root is None. Defaulting to no upcoming birthday.")
        return {"next_birthday": None, "status_text": "None"}

    season_node = root.find("currentSeason")
    day_node = root.find("dayOfMonth")

    season = season_node.text.lower() if season_node is not None and season_node.text else "spring"
    try:
        day = int(day_node.text) if day_node is not None and day_node.text else 1
    except ValueError:
        logger.debug(f"Invalid dayOfMonth text '{day_node.text if day_node is not None else None}'; defaulting to 1")
        day = 1

    seasonal_birthdays = get_seasonal_birthdays(season)
    upcoming = [b for b in seasonal_birthdays if b["day"] >= day]

    if upcoming:
        next_bday = dict(upcoming[0])
        days_away = next_bday["day"] - day
        status_text = "Today!" if days_away == 0 else f"In {days_away} day{'s' if days_away > 1 else ''} (Day {next_bday['day']})"
        next_bday["loved_gifts"] = get_loved_gifts(next_bday["name"])
        logger.debug(f"Next birthday: {next_bday['name']} on {season.capitalize()} {next_bday['day']} ({status_text})")
    else:
        next_bday = None
        status_text = "None remaining this season"
        logger.debug(f"No remaining birthdays in {season.capitalize()} after day {day}")

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    logger.debug(f"Birthdays module parsed in {elapsed_ms:.2f}ms")

    return {
        "next_birthday": next_bday,
        "status_text": status_text
    }
    