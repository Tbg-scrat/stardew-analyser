import json
import logging
import os
from PIL import Image
from ..image_utils import crop_tile

logger = logging.getLogger(__name__)

CACHE_DIR = os.getenv("CACHE_DIR", "/cache")
OUTPUT_IMG_DIR = os.path.join(CACHE_DIR, "img", "items")
OBJECTS_JSON_PATH = os.path.join("data", "objects.json")


def extract_objects_from_catalog(temp_unpacked_dir: str) -> int:
    """Parse objects.json manifest and extract item icons based on Texture and SpriteIndex."""
    if not os.path.exists(OBJECTS_JSON_PATH):
        logger.warning(f"[AssetExtractor] Catalog manifest missing at {OBJECTS_JSON_PATH}.")
        return 0

    try:
        with open(OBJECTS_JSON_PATH, "r", encoding="utf-8") as f:
            objects_data = json.load(f)
    except Exception as e:
        logger.error(f"[AssetExtractor] Failed reading {OBJECTS_JSON_PATH}: {e}")
        return 0

    loaded_sheets = {}
    for filename in os.listdir(temp_unpacked_dir):
        if filename.lower().endswith(".png"):
            key = os.path.splitext(filename)[0].lower()
            loaded_sheets[key] = Image.open(os.path.join(temp_unpacked_dir, filename))

    default_sheet = loaded_sheets.get("springobjects")
    if not default_sheet:
        logger.warning("[AssetExtractor] springobjects.png missing in unpacked files.")
        return 0

    os.makedirs(OUTPUT_IMG_DIR, exist_ok=True)
    count = 0
    missing_sheets_warned = set()

    for item_key, item_data in objects_data.items():
        if not isinstance(item_data, dict):
            continue

        sprite_index = item_data.get("SpriteIndex")
        if sprite_index is None:
            continue

        texture_path = item_data.get("Texture")
        if not texture_path:
            sheet_img = default_sheet
        else:
            sheet_name = os.path.basename(texture_path.replace("\\", "/")).lower()
            sheet_img = loaded_sheets.get(sheet_name)
            if not sheet_img:
                if sheet_name not in missing_sheets_warned:
                    logger.warning(
                        f"[AssetExtractor] Required texture sheet '{sheet_name}' (for item '{item_key}') "
                        f"not found in unpacked files. Falling back to springobjects."
                    )
                    missing_sheets_warned.add(sheet_name)
                sheet_img = default_sheet

        tile = crop_tile(sheet_img, sprite_index, tile_w=16, tile_h=16)
        if tile:
            out_filename = f"{item_key}.png" if str(item_key).startswith("O_") else f"O_{item_key}.png"
            tile.save(os.path.join(OUTPUT_IMG_DIR, out_filename))
            count += 1

    logger.debug(f"[AssetExtractor] Extracted {count} item icons using objects.json manifest.")
    return count
