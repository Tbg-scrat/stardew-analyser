# src/core/reference_data.py
"""
Core item metadata lookup utility.
Builds an in-memory index over domain catalogs for fast item detail lookups.
"""

import logging
import time

from data.data_loader import TOOLS_CATALOG, get_combined_objects_catalog

logger = logging.getLogger(__name__)

KNOWN_PREFIXES = ("O_", "T_", "BC_", "W_", "H_", "B_", "F_")


def qualify_item_id(raw_id: str, default_prefix: str = "O_") -> str:
    """Normalizes raw save IDs or bare numeric strings to catalog keys (e.g. "128" -> "O_128")."""
    if not raw_id:
        return ""
    clean = str(raw_id).replace("(O)", "").strip()
    if clean.startswith(KNOWN_PREFIXES):
        return clean
    return f"{default_prefix}{clean}"


_OBJECT_LOOKUP_CACHE = None

KNOWN_PREFIXES = ("O_", "T_", "BC_", "W_", "H_", "B_", "F_")


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
    catalog = get_combined_objects_catalog()

    logger.debug(
        f"Initializing object lookup cache from catalog ({len(catalog)} raw items)"
    )

    skipped_count = 0
    for item in catalog:
        if not isinstance(item, dict):
            skipped_count += 1
            continue

        item_id = str(item.get("id", "")).strip()
        names = item.get("names", {})
        
        name = (
            item.get("name")
            or names.get("data-en-US")
            or names.get("en-US")
            or "Unknown"
        )
        price = item.get("price", 0)

        clean_name = name.replace(" ", "_").replace("'", "")
        wiki_filename = name.replace(" ", "_")

        # Resolve icon path dynamically without duplicating prefixes
        if item_id:
            if item_id.startswith(KNOWN_PREFIXES):
                primary_icon = f"/cache/img/items/{item_id}.png"
            else:
                primary_icon = f"/cache/img/items/O_{item_id}.png"
        else:
            primary_icon = f"/cache/img/items/O_{clean_name}.png"

        info = {
            "id": item_id,
            "name": name,
            "price": price,
            "icon": primary_icon,
            "wiki_icon": f"https://stardewvalleywiki.com/Special:Redirect/file/{wiki_filename}.png",
        }

        if item_id:
            # Primary lookup under qualified ID (e.g., "O_128")
            lookup[item_id] = info

            # Aliases for backward compatibility with bare numeric IDs ("128", "(O)128")
            if item_id.startswith("O_"):
                bare_id = item_id[2:]
                lookup[bare_id] = info
                lookup[f"(O){bare_id}"] = info
            elif not item_id.startswith(KNOWN_PREFIXES):
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


def get_object_info(harvest_id: str, fallback_name: str = None) -> dict:
    """
    Look up item metadata (display name, sprite icon, base price)
    by qualified ID ("O_128"), numeric ID ("128"), qualified save ID ("(O)128"),
    or 1.6 string key ("Powdermelon").
    """
    if not harvest_id or str(harvest_id).strip() in ("None", "-1", ""):
        logger.debug(
            f"Blank/invalid harvest_id '{harvest_id}' passed to get_object_info; returning Wild/Unknown default"
        )
        return {
            "name": "Wild / Unknown",
            "icon": "/cache/img/items/placeholder.png",
            "wiki_icon": "https://stardewvalleywiki.com/Special:Redirect/file/Tile.png",
            "price": 0,
        }

    raw_key = str(harvest_id).replace("(O)", "").strip()
    lookup = _get_object_lookup()

    # Direct key hit
    if raw_key in lookup:
        return dict(lookup[raw_key])

    # Try prepending O_ if an unqualified ID was passed
    prefixed_key = f"O_{raw_key}"
    if prefixed_key in lookup:
        return dict(lookup[prefixed_key])

    # Lowercase match fallback
    if raw_key.lower() in lookup:
        return dict(lookup[raw_key.lower()])

    formatted_name = fallback_name if fallback_name else raw_key.replace("_", " ")
    icon_filename = raw_key if raw_key.startswith(KNOWN_PREFIXES) else f"O_{raw_key}"

    logger.debug(
        f"Catalog miss for item key '{harvest_id}'. Falling back to formatted key '{formatted_name}'"
    )
    return {
        "id": raw_key,
        "name": formatted_name,
        "price": 0,
        "icon": f"/cache/img/items/{icon_filename}.png",
        "wiki_icon": f"https://stardewvalleywiki.com/Special:Redirect/file/{raw_key}.png",
    }