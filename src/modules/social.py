# src/modules/social.py
# -*- coding: utf-8 -*-
"""
Social module for Stardew Valley save file parsing.
Extracts villager friendships, heart levels, daily interaction statuses, loved gift preferences,
and handles sorting by friendship points and marital status.
"""

import logging
from src.core.gift_data import get_loved_gifts

logger = logging.getLogger(__name__)

DATABLE_VILLAGERS = {
    "Abigail", "Alex", "Elliott", "Emily", "Haley", "Harvey",
    "Leah", "Maru", "Penny", "Sam", "Sebastian", "Shane"
}


def parse_social(player):
    """
    Parses friendship data from the <player> XML node.

    :param player: xml.etree.ElementTree Element representing <player>
    :return: list of villager dictionaries sorted descending by friendship points
    """
    if player is None:
        logger.warning("Player node is None. Returning empty friendship list.")
        return []

    friendships_list = []
    friendship_data = player.find("friendshipData")

    if friendship_data is not None:
        for item in friendship_data.findall("item"):
            key = item.find("key/string")
            value = item.find("value/Friendship")

            if key is not None and value is not None and key.text:
                npc_name = key.text
                
                # Filter out system/internal names
                if npc_name.startswith("Henchman") or npc_name.startswith("Granter"):
                    continue

                points_node = value.find("Points")
                talked_node = value.find("TalkedToToday")
                gifts_node = value.find("GiftsThisWeek")
                status_node = value.find("Status")

                points = int(points_node.text) if points_node is not None and points_node.text else 0
                talked = talked_node.text == "true" if talked_node is not None else False
                gifts_this_week = int(gifts_node.text) if gifts_node is not None and gifts_node.text else 0
                status_raw = status_node.text if status_node is not None else "Normal"

                hearts = points // 250
                is_datable = npc_name in DATABLE_VILLAGERS
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

                friendships_list.append({
                    "name": npc_name,
                    "points": points,
                    "hearts": min(hearts, max_hearts),
                    "max_hearts": max_hearts,
                    "talked_today": talked,
                    "gifts_this_week": gifts_this_week,
                    "status": status_display,
                    "datable": is_datable,
                    "is_spouse": is_spouse,
                    "loved_gifts": get_loved_gifts(npc_name)
                })

    logger.debug(f"Extracted {len(friendships_list)} villager friendship records")

    # Sort list descending by friendship points (highest points first)
    friendships_list.sort(key=lambda x: x["points"], reverse=True)
    
    return friendships_list
    