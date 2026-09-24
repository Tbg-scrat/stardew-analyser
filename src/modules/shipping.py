# src/modules/shipping.py

import logging
from src.core.xml_reader import get_key_value
from data.data_loader import SHIPPING_CATALOG

logger = logging.getLogger(__name__)


def format_wiki_filename(name):
    """Clean item names into Stardew Valley Wiki image file conventions."""
    if not name:
        return ""
    return name.replace(" ", "_").replace("'", "%27")


def parse_shipping(player_node):
    """Extract basicShipped item counts from the player XML node."""
    if player_node is None:
        logger.warning("Player node is None. Returning empty basicShipped dictionary.")
        return {}

    shipped_items = {}
    basic_shipped = player_node.find("basicShipped")
    if basic_shipped is not None:
        for item in basic_shipped.findall("item"):
            item_id, val_node = get_key_value(item)
            if item_id and val_node is not None:
                count = val_node.findtext("int", "0")
                try:
                    count_int = int(count)
                except ValueError:
                    count_int = 0
                shipped_items[str(item_id)] = count_int

    logger.debug(f"Extracted {len(shipped_items)} shipped items from basicShipped XML")
    return shipped_items


def get_formatted_shipping(player_node, catalog=None):
    """
    Parses shipping save data and merges it against SHIPPING_CATALOG,
    returning a sorted list of shipping item dictionaries ready for the UI.
    """
    if catalog is None:
        logger.debug("Using default SHIPPING_CATALOG")
        catalog = SHIPPING_CATALOG

    raw_shipped = parse_shipping(player_node)
    shipped_save_map = {str(k).replace("(O)", ""): v for k, v in raw_shipped.items()}

    shipped_mapped = []
    catalog_items = catalog.items() if isinstance(catalog, dict) else []

    for item_id, catalog_item in catalog_items:
        if not isinstance(catalog_item, dict):
            continue

        count = shipped_save_map.get(str(item_id), 0)
        is_shipped = count > 0

        item_name = catalog_item.get("name", f"Item {item_id}")

        shipped_mapped.append({
            "id": item_id,
            "name": item_name,
            "count": count,
            "status": "shipped" if is_shipped else "not_shipped",
            "is_unlocked": is_shipped,
            "achievement_required": catalog_item.get("achievement_required", False),
            "is_polyculture": catalog_item.get("is_polyculture", False),
            "is_monoculture": catalog_item.get("is_monoculture", False),
            "image": catalog_item.get("image", ""),
            "wiki_icon": format_wiki_filename(item_name),
        })

    shipped_total = sum(1 for s in shipped_mapped if s["is_unlocked"])
    catalog_total = len(shipped_mapped)
    logger.debug(f"Shipping progress: {shipped_total}/{catalog_total} items shipped")

    return sorted(shipped_mapped, key=lambda x: x["name"])
    