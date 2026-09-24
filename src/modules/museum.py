# src/modules/museum.py

import logging
from data.data_loader import MUSEUM_CATALOG

logger = logging.getLogger(__name__)


def format_wiki_filename(name):
    """Clean item names into Stardew Valley Wiki image file conventions."""
    if not name:
        return ""
    return name.replace(" ", "_").replace("'", "%27")


def parse_museum(root_node):
    """Extract LibraryMuseum donated pieces."""
    if root_node is None:
        logger.warning("SaveGame root_node is None. Returning empty museum collection.")
        return []

    museum_pieces = {}
    locations = root_node.find("locations")
    if locations is not None:
        for loc in locations.findall("GameLocation"):
            museum_node = loc.find("museumPieces")
            if museum_node is not None:
                for item in museum_node.findall("item"):
                    val_node = item.find("value")
                    if val_node is not None:
                        item_id = val_node.findtext("string") or val_node.findtext("int")
                        if item_id:
                            museum_pieces[str(item_id)] = True

    donated_list = list(museum_pieces.keys())
    logger.debug(f"Extracted {len(donated_list)} donated pieces from LibraryMuseum XML")
    return donated_list


def get_formatted_museum(root_node, catalog=None):
    """
    Parses museum save data and merges it against MUSEUM_CATALOG,
    returning a sorted list of museum piece dictionaries ready for the UI.
    """
    if catalog is None:
        logger.debug("Using default MUSEUM_CATALOG")
        catalog = MUSEUM_CATALOG

    raw_museum = parse_museum(root_node)
    donated_set = {str(item_id).replace("(O)", "") for item_id in raw_museum}

    museum_mapped = []
    catalog_items = catalog.items() if isinstance(catalog, dict) else []

    for item_id, catalog_item in catalog_items:
        if not isinstance(catalog_item, dict):
            continue

        is_donated = str(item_id) in donated_set
        item_name = catalog_item.get("name", f"Artifact/Mineral {item_id}")

        museum_mapped.append({
            "id": item_id,
            "name": item_name,
            "type": catalog_item.get("type", "Artifact"),
            "status": "found" if is_donated else "not_found",
            "is_unlocked": is_donated,
            "image": catalog_item.get("image", ""),
            "wiki_icon": format_wiki_filename(item_name),
        })

    donated_total = sum(1 for m in museum_mapped if m["is_unlocked"])
    catalog_total = len(museum_mapped)
    logger.debug(f"Museum progress: {donated_total}/{catalog_total} items donated")

    return sorted(museum_mapped, key=lambda x: x["name"])
    