# -*- coding: utf-8 -*-
"""
Social module for Stardew Valley save file parsing.
Extracts villager friendships, heart levels, daily interaction statuses, and loved gift preferences.
"""

from src.core.gift_data import get_loved_gifts

DATABLE_VILLAGERS = {
    "Abigail", "Alex", "Elliott", "Emily", "Haley", "Harvey",
    "Leah", "Maru", "Penny", "Sam", "Sebastian", "Shane"
}

def parse_social(player):
    """
    Parses friendship data from the <player> XML node.

    :param player: xml.etree.ElementTree Element representing <player>
    :return: dict of villagers mapped to heart levels, points, talked status, and loved gifts
    """
    if player is None:
        return {}

    friendships = {}
    friendship_data = player.find("friendshipData")

    if friendship_data is not None:
        for item in friendship_data.findall("item"):
            key = item.find("key/string")
            value = item.find("value/Friendship")

            if key is not None and value is not None and key.text:
                npc_name = key.text
                
                # Filter out system/internal names if necessary
                if npc_name.startswith("Henchman") or npc_name.startswith("Granter"):
                    continue

                points_node = value.find("Points")
                talked_node = value.find("TalkedToToday")
                gifts_node = value.find("GiftsThisWeek")
                status_node = value.find("Status")

                points = int(points_node.text) if points_node is not None and points_node.text else 0
                talked = talked_node.text == "true" if talked_node is not None else False
                gifts_this_week = int(gifts_node.text) if gifts_node is not None and gifts_node.text else 0
                status = status_node.text if status_node is not None else "Normal"

                hearts = points // 250
                is_datable = npc_name in DATABLE_VILLAGERS
                max_hearts = 10 if is_datable else 10

                friendships[npc_name] = {
                    "points": points,
                    "hearts": min(hearts, 14), # Cap at max conceivable
                    "max_hearts": max_hearts,
                    "talked_today": talked,
                    "gifts_this_week": gifts_this_week,
                    "status": "Datable" if is_datable else status,
                    "loved_gifts": get_loved_gifts(npc_name)
                }

    # Sort dictionary alphabetically by NPC name
    return dict(sorted(friendships.items()))
