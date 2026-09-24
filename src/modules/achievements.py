# src/modules/achievements.py

import logging
from data.data_loader import ACHIEVEMENTS_CATALOG

logger = logging.getLogger(__name__)


def parse_achievements(player_node, catalog=None, shipped_items=None):
    """
    Parses unlocked achievements from player XML, merges with catalog metadata,
    and calculates progress for special achievements like Monoculture.
    """
    achievements_catalog = catalog if catalog is not None else ACHIEVEMENTS_CATALOG
    if catalog is None:
        logger.debug("Using default ACHIEVEMENTS_CATALOG")

    unlocked_ids = set()
    achievements_node = player_node.find("achievements")
    
    if achievements_node is None:
        logger.warning("No <achievements> node found in player data.")
    else:
        for node in achievements_node.findall("int"):
            if node.text and node.text.isdigit():
                unlocked_ids.add(int(node.text))
            elif node.text:
                logger.warning(f"Ignored non-integer achievement ID: '{node.text}'")

    logger.debug(f"Extracted {len(unlocked_ids)} unlocked achievement IDs from XML")

    monoculture_count = 0
    if shipped_items:
        monoculture_items = [item for item in shipped_items if item.get("is_monoculture")]
        monoculture_count = (
            max([item.get("count", 0) for item in monoculture_items], default=0)
            if monoculture_items
            else 0
        )
        logger.debug(f"Monoculture calculated max single crop shipped: {monoculture_count}/300")

    processed_achievements = []
    
    for catalog_item in achievements_catalog:
        item_id = catalog_item.get("id")
        is_unlocked = item_id in unlocked_ids
        name = catalog_item.get("name")

        item_dict = {
            "id": item_id,
            "name": name,
            "description": catalog_item.get("description"),
            "category": catalog_item.get("category"),
            "icon": catalog_item.get("icon"),
            "target": catalog_item.get("target"),
            "tip": catalog_item.get("tip"),
            "unlocked": is_unlocked,
            "link_module": catalog_item.get("link_module"),
            "link_filter": catalog_item.get("link_filter")
        }

        if name == "Monoculture":
            override_unlock = is_unlocked or (monoculture_count >= 300)
            if override_unlock and not is_unlocked:
                logger.debug("Monoculture achievement marked unlocked based on shipped items threshold")
            item_dict["progress_current"] = min(monoculture_count, 300)
            item_dict["target"] = 300
            item_dict["unlocked"] = override_unlock
            item_dict["link_module"] = None
            item_dict["link_filter"] = None

        processed_achievements.append(item_dict)

    total_count = len(processed_achievements)
    unlocked_count = sum(1 for a in processed_achievements if a["unlocked"])
    pct = round((unlocked_count / total_count * 100), 1) if total_count > 0 else 0

    logger.debug(f"Achievements summary: {unlocked_count}/{total_count} unlocked ({pct}%)")

    return {
        "list": processed_achievements,
        "total": total_count,
        "unlocked_count": unlocked_count,
        "percent": pct
    }
    