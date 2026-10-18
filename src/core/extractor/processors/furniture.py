import json
import logging
import os
from PIL import Image

logger = logging.getLogger(__name__)

def process_furniture(temp_unpacked_dir: str, config: dict, cache_dir: str) -> int:
    """Extracts variable-sized furniture items based on collision dimensions and type."""
    file_path = config["file_path"]
    meta = config["meta"]
    
    prefix = meta.get("prefix", "F")
    source_xnb = meta.get("source_xnb", "TileSheets/furniture.xnb")

    filename = os.path.basename(source_xnb).replace(".xnb", ".png")
    sheet_path = os.path.join(temp_unpacked_dir, filename)

    if not os.path.exists(sheet_path):
        logger.warning(f"[FurnitureProcessor] Spritesheet not found: {sheet_path}")
        return 0

    out_dir = os.path.join(cache_dir, "img", prefix)
    os.makedirs(out_dir, exist_ok=True)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"[FurnitureProcessor] Failed to read {file_path}: {e}")
        return 0

    items = data.get("items", {})
    if not items:
        return 0

    try:
        img = Image.open(sheet_path)
    except Exception as e:
        logger.error(f"[FurnitureProcessor] Failed opening sheet {sheet_path}: {e}")
        return 0

    sheet_w, sheet_h = img.size
    # Stardew furniture sheets use a 16px grid base
    tiles_per_row = sheet_w // 16 

    count = 0
    # Flat types do not get the +16px vertical sprite height extension
    flat_types = {"rug"}

    for item_key, item_data in items.items():
        if not isinstance(item_data, dict):
            continue
            
        sprite_index = item_data.get("SpriteIndex", -1)
        if sprite_index < 0:
            continue
            
        width_tiles = item_data.get("Width", 1)
        height_tiles = item_data.get("Height", 1)
        f_type = str(item_data.get("Type", "other")).lower()

        # Calculate pixel dimensions
        crop_w = width_tiles * 16
        crop_h = height_tiles * 16
        
        # Add the visual overhang for non-flat furniture (chairs, tables, etc.)
        if f_type not in flat_types:
            crop_h += 16
            
        # SpriteIndex points to the top-left 16x16 tile of the item
        start_col = sprite_index % tiles_per_row
        start_row = sprite_index // tiles_per_row
        
        x = start_col * 16
        y = start_row * 16
        
        # Ensure we don't attempt to crop outside the image boundaries
        if x + crop_w > sheet_w or y + crop_h > sheet_h:
            logger.debug(f"[FurnitureProcessor] Skipping {item_key}: Dimensions exceed sheet bounds.")
            continue

        try:
            cropped = img.crop((x, y, x + crop_w, y + crop_h))
            out_filename = f"{prefix}_{item_key}.png"
            cropped.save(os.path.join(out_dir, out_filename))
            count += 1
        except Exception as e:
            logger.warning(f"[FurnitureProcessor] Failed cropping {item_key}: {e}")

    logger.info(f"[FurnitureProcessor] Extracted {count} items from {filename} into {prefix}/ subfolder.")
    return count
    