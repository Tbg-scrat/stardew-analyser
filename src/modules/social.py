# src/modules/social.py
"""
Social module for Stardew Valley save file parsing.
Extracts villager friendships, heart levels, daily interaction statuses, loved gift preferences,
and handles sorting by friendship points and marital status.
"""

import logging
import time

from data.data_loader import VILLAGERS_CATALOG

logger = logging.getLogger(__name__)


def format_wiki_filename(name):
    """Clean item names into Stardew Valley Wiki image file conventions."""
    return name.replace(" ", "_").replace("'", "%27")


def get_loved_gifts(villager_name):
    """Returns a list of dicts containing name and wiki_icon for a villager's loved gifts."""
    villagers_map = VILLAGERS_CATALOG.get("villagers", {})
    villager_data = villagers_map.get(villager_name, {})
    gifts = villager_data.get("loved_gifts", [])
    return [{"name": name, "wiki_icon": format_wiki_filename(name)} for name in gifts]


def parse_social(player):
    """
    Parses friendship data from the <player> XML node.

    :param player: xml.etree.ElementTree Element representing <player>
    :return: list of villager dictionaries sorted descending by friendship points
    """
    start_time = time.perf_counter()

    if player is None:
        logger.warning("Player node is None. Returning empty friendship list.")
        return []

    friendships_list = []
    friendship_data = player.find("friendshipData")

    if friendship_data is None:
        logger.debug("No <friendshipData> node found under player XML")
        return []

    items = friendship_data.findall("item")
    logger.debug(
        f"Parsing <friendshipData> node containing {len(items)} raw villager entries"
    )

    villagers_meta = VILLAGERS_CATALOG.get("villagers", {})
    ignored_npcs = set(VILLAGERS_CATALOG.get("ignored_npcs", []))

    skipped_internal = 0

    for item in items:
        key = item.find("key/string")
        value = item.find("value/Friendship")

        if key is not None and value is not None and key.text:
            npc_name = key.text

            # Filter out system/internal names
            if (
                npc_name in ignored_npcs
                or npc_name.startswith("Henchman")
                or npc_name.startswith("Granter")
            ):
                skipped_internal += 1
                continue

            points_node = value.find("Points")
            talked_node = value.find("TalkedToToday")
            gifts_node = value.find("GiftsThisWeek")
            status_node = value.find("Status")

            points = (
                int(points_node.text)
                if points_node is not None and points_node.text
                else 0
            )
            talked = talked_node.text == "true" if talked_node is not None else False
            gifts_this_week = (
                int(gifts_node.text)
                if gifts_node is not None and gifts_node.text
                else 0
            )
            status_raw = status_node.text if status_node is not None else "Normal"

            hearts = points // 250

            # Check datable status from catalog
            is_datable = villagers_meta.get(npc_name, {}).get("datable", False)
            is_spouse = status_raw == "Married"
            is_dating = status_raw == "Dating"

            # Determine display status badge & accurate game max hearts
            if is_spouse:
                status_display = "Spouse"
                max_hearts = 14
            elif is_datable:
                status_display = "Datable"
                max_hearts = 10 if is_dating else 8
            else:
                status_display = "Normal"
                max_hearts = 10

            friendships_list.append(
                {
                    "name": npc_name,
                    "points": points,
                    "hearts": min(hearts, max_hearts),
                    "max_hearts": max_hearts,
                    "talked_today": talked,
                    "gifts_this_week": gifts_this_week,
                    "status": status_display,
                    "datable": is_datable,
                    "is_spouse": is_spouse,
                    "loved_gifts": get_loved_gifts(npc_name),
                }
            )

    if skipped_internal > 0:
        logger.debug(
            f"Skipped {skipped_internal} internal/system NPC friendship records"
        )

    # Sort list descending by friendship points (highest points first)
    friendships_list.sort(key=lambda x: x["points"], reverse=True)

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    logger.debug(
        f"Extracted {len(friendships_list)} villager friendship records in {elapsed_ms:.2f}ms"
    )

    return friendships_list
