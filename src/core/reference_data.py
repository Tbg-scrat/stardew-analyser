# src/core/reference_data.py
"""
Core item metadata lookup utility.
Builds an in-memory index over OBJECTS_CATALOG for fast item detail lookups.
"""

import logging
import time

from data.data_loader import OBJECTS_CATALOG, TOOLS_CATALOG

logger = logging.getLogger(__name__)

_OBJECT_LOOKUP_CACHE = None


def get_tools_catalog() -> dict:
    """Returns the static tools catalog loaded via data_loader."""
    return (
        TOOLS_CATALOG
        if isinstance(TOOLS_CATALOG, dict)
        else {"upgradeable_tools": {}, "special_tools": {}}
    )


def _get_object_lookup():
    """Builds an in-memory index mapping string IDs, (O)IDs, and string names to object metadata."""
    global _OBJECT_LOOKUP_CACHE
    if _OBJECT_LOOKUP_CACHE is not None:
        return _OBJECT_LOOKUP_CACHE

    start_time = time.perf_counter()
    lookup = {}
    catalog = OBJECTS_CATALOG if isinstance(OBJECTS_CATALOG, list) else []

    logger.debug(
        f"Initializing object lookup cache from catalog ({len(catalog)} raw items)"
    )

    skipped_count = 0
    for item in catalog:
        if not isinstance(item, dict):
            skipped_count += 1
            continue

        item_id = str(item.get("id", ""))
        names = item.get("names", {})
        name = (
            names.get("data-en-US")
            or names.get("en-US")
            or item.get("name")
            or "Unknown"
        )
        price = item.get("price", 0)

        clean_name = name.replace(" ", "_").replace("'", "")
        wiki_filename = name.replace(" ", "_")

        if item_id:
            primary_icon = f"/static/img/items/O_{item_id}.png"
        else:
            primary_icon = f"/static/img/items/O_{clean_name}.png"

        info = {
            "id": item_id,
            "name": name,
            "price": price,
            "icon": primary_icon,
            "wiki_icon": f"https://stardewvalleywiki.com/Special:Redirect/file/{wiki_filename}.png",
        }

        if item_id:
            lookup[item_id] = info
            lookup[f"(O){item_id}"] = info

        if name:
            lookup[name] = info
            lookup[name.lower()] = info

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    _OBJECT_LOOKUP_CACHE = lookup
    logger.debug(
        f"Built object lookup cache with {len(lookup)} total index keys "
        f"({skipped_count} invalid items skipped) in {elapsed_ms:.2f}ms"
    )
    return lookup


def get_object_info(harvest_id: str) -> dict:
    """
    Look up item metadata (display name, sprite icon, base price)
    by numeric ID ("412"), qualified ID ("(O)412"), or 1.6 string key ("Powdermelon").
    """
    if not harvest_id or str(harvest_id).strip() in ("None", "-1", ""):
        logger.debug(
            f"Blank/invalid harvest_id '{harvest_id}' passed to get_object_info; returning Wild/Unknown default"
        )
        return {
            "name": "Wild / Unknown",
            "icon": "/static/img/items/placeholder.png",
            "wiki_icon": "https://stardewvalleywiki.com/Special:Redirect/file/Tile.png",
            "price": 0,
        }

    raw_key = str(harvest_id).replace("(O)", "").strip()
    lookup = _get_object_lookup()

    if raw_key in lookup:
        logger.debug(
            f"Direct catalog match for item key '{harvest_id}' -> Name: '{lookup[raw_key]['name']}'"
        )
        return dict(lookup[raw_key])

    if raw_key.lower() in lookup:
        logger.debug(
            f"Lowercase catalog match for item key '{harvest_id}' -> Name: '{lookup[raw_key.lower()]['name']}'"
        )
        return dict(lookup[raw_key.lower()])

    formatted_name = raw_key.replace("_", " ")
    logger.debug(
        f"Catalog miss for item key '{harvest_id}'. Falling back to formatted key '{formatted_name}'"
    )
    return {
        "id": raw_key,
        "name": formatted_name,
        "price": 0,
        "icon": f"/static/img/items/O_{raw_key}.png",
        "wiki_icon": f"https://stardewvalleywiki.com/Special:Redirect/file/{raw_key}.png",
    }
