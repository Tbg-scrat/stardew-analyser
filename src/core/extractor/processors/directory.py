import json
import logging
import os

from PIL import Image

logger = logging.getLogger(__name__)


def process_directory(temp_unpacked_dir: str, config: dict, cache_dir: str) -> int:
    """
    Extracts images from a directory of individual files (like Portraits).
    Supports cropping specific regions based on the _meta block.
    """
    meta = config.get("meta", {})

    prefix = meta.get("prefix")
    crop_coords = meta.get("crop")  # e.g., [0, 0, 64, 64]

    if not prefix:
        logger.error("[DirectoryProcessor] Missing 'prefix' in meta.")
        return 0

    out_dir = os.path.join(cache_dir, "img", prefix)
    os.makedirs(out_dir, exist_ok=True)

    count = 0
    file_path = config.get("file_path")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"[DirectoryProcessor] Failed to read {file_path}: {e}")
        return 0

    items = data.get("villagers", {})

    if not items:
        logger.warning(f"[DirectoryProcessor] No items found to extract for prefix {prefix}")
        return 0

    # Fix: Resolve the source directory to maintain nested structure parity with router
    source_dir = meta.get("source_dir", "")
    base_source_path = os.path.join(temp_unpacked_dir, source_dir.replace("\\", "/"))

    for item_key in items.keys():
        safe_key = str(item_key).strip()
        source_filename = f"{safe_key}.png"
        source_path = os.path.join(base_source_path, source_filename)

        if not os.path.exists(source_path):
            logger.debug(f"[DirectoryProcessor] Source file not found: {source_path}")
            continue

        try:
            with Image.open(source_path) as img:
                if crop_coords and len(crop_coords) == 4:
                    out_img = img.crop(tuple(crop_coords))
                else:
                    out_img = img

                out_filename = f"{safe_key}.png"
                out_img.save(os.path.join(out_dir, out_filename))
                count += 1
        except Exception as e:
            logger.warning(f"[DirectoryProcessor] Failed processing {source_filename}: {e}")

    logger.info(f"[DirectoryProcessor] Extracted {count} images into {prefix}/")
    return count
