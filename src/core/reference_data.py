# src/core/reference_data.py
"""
Core item metadata lookup utility.
Builds an in-memory index dynamically over all JSON domain catalogs containing _meta blocks.
"""

import logging
import time
import re
import os
import json
from glob import glob

from data.data_loader import TOOLS_CATALOG

logger = logging.getLogger(__name__)

KNOWN_PREFIXES = ("O_", "T_", "BC_", "W_", "H_", "P_", "R_", "F_", "S_", "WP_", "FL_")
DATA_DIR = os.getenv("DATA_DIR", "data")


def qualify_item_id(raw_id: str, default_prefix: str = "O_") -> str:
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
                
                # FIX: Guarantee parity with catalog.py generation logic
                # Ensure sanitization completely mirrors file output
                sprite_target = item_key_str.replace(":", "_").replace("/", "_").replace(" ", "_")
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
                    "icon": f"/cache/img/{prefix}/{sprite_key}.png"
                }

                # Register primary lookup keys safely without collisions
                lookup[f"({prefix}){item_key_str}"] = info
                
                if item_key_str not in lookup:
                    lookup[item_key_str] = info

                if sprite_key not in lookup:
                    lookup[sprite_key] = info

                # FIX: Cleaned up memory bloat from unnecessary fuzzy name variations. 
                # Keep primary exact-name mappings for chests.py xml_name fallbacks.
                if name and name != "Unknown":
                    if name not in lookup:
                        lookup[name] = info

                loaded_count += 1

        except Exception as e:
            logger.warning(f"[ReferenceData] Failed to parse catalog {file_path}: {e}")

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    _OBJECT_LOOKUP_CACHE = lookup
    logger.debug(
        f"Built dynamic object lookup cache with {len(lookup)} routing keys "
        f"({loaded_count} items indexed) in {elapsed_ms:.2f}ms"
    )
    return lookup



def get_object_info(harvest_id: str, fallback_name: str = None) -> dict:
    if not harvest_id or str(harvest_id).strip() in ("None", "-1", ""):
        return {
            "name": "Wild / Unknown",
            "icon": "/static/img/placeholder.svg",
            "price": 0,
        }

    raw_input = str(harvest_id).strip()
    lookup = _get_object_lookup()

    if raw_input in lookup:
        return dict(lookup[raw_input])

    tag_mapping = {
        "(O)": "O_",
        "(W)": "W_",
        "(BC)": "BC_",
        "(T)": "T_",
        "(H)": "H_",
        "(P)": "P_",
        "(R)": "O_",
        "(F)": "F_",
        "(S)": "S_",
        "(WP)": "WP_",
        "(FL)": "FL_"
    }


    for tag, catalog_prefix in tag_mapping.items():
        if tag in raw_input:
            bare_id = raw_input.replace(tag, "").strip()
            while "(" in bare_id and ")" in bare_id:
                bare_id = re.sub(r'\([^)]*\)', '', bare_id).strip()
            
            prefixed_key = f"{catalog_prefix}{bare_id}"
            if prefixed_key in lookup:
                return dict(lookup[prefixed_key])

    clean_key = raw_input
    while "(" in clean_key and ")" in clean_key:
        clean_key = re.sub(r'\([^)]*\)', '', clean_key).strip()

    if clean_key in lookup:
        return dict(lookup[clean_key])
        
    # Catch case-insensitive 1.6 string IDs as a final fallback
    if clean_key.lower() in lookup:
        return dict(lookup[clean_key.lower()])
        
    for prefix in KNOWN_PREFIXES:
        if clean_key.startswith(prefix):
            bare_id = clean_key[len(prefix):]
            if bare_id in lookup:
                return dict(lookup[bare_id])

    fallback_prefix = "O"
    for tag, cat_prefix in tag_mapping.items():
        if tag in raw_input:
            fallback_prefix = cat_prefix.replace("_", "")
            break

    formatted_name = fallback_name if fallback_name else clean_key.replace("_", " ")
    
    if clean_key.startswith(KNOWN_PREFIXES):
        icon_filename = clean_key
        fallback_prefix = clean_key.split("_")[0]
    else:
        icon_filename = f"{fallback_prefix}_{clean_key}"

    return {
        "id": clean_key,
        "name": formatted_name,
        "price": 0,
        "prefix": fallback_prefix,
        "icon": f"/cache/img/{fallback_prefix}/{icon_filename}.png",
        "sprite_key": icon_filename,
    }
    