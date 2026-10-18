import logging
import os
from PIL import Image
from ..image_utils import crop_tile

logger = logging.getLogger(__name__)

def process_grid(temp_unpacked_dir: str, meta: dict, cache_dir: str) -> int:
    """Dynamically slices a spritesheet based on JSON metadata configuration."""
    source_xnb = meta.get("source_xnb", "")
    prefix = meta.get("prefix", "IMG")
    tile_w = meta.get("tile_width", 16)
    tile_h = meta.get("tile_height", 16)
    
    # NEW: Optional sub-crop dimensions
    crop_w = meta.get("crop_width", tile_w)
    crop_h = meta.get("crop_height", tile_h)
    
    tiles_per_row = meta.get("tiles_per_row", 0)

    # Reconstruct the unpacked .png filename from the source .xnb path
    filename = os.path.basename(source_xnb).replace(".xnb", ".png")
    sheet_path = os.path.join(temp_unpacked_dir, filename)

    if not os.path.exists(sheet_path):
        logger.warning(f"[GridProcessor] Required spritesheet not found: {sheet_path}")
        return 0

    out_dir = os.path.join(cache_dir, "img", prefix)
    os.makedirs(out_dir, exist_ok=True)

    try:
        img = Image.open(sheet_path)
    except Exception as e:
        logger.error(f"[GridProcessor] Failed opening sheet {sheet_path}: {e}")
        return 0

    sheet_w, sheet_h = img.size
    
    # Calculate grid bounds dynamically if not provided
    cols = tiles_per_row if tiles_per_row > 0 else sheet_w // tile_w
    if cols <= 0:
        logger.error("[GridProcessor] Invalid column count calculation.")
        return 0
        
    rows = sheet_h // tile_h
    count = 0

    for row in range(rows):
        for col in range(cols):
            tile_id = row * cols + col
            tile = crop_tile(img, tile_id, tile_w, tile_h, tiles_per_row=cols)
            if not tile:
                continue

            # NEW: Apply the sub-crop if it differs from the grid cell size
            if crop_w != tile_w or crop_h != tile_h:
                tile = tile.crop((0, 0, crop_w, crop_h))

            # Save the file into the new prefix subfolder
            tile_path = os.path.join(out_dir, f"{prefix}_{tile_id}.png")
            tile.save(tile_path)
            count += 1

    logger.info(f"[GridProcessor] Sliced {count} tiles from {filename} into {prefix}/ subfolder.")
    return count
    