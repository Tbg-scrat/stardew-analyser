import json
import logging
import os
from PIL import Image

logger = logging.getLogger(__name__)

def process_free_crop(temp_unpacked_dir: str, config: dict, cache_dir: str) -> int:
    """Extracts UI elements using exact pixel bounding boxes."""
    file_path = config["file_path"]
    meta = config["meta"]
    
    prefix = meta.get("prefix", "items")
    source_xnb = meta.get("source_xnb", "")

    filename = os.path.basename(source_xnb).replace(".xnb", ".png")
    sheet_path = os.path.join(temp_unpacked_dir, filename)

    if not os.path.exists(sheet_path):
        logger.warning(f"[FreeCropProcessor] Spritesheet not found: {sheet_path}")
        return 0

    out_dir = os.path.join(cache_dir, "img", prefix)
    os.makedirs(out_dir, exist_ok=True)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"[FreeCropProcessor] Failed to read {file_path}: {e}")
        return 0

    elements = data.get("elements", {})
    if not elements:
        return 0

    try:
        img = Image.open(sheet_path)
    except Exception as e:
        logger.error(f"[FreeCropProcessor] Failed opening sheet {sheet_path}: {e}")
        return 0

    count = 0
    for key, box in elements.items():
        if len(box) == 4:
            try:
                # Pillow crop expects a tuple of (left, upper, right, lower)
                cropped = img.crop(tuple(box))
                out_filename = f"{key}.png"
                cropped.save(os.path.join(out_dir, out_filename))
                count += 1
            except Exception as e:
                logger.warning(f"[FreeCropProcessor] Failed cropping {key}: {e}")

    logger.info(f"[FreeCropProcessor] Extracted {count} elements from {filename} into {prefix}/ subfolder.")
    return count
    