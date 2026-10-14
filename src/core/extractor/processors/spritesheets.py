import logging
import os
from PIL import Image
from ..image_utils import crop_tile

logger = logging.getLogger(__name__)

CACHE_DIR = os.getenv("CACHE_DIR", "/cache")
OUTPUT_IMG_DIR = os.path.join(CACHE_DIR, "img", "items")


def slice_spritesheet(sheet_path: str, prefix: str, tile_w: int, tile_h: int, tiles_per_row: int) -> int:
    """Slice an unpacked generic spritesheet PNG into individual item tiles."""
    if not os.path.exists(sheet_path):
        logger.warning(f"[AssetExtractor] Spritesheet not found: {sheet_path}")
        return 0

    img = Image.open(sheet_path)
    sheet_w, sheet_h = img.size
    cols = tiles_per_row
    rows = sheet_h // tile_h

    os.makedirs(OUTPUT_IMG_DIR, exist_ok=True)
    count = 0

    for row in range(rows):
        for col in range(cols):
            tile_id = row * cols + col
            tile = crop_tile(img, tile_id, tile_w, tile_h, tiles_per_row=cols)
            if not tile:
                continue

            tile_path = os.path.join(OUTPUT_IMG_DIR, f"{prefix}_{tile_id}.png")
            tile.save(tile_path)
            count += 1

    logger.debug(f"[AssetExtractor] Sliced {count} tiles from {sheet_path} with prefix '{prefix}'")
    return count


def extract_quality_stars(cursors_path: str) -> bool:
    """Slice 8x8 quality star badges from unpacked Cursors.png into items cache."""
    if not os.path.exists(cursors_path):
        logger.warning(f"[AssetExtractor] Cursors.png not found for star badges: {cursors_path}")
        return False

    os.makedirs(OUTPUT_IMG_DIR, exist_ok=True)
    img = Image.open(cursors_path)

    stars = {
        "silver_star.png": (338, 400, 346, 408),
        "gold_star.png": (346, 400, 354, 408),
        "iridium_star.png": (346, 392, 354, 400),
    }

    for filename, box in stars.items():
        star_crop = img.crop(box)
        star_crop.save(os.path.join(OUTPUT_IMG_DIR, filename))

    logger.debug("[AssetExtractor] Extracted quality star badges to items cache.")
    return True
