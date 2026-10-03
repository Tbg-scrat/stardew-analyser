# src/modules/fishing.py

import logging
import time
from src.core.xml_reader import get_key_value
from data.data_loader import FISH_CATALOG

logger = logging.getLogger(__name__)


def format_wiki_filename(name):
    """Clean item names into Stardew Valley Wiki image file conventions."""
    if not name:
        return ""
    return name.replace(" ", "_").replace("'", "%27")


def parse_fishing(player_node):
    """Extract fishCaught records with quantity and max length."""
    if player_node is None:
        logger.warning("Player node is None. Returning empty fishCaught record.")
        return {}

    fish_caught = {}
    fish_node = player_node.find("fishCaught")
    if fish_node is None:
        logger.debug("No <fishCaught> node found under player XML")
        return {}

    items = fish_node.findall("item")
    logger.debug(f"Parsing <fishCaught> node containing {len(items)} raw fish item entries")

    for item in items:
        item_id, val_node = get_key_value(item)
        if item_id and val_node is not None:
            count, length = 0, 0

            array_node = val_node.find("ArrayOfInt")
            if array_node is None:
                array_node = val_node.find("ArrayOfint")

            if array_node is not None:
                ints = array_node.findall("int")
                if len(ints) > 0 and ints[0].text:
                    try:
                        count = int(ints[0].text)
                    except ValueError:
                        logger.debug(f"Invalid count text '{ints[0].text}' for fish '{item_id}'; defaulting to 0")
                        count = 0
                if len(ints) > 1 and ints[1].text:
                    try:
                        length = int(ints[1].text)
                    except ValueError:
                        logger.debug(f"Invalid length text '{ints[1].text}' for fish '{item_id}'; defaulting to 0")
                        length = 0
            else:
                int_val = val_node.findtext("int")
                if int_val:
                    try:
                        count = int(int_val)
                    except ValueError:
                        logger.debug(f"Invalid single int_val '{int_val}' for fish '{item_id}'; defaulting to 0")
                        count = 0

            fish_caught[str(item_id)] = {"count": count, "length": length}

    logger.debug(f"Extracted {len(fish_caught)} caught fish entries from player XML")
    return fish_caught


def get_formatted_fishing(player_node, catalog=None):
    """
    Parses fishing save data and merges it against FISH_CATALOG,
    returning a sorted list of fish item dictionaries ready for the UI.
    """
    start_time = time.perf_counter()
    if catalog is None:
        logger.debug("Using default FISH_CATALOG")
        catalog = FISH_CATALOG

    raw_fish = parse_fishing(player_node)
    fish_save_map = {str(k).replace("(O)", ""): v for k, v in raw_fish.items()}

    fish_mapped = []
    catalog_items = catalog.items() if isinstance(catalog, dict) else []

    unmapped_count = 0
    for item_id, catalog_item in catalog_items:
        if not isinstance(catalog_item, dict):
            unmapped_count += 1
            continue

        stats = fish_save_map.get(str(item_id))
        is_caught = stats is not None
        item_name = catalog_item.get("name", f"Fish {item_id}")

        fish_mapped.append({
            "id": item_id,
            "name": item_name,
            "count": stats["count"] if is_caught else 0,
            "length": stats["length"] if is_caught else 0,
            "status": "caught" if is_caught else "not_caught",
            "is_unlocked": is_caught,
            "image": catalog_item.get("image", ""),
            "wiki_icon": format_wiki_filename(item_name),
        })

    if unmapped_count > 0:
        logger.debug(f"Skipped {unmapped_count} invalid non-dict entries in fish catalog")

    caught_total = sum(1 for f in fish_mapped if f["is_unlocked"])
    catalog_total = len(fish_mapped)
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    logger.debug(
        f"Fishing progress: {caught_total}/{catalog_total} fish species caught "
        f"(Parsed in {elapsed_ms:.2f}ms)"
    )

    return sorted(fish_mapped, key=lambda x: x["name"])
    