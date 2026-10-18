import json
import logging
import os
from PIL import Image
from ..image_utils import crop_tile

logger = logging.getLogger(__name__)

def process_catalog(temp_unpacked_dir: str, config: dict, cache_dir: str) -> int:
    """Extracts item icons based on a JSON catalog mapping."""
    file_path = config["file_path"]
    meta = config["meta"]
    
    prefix = meta.get("prefix", "O")
    tile_w = meta.get("tile_width", 16)
    tile_h = meta.get("tile_height", 16)
    default_texture_xnb = meta.get("default_texture", "Maps/springobjects.xnb")

    # 1. Load the full JSON to access the items dictionary
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"[CatalogProcessor] Failed to read {file_path}: {e}")
        return 0

    items = data.get("items", {})
    if not items:
        logger.warning(f"[CatalogProcessor] No items found in {file_path}")
        return 0

    # 2. Pre-load all available spritesheets in the unpacked directory
    loaded_sheets = {}
    for filename in os.listdir(temp_unpacked_dir):
        if filename.lower().endswith(".png"):
            key = os.path.splitext(filename)[0].lower()
            try:
                loaded_sheets[key] = Image.open(os.path.join(temp_unpacked_dir, filename))
            except Exception as e:
                logger.error(f"[CatalogProcessor] Failed to open image {filename}: {e}")

    default_sheet_name = os.path.basename(default_texture_xnb).replace(".xnb", "").lower()
    default_sheet = loaded_sheets.get(default_sheet_name)
    
    if not default_sheet:
        logger.warning(f"[CatalogProcessor] Default texture '{default_sheet_name}.png' missing in unpacked files.")
        return 0

    # 3. Setup output directory
    out_dir = os.path.join(cache_dir, "img", prefix)
    os.makedirs(out_dir, exist_ok=True)
    
    count = 0
    missing_sheets_warned = set()

    # 4. Iterate and extract
    for item_key, item_data in items.items():
        if not isinstance(item_data, dict):
            continue
        
        sprite_index = item_data.get("SpriteIndex")
        if sprite_index is None or sprite_index < 0:
            continue

        # Handle custom texture overrides if they exist
        texture_path = item_data.get("Texture")
        if not texture_path:
            sheet_img = default_sheet
        else:
            sheet_name = os.path.basename(texture_path.replace("\\", "/")).replace(".xnb", "").lower()
            sheet_img = loaded_sheets.get(sheet_name)
            if not sheet_img:
                if sheet_name not in missing_sheets_warned:
                    logger.warning(f"[CatalogProcessor] Required texture '{sheet_name}' not found. Falling back to default.")
                    missing_sheets_warned.add(sheet_name)
                sheet_img = default_sheet

        # Crop and save
        tile = crop_tile(sheet_img, sprite_index, tile_w=tile_w, tile_h=tile_h)
        if tile:
            item_key_str = str(item_key)
            sprite_target = item_key_str
            
            # Exclude Tools (T), Wallpapers (WP), and Flooring (FL) from numeric routing
            if not item_key_str.isdigit() and prefix not in ("T", "WP", "FL"):
                sprite_target = str(sprite_index)

            # Sanitize colons for safe file saving (e.g., "MoreWalls:11" -> "MoreWalls_11")
            sprite_target = sprite_target.replace(":", "_")

            out_filename = f"{prefix}_{sprite_target}.png"
            tile.save(os.path.join(out_dir, out_filename))
            count += 1

    logger.info(f"[CatalogProcessor] Extracted {count} items from {os.path.basename(file_path)} into {prefix}/ subfolder.")
    return count
    