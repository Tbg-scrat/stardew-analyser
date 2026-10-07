import hashlib
import logging
import os
import shutil
import subprocess
from PIL import Image
from src.core.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

XNBCLI_BIN = os.getenv("XNBCLI_BIN", "/app/bin/xnbcli/xnbcli")
CONTENT_DIR = os.getenv("CONTENT_DIR", "/content")
CACHE_DIR = os.getenv("CACHE_DIR", "/cache")
MARKER_FILE = os.path.join(CACHE_DIR, ".extracted_marker")
OUTPUT_IMG_DIR = os.path.join(CACHE_DIR, "img", "items")


def compute_content_hash(content_path: str) -> str:
    """Compute MD5 hash of ContentHashes.json to detect game updates."""
    hash_file = os.path.join(content_path, "ContentHashes.json")
    if not os.path.exists(hash_file):
        logger.debug(f"[AssetExtractor] ContentHashes.json not found at {hash_file}")
        return "unknown"

    with open(hash_file, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def is_cache_valid() -> bool:
    """Check if cache marker exists and matches current game files."""
    if not os.path.exists(MARKER_FILE):
        logger.debug("[AssetExtractor] Cache marker file missing.")
        return False

    current_hash = compute_content_hash(CONTENT_DIR)
    try:
        with open(MARKER_FILE, "r") as f:
            cached_hash = f.read().strip()
        is_valid = current_hash == cached_hash
        logger.debug(f"[AssetExtractor] Cache validity: {is_valid} (cached: {cached_hash}, current: {current_hash})")
        return is_valid
    except Exception as e:
        logger.warning(f"[AssetExtractor] Failed to read marker file: {e}")
        return False


def slice_spritesheet(sheet_path: str, prefix: str, tile_w: int, tile_h: int, tiles_per_row: int) -> int:
    """Slice an unpacked spritesheet PNG into individual item tiles."""
    if not os.path.exists(sheet_path):
        logger.error(f"[AssetExtractor] Spritesheet not found: {sheet_path}")
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
            crop_box = (col * tile_w, row * tile_h, (col + 1) * tile_w, (row + 1) * tile_h)

            tile = img.crop(crop_box)
            if not tile.getbbox():
                continue

            tile_path = os.path.join(OUTPUT_IMG_DIR, f"{prefix}_{tile_id}.png")
            tile.save(tile_path)
            count += 1

    logger.debug(f"[AssetExtractor] Sliced {count} tiles from {sheet_path} with prefix '{prefix}'")
    return count


def extract_all_assets() -> bool:
    """Main extraction routine calling xnbcli and slicing sprite sheets."""
    if is_cache_valid():
        logger.info("[AssetExtractor] Asset cache is up to date. Skipping extraction.")
        return True

    if not os.path.exists(CONTENT_DIR):
        logger.warning(f"[AssetExtractor] Content directory '{CONTENT_DIR}' not found. Skipping extraction.")
        return False

    logger.info("[AssetExtractor] Extracting game assets from content volume...")
    temp_packed = os.path.join(CACHE_DIR, "_tmp_packed")
    temp_unpacked = os.path.join(CACHE_DIR, "_tmp_unpacked")

    os.makedirs(temp_packed, exist_ok=True)
    os.makedirs(temp_unpacked, exist_ok=True)

    try:
        targets = [
            ("Maps/springobjects.xnb", "springobjects.xnb"),
            ("TileSheets/Craftables.xnb", "Craftables.xnb"),
            ("TileSheets/tools.xnb", "tools.xnb"),
        ]

        for src_rel, dst_name in targets:
            src_path = os.path.join(CONTENT_DIR, src_rel)
            if os.path.exists(src_path):
                shutil.copy(src_path, os.path.join(temp_packed, dst_name))
                logger.debug(f"[AssetExtractor] Staged {src_rel} for unpacking.")

        cmd = [XNBCLI_BIN, "unpack", temp_packed, temp_unpacked]
        logger.debug(f"[AssetExtractor] Executing xnbcli: {' '.join(cmd)}")
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.debug(f"[AssetExtractor] xnbcli output: {res.stdout.strip()}")

        spring_png = os.path.join(temp_unpacked, "springobjects.png")
        craft_png = os.path.join(temp_unpacked, "Craftables.png")
        tools_png = os.path.join(temp_unpacked, "tools.png")

        slice_spritesheet(spring_png, "O", 16, 16, 24)
        slice_spritesheet(craft_png, "BC", 16, 32, 8)
        slice_spritesheet(tools_png, "T", 16, 16, 21)

        current_hash = compute_content_hash(CONTENT_DIR)
        with open(MARKER_FILE, "w") as f:
            f.write(current_hash)

        logger.info("[AssetExtractor] Asset extraction completed successfully.")
        return True

    except Exception as e:
        logger.error(f"[AssetExtractor] Extraction failed: {e}", exc_info=True)
        return False
    finally:
        shutil.rmtree(temp_packed, ignore_errors=True)
        shutil.rmtree(temp_unpacked, ignore_errors=True)


if __name__ == "__main__":
    extract_all_assets()
    