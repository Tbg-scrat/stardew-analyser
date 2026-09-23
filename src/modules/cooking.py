# -*- coding: utf-8 -*-
"""
Cooking module for Stardew Valley save file parsing.
Extracts cooked recipe counts keyed by item ID string from <recipesCooked>
and formats catalog data for UI rendering.
"""

from data.data_loader import COOKING_CATALOG


def format_wiki_filename(name):
    """Clean item names into Stardew Valley Wiki image file conventions."""
    if not name:
        return ""
    return name.replace(" ", "_").replace("'", "%27")


def parse_cooking(player):
    """
    Parses <recipesCooked> from the player node or any sub-tree.

    :param player: xml.etree.ElementTree Element representing <player>
    :return: dict mapping item IDs (e.g. "194", "253") to cooked counts
    """
    if player is None:
        return {}

    cooked_counts = {}

    recipes_cooked_node = player.find("recipesCooked") or player.find(".//recipesCooked")

    if recipes_cooked_node is not None:
        for item in recipes_cooked_node.findall("item"):
            key_node = item.find("key")
            val_node = item.find("value")

            if key_node is not None:
                raw_key = "".join(key_node.itertext()).strip().replace("(O)", "")

                count = 0
                if val_node is not None:
                    val_text = "".join(val_node.itertext()).strip()
                    try:
                        count = int(val_text)
                    except ValueError:
                        count = 0

                if raw_key:
                    cooked_counts[raw_key] = count

    return cooked_counts


def get_formatted_cooking(player, catalog=None):
    """
    Parses cooking save data and merges it against COOKING_CATALOG,
    returning a sorted list of cooking recipe dictionaries ready for the UI.
    """
    if catalog is None:
        catalog = COOKING_CATALOG

    raw_cooking = parse_cooking(player)
    cooking_save_map = {str(k).replace("(O)", ""): v for k, v in raw_cooking.items()}

    cooking_mapped = []
    catalog_items = catalog.items() if isinstance(catalog, dict) else []

    for item_id, catalog_item in catalog_items:
        if not isinstance(catalog_item, dict):
            continue

        count = cooking_save_map.get(str(item_id), 0)
        is_cooked = count > 0
        item_name = catalog_item.get("name", f"Recipe {item_id}")

        cooking_mapped.append(
            {
                "id": item_id,
                "name": item_name,
                "count": count,
                "status": "cooked" if is_cooked else "not_cooked",
                "is_unlocked": is_cooked,
                "image": catalog_item.get("image", ""),
                "wiki_icon": catalog_item.get(
                    "wiki_icon", format_wiki_filename(item_name)
                ),
            }
        )

    return sorted(cooking_mapped, key=lambda x: x["name"])
    