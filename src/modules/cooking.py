# src/modules/cooking.py
# -*- coding: utf-8 -*-

import logging
import time
from data.data_loader import COOKING_CATALOG

logger = logging.getLogger(__name__)


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
        logger.warning("Player node is None. Returning empty cooking counts.")
        return {}

    cooked_counts = {}
    recipes_cooked_node = player.find("recipesCooked")
    if recipes_cooked_node is None:
        recipes_cooked_node = player.find(".//recipesCooked")

    if recipes_cooked_node is None:
        logger.debug("No <recipesCooked> node found under player XML")
        return {}

    raw_entries = recipes_cooked_node.findall("item")
    logger.debug(f"Found <recipesCooked> node with {len(raw_entries)} raw recipe item entries")

    for item in raw_entries:
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
                    logger.debug(f"Invalid non-integer count '{val_text}' for recipe '{raw_key}'; defaulting to 0")
                    count = 0

            if raw_key:
                cooked_counts[raw_key] = count

    logger.debug(f"Extracted {len(cooked_counts)} valid cooked recipe entries from player XML")
    return cooked_counts


def get_formatted_cooking(player, catalog=None):
    """
    Parses cooking save data and merges it against COOKING_CATALOG,
    returning a sorted list of cooking recipe dictionaries ready for the UI.
    """
    start_time = time.perf_counter()
    if catalog is None:
        logger.debug("Using default COOKING_CATALOG")
        catalog = COOKING_CATALOG

    raw_cooking = parse_cooking(player)
    cooking_save_map = {str(k).replace("(O)", ""): v for k, v in raw_cooking.items()}

    cooking_mapped = []
    catalog_items = catalog.items() if isinstance(catalog, dict) else []

    unmapped_count = 0
    for item_id, catalog_item in catalog_items:
        if not isinstance(catalog_item, dict):
            unmapped_count += 1
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

    if unmapped_count > 0:
        logger.debug(f"Skipped {unmapped_count} invalid non-dict entries in cooking catalog")

    cooked_total = sum(1 for c in cooking_mapped if c["is_unlocked"])
    catalog_total = len(cooking_mapped)
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    logger.debug(
        f"Cooking progress: {cooked_total}/{catalog_total} recipes cooked "
        f"(Parsed in {elapsed_ms:.2f}ms)"
    )

    return sorted(cooking_mapped, key=lambda x: x["name"])
    