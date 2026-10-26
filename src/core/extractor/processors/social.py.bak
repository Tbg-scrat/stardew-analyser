import logging
import os
from PIL import Image

logger = logging.getLogger(__name__)

CACHE_DIR = os.getenv("CACHE_DIR", "/cache")
OUTPUT_PORTRAITS_DIR = os.path.join(CACHE_DIR, "img", "portraits")


def extract_portraits(temp_unpacked_dir: str) -> int:
    """Extract 64x64 NPC headshots from unpacked Portraits PNG sheets."""
    portraits_dir = None
    for entry in os.listdir(temp_unpacked_dir):
        if entry.lower() == "portraits":
            candidate = os.path.join(temp_unpacked_dir, entry)
            if os.path.isdir(candidate):
                portraits_dir = candidate
                break

    if not portraits_dir or not os.path.exists(portraits_dir):
        logger.warning(
            f"[AssetExtractor] Portraits directory not found in {temp_unpacked_dir}."
        )
        return 0

    cache_dir = os.getenv("CACHE_DIR", "/cache")
    out_dir = os.path.join(cache_dir, "img", "portraits")
    os.makedirs(out_dir, exist_ok=True)
    count = 0

    for filename in os.listdir(portraits_dir):
        if not filename.lower().endswith(".png"):
            continue

        npc_name = os.path.splitext(filename)[0]
        sheet_path = os.path.join(portraits_dir, filename)

        try:
            img = Image.open(sheet_path)
            if img.width >= 64 and img.height >= 64:
                portrait = img.crop((0, 0, 64, 64))
                if portrait.getbbox():
                    out_path = os.path.join(out_dir, f"{npc_name}.png")
                    portrait.save(out_path)
                    count += 1
        except Exception as e:
            logger.warning(
                f"[AssetExtractor] Failed cropping portrait for {npc_name}: {e}"
            )

    logger.debug(f"[AssetExtractor] Extracted {count} NPC portraits.")
    return count
