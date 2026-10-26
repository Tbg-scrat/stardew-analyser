# src/core/reference_data.py
"""
Core item metadata lookup utility.
Builds an in-memory index dynamically over all JSON domain catalogs containing _meta blocks
and modular catalogs loaded via data_loader.
"""

import json
import logging
import os
import re
import time
from glob import glob

from data.data_loader import TOOLS_CATALOG, get_combined_objects_catalog

logger = logging.getLogger(__name__)

KNOWN_PREFIXES = ("O_", "T_", "BC_", "W_", "H_", "P_", "R_", "F_", "S_", "WP_", "FL_", "B_")
DATA_DIR = os.getenv("DATA_DIR", "data")


def qualify_item_id(raw_id: str, default_prefix: str = "O_") -> str:
    if not raw_id:
        return ""
    clean = str(raw_id).strip()
    while "(" in clean and ")" in clean:
        clean = re.sub(r"\([^)]*\)", "", clean).strip()
    if clean.startswith(KNOWN_PREFIXES):
        return clean
    return f"{default_prefix}{clean}"


_OBJECT_LOOKUP_CACHE = None


def get_tools_catalog() -> dict:
    return (
        TOOLS_CATALOG
        if isinstance(TOOLS_CATALOG, dict)
        else {"upgradeable_tools": {}, "special_tools": {}}
    )


def _get_object_lookup():
    global _OBJECT_LOOKUP_CACHE
    if _OBJECT_LOOKUP_CACHE is not None:
        return _OBJECT_LOOKUP_CACHE

    start_time = time.perf_counter()
    lookup = {}
    loaded_count = 0

    # 1. Process files containing _meta block configurations (Ground Truth for extracted sprites)
    json_files = glob(os.path.join(DATA_DIR, "*.json"))

    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict) or "_meta" not in data:
                continue

            meta = data["_meta"]
            prefix = meta.get("prefix", "O")

            items = data.get("items")
            if items is None:
                items = {k: v for k, v in data.items() if k != "_meta"}

            for item_key, item_data in items.items():
                item_key_str = str(item_key).strip()

                # 1.6 BigCraftables were extracted using SpriteIndex tiles (BC_283.png),
                # whereas 1.6 Objects use string ID files (O_DriedMushrooms.png).
                if (
                    prefix == "BC"
                    and isinstance(item_data, dict)
                    and item_data.get("SpriteIndex", -1) >= 0
                    and not item_key_str.isdigit()
                ):
                    sprite_target = str(item_data["SpriteIndex"])
                else:
                    sprite_target = (
                        item_key_str.replace(":", "_").replace("/", "_").replace(" ", "_")
                    )

                sprite_key = f"{prefix}_{sprite_target}"

                if isinstance(item_data, dict):
                    name = item_data.get("Name") or item_data.get("name") or "Unknown"
                    price = item_data.get("Price") or item_data.get("price") or 0
                else:
                    name = str(item_data)
                    price = 0

                info = {
                    "id": item_key_str,
                    "name": name,
                    "price": price,
                    "prefix": prefix,
                    "sprite_key": sprite_key,
                    "icon": f"/cache/img/{prefix}/{sprite_key}.png",
                }

                # Register strict namespaced and domain-prefixed routing keys
                lookup[f"({prefix}){item_key_str}"] = info
                lookup[f"{prefix}_{item_key_str}"] = info
                lookup[sprite_key] = info

                if item_key_str not in lookup:
                    lookup[item_key_str] = info

                if name and name != "Unknown" and name not in lookup:
                    lookup[name] = info

                loaded_count += 1

        except Exception as e:
            logger.warning(f"[ReferenceData] Failed to parse catalog {file_path}: {e}")

    # 2. Ingest modular non-_meta domain catalogs (boots, pants, shirts, cooking, etc.)
    for item in get_combined_objects_catalog():
        if not isinstance(item, dict):
            continue

        raw_item_id = str(item.get("id", "")).strip()
        if not raw_item_id:
            continue

        clean_item_id = re.sub(r"\([^)]*\)", "", raw_item_id).strip()

        name = item.get("name") or item.get("Name") or "Unknown"
        price = item.get("price") or item.get("Price") or 0

        # Determine domain prefix & bare ID
        if raw_item_id.startswith("B_") or clean_item_id.startswith("B_"):
            prefix = "B"
            bare_id = clean_item_id.replace("B_", "")
            icon = "/static/img/placeholder_boots.png"
            sprite_key = f"B_{bare_id}"
        elif raw_item_id.startswith("P_") or clean_item_id.startswith("P_"):
            prefix = "P"
            bare_id = clean_item_id.replace("P_", "")
            icon = "/static/img/placeholder_pants.png"
            sprite_key = f"P_{bare_id}"
        elif raw_item_id.startswith("S_") or clean_item_id.startswith("S_"):
            prefix = "S"
            bare_id = clean_item_id.replace("S_", "")
            icon = "/static/img/placeholder_shirts.png"
            sprite_key = f"S_{bare_id}"
        elif raw_item_id.startswith("W_") or clean_item_id.startswith("W_"):
            prefix = "W"
            bare_id = clean_item_id.replace("W_", "")
            sprite_key = f"W_{bare_id}"
            icon = f"/cache/img/W/{sprite_key}.png"
        elif raw_item_id.startswith("T_") or clean_item_id.startswith("T_"):
            prefix = "T"
            bare_id = clean_item_id.replace("T_", "")
            sprite_key = item.get("sprite_key", f"T_{bare_id}")
            icon = f"/cache/img/T/{sprite_key}.png"
        else:
            prefix = "O"
            bare_id = clean_item_id.replace("O_", "")
            sprite_key = f"O_{bare_id}"
            icon = f"/cache/img/O/{sprite_key}.png"

        lookup_key = f"({prefix}){bare_id}"

        # Do NOT overwrite ground-truth entries already indexed in Step 1
        if lookup_key in lookup:
            continue

        info = {
            "id": bare_id,
            "name": name,
            "price": price,
            "prefix": prefix,
            "sprite_key": sprite_key,
            "icon": icon,
        }

        lookup[lookup_key] = info
        lookup[f"{prefix}_{bare_id}"] = info
        if bare_id not in lookup:
            lookup[bare_id] = info
        if name and name != "Unknown" and name not in lookup:
            lookup[name] = info

        loaded_count += 1

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    _OBJECT_LOOKUP_CACHE = lookup
    logger.debug(
        f"Built strict namespaced object lookup cache with {len(lookup)} routing keys "
        f"({loaded_count} items indexed) in {elapsed_ms:.2f}ms"
    )
    return lookup


def get_object_info(harvest_id: str, fallback_name: str = None) -> dict:
    if not harvest_id or str(harvest_id).strip() in ("None", "-1", ""):
        if fallback_name:
            lookup = _get_object_lookup()
            clean_fallback = str(fallback_name).strip()
            if clean_fallback in lookup:
                return dict(lookup[clean_fallback])
            if clean_fallback.lower() in lookup:
                return dict(lookup[clean_fallback.lower()])

        return {
            "name": "Wild / Unknown",
            "icon": "/static/img/placeholder.svg",
            "price": 0,
        }

    lookup = _get_object_lookup()

    # If harvest_id is purely numeric (like a color-mask parentSheetIndex e.g. '123')
    # but we have a fallback name, prioritize checking the fallback name first to prevent numeric collisions.
    if str(harvest_id).strip().isdigit() and fallback_name:
        clean_fallback = str(fallback_name).strip()
        if clean_fallback in lookup:
            return dict(lookup[clean_fallback])
        if clean_fallback.lower() in lookup:
            return dict(lookup[clean_fallback.lower()])
        # Prioritize matching from the end of the name (e.g., "Wine" in "Ancient Fruit Wine")
        for word in reversed(clean_fallback.split()):
            if word in lookup:
                return dict(lookup[word])
            if word.capitalize() in lookup:
                return dict(lookup[word.capitalize()])

    raw_input = str(harvest_id).strip()

    if raw_input in lookup:
        return dict(lookup[raw_input])

    tag_mapping = {
        "(O)": "O_",
        "(W)": "W_",
        "(BC)": "BC_",
        "(T)": "T_",
        "(H)": "H_",
        "(P)": "P_",
        "(B)": "B_",
        "(R)": "O_",
        "(F)": "F_",
        "(S)": "S_",
        "(WP)": "WP_",
        "(FL)": "FL_",
    }

    for tag, catalog_prefix in tag_mapping.items():
        if tag in raw_input:
            bare_id = raw_input.replace(tag, "").strip()
            while "(" in bare_id and ")" in bare_id:
                bare_id = re.sub(r"\([^)]*\)", "", bare_id).strip()

            prefixed_key = f"{catalog_prefix}{bare_id}"
            if prefixed_key in lookup:
                return dict(lookup[prefixed_key])

    clean_key = raw_input
    while "(" in clean_key and ")" in clean_key:
        clean_key = re.sub(r"\([^)]*\)", "", clean_key).strip()

    if clean_key in lookup:
        return dict(lookup[clean_key])

    if clean_key.lower() in lookup:
        return dict(lookup[clean_key.lower()])

    for prefix in KNOWN_PREFIXES:
        if clean_key.startswith(prefix):
            bare_id = clean_key[len(prefix) :]
            if bare_id in lookup:
                return dict(lookup[bare_id])

    if fallback_name:
        clean_fallback = str(fallback_name).strip()
        if clean_fallback in lookup:
            return dict(lookup[clean_fallback])

    # STRICT ERROR POLICY: Do not silently guess domain prefixes for un-prefixed identifiers.
    logger.error(
        f"[ReferenceData] Configuration/Source Error: Unqualified or unrecognized item ID '{harvest_id}' received without valid domain prefix."
    )

    formatted_name = fallback_name if fallback_name else clean_key.replace("_", " ")
    return {
        "id": clean_key,
        "name": formatted_name,
        "price": 0,
        "prefix": "items",
        "icon": "/static/img/placeholder.svg",
        "sprite_key": clean_key,
    }
