# src/core/reference_data.py
"""
Core item metadata lookup utility.
Builds an in-memory index over domain catalogs for fast item detail lookups.
"""

import logging
import time
import re

from data.data_loader import TOOLS_CATALOG, get_combined_objects_catalog

logger = logging.getLogger(__name__)

KNOWN_PREFIXES = ("O_", "T_", "BC_", "W_", "H_", "P_", "R_", "F_", "S_")


def qualify_item_id(raw_id: str, default_prefix: str = "O_") -> str:
    """Normalizes raw save IDs or bare numeric strings to catalog keys (e.g. "128" -> "O_128")."""
    if not raw_id:
        return ""
    clean = str(raw_id).strip()
    while "(" in clean and ")" in clean:
        clean = re.sub(r'\([^)]*\)', '', clean).strip()
    if clean.startswith(KNOWN_PREFIXES):
        return clean
    return f"{default_prefix}{clean}"


_OBJECT_LOOKUP_CACHE = None


def get_tools_catalog() -> dict:
    """Returns the static tools catalog loaded via data_loader."""
    return (
        TOOLS_CATALOG
        if isinstance(TOOLS_CATALOG, dict)
        else {"upgradeable_tools": {}, "special_tools": {}}
    )


def _get_object_lookup():
    """Builds an in-memory index mapping string IDs, qualified IDs, and string names to object metadata."""
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
            or item.get("Name")
            or names.get("data-en-US")
            or names.get("en-US")
            or "Unknown"
        )
        price = item.get("price", item.get("SalePrice", 0))

        clean_name = name.replace(" ", "_").replace("'", "")

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
            "sprite_key": item.get("sprite_key"),
        }

        if item_id:
            # Store exact qualified primary ID (e.g., H_17, BC_37, W_64)
            lookup[item_id] = info

            # Map explicit parenthesis tags strictly to their prefixed catalog keys
            for tag, prefix in [
                ("(O)", "O_"), ("(W)", "W_"), ("(BC)", "BC_"), 
                ("(T)", "T_"), ("(H)", "H_"), ("(P)", "P_"), 
                ("(R)", "R_"), ("(F)", "F_"), ("(S)", "S_")
            ]:
                if item_id.startswith(prefix):
                    bare_id = item_id[len(prefix):]
                    # Store with explicit prefix tag so (H)17 checks H_17 directly
                    lookup[f"{tag}{bare_id}"] = info

            if not item_id.startswith(KNOWN_PREFIXES):
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
    Look up item metadata ensuring strict category prefix separation (H_, BC_, W_, etc.).
    """
    if not harvest_id or str(harvest_id).strip() in ("None", "-1", ""):
        return {
            "name": "Wild / Unknown",
            "icon": "/static/img/placeholder.svg",
            "price": 0,
        }

    raw_input = str(harvest_id).strip()
    lookup = _get_object_lookup()

    # 1. Direct exact match in lookup (e.g., "(H)17", "(BC)37", "BC_37", "H_17")
    if raw_input in lookup:
        return dict(lookup[raw_input])

    # 2. Convert parenthesis notation directly to catalog prefix format (e.g. "(H)17" -> "H_17")
    tag_mapping = {
        "(O)": "O_",
        "(W)": "W_",
        "(BC)": "BC_",
        "(T)": "T_",
        "(H)": "H_",
        "(P)": "P_",
        "(R)": "R_",
        "(F)": "F_",
        "(S)": "S_"
    }

    for tag, catalog_prefix in tag_mapping.items():
        if tag in raw_input:
            bare_id = raw_input.replace(tag, "").strip()
            while "(" in bare_id and ")" in bare_id:
                bare_id = re.sub(r'\([^)]*\)', '', bare_id).strip()
            
            prefixed_key = f"{catalog_prefix}{bare_id}"
            if prefixed_key in lookup:
                return dict(lookup[prefixed_key])

    # 3. Clean fallback search
    clean_key = raw_input
    while "(" in clean_key and ")" in clean_key:
        clean_key = re.sub(r'\([^)]*\)', '', clean_key).strip()

    if clean_key in lookup:
        return dict(lookup[clean_key])

    formatted_name = fallback_name if fallback_name else clean_key.replace("_", " ")
    icon_filename = clean_key if clean_key.startswith(KNOWN_PREFIXES) else f"O_{clean_key}"

    return {
        "id": clean_key,
        "name": formatted_name,
        "price": 0,
        "icon": f"/cache/img/items/{icon_filename}.png",
    }
    