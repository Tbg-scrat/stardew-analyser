#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for parsing player achievement data from Stardew Valley save files.
"""

def parse_achievements(player_elem, catalog):
    """
    Parses unlocked achievement IDs from the player XML element and merges
    them with the master achievement catalog.

    :param player_elem: ElementTree Element representing <player>
    :param catalog: List of achievement dicts loaded from data/achievements.json
    :return: Dict containing achievement progress metrics and item details
    """
    # 1. Collect unlocked achievement IDs from <player><achievements>
    unlocked_ids = set()
    achievements_node = player_elem.find("achievements")
    
    if achievements_node is not None:
        for int_elem in achievements_node.findall("int"):
            try:
                unlocked_ids.add(int(int_elem.text))
            except (ValueError, TypeError):
                continue

    # 2. Process each catalog entry
    processed_achievements = []
    unlocked_count = 0

    for item in catalog:
        ach_id = item["id"]
        is_unlocked = ach_id in unlocked_ids
        
        if is_unlocked:
            unlocked_count += 1

        processed_achievements.append({
            "id": ach_id,
            "key": item["key"],
            "name": item["name"],
            "description": item["description"],
            "category": item["category"],
            "icon": item["icon"],
            "target": item["target"],
            "tip": item["tip"],
            "unlocked": is_unlocked
        })

    total_count = len(catalog)
    percentage = round((unlocked_count / total_count * 100), 1) if total_count > 0 else 0.0


    return {
       "unlocked_count": unlocked_count,
       "total_count": total_count,
       "percentage": percentage,
       "list": processed_achievements  # Renamed from 'items'
    }
