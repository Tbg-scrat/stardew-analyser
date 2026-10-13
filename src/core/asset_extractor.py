import hashlib
import json
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

# Extracted items and badges target directory
OUTPUT_IMG_DIR = os.path.join(CACHE_DIR, "img", "items")
OBJECTS_JSON_PATH = os.path.join("data", "objects.json")


def compute_source_hash(content_path: str) -> str:
    """Compute MD5 hash for source content using ContentHashes.json or fallback file metadata."""
    hash_file = os.path.join(content_path, "ContentHashes.json")
    if os.path.exists(hash_file):
        try:
            with open(hash_file, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f"[AssetExtractor] Failed reading ContentHashes.json: {e}")

    # Fallback: Hash key asset modification timestamps & file sizes if ContentHashes.json is absent
    hasher = hashlib.md5()
    found_files = 0
    for root, _, files in os.walk(content_path):
        for file in sorted(files):
            if file.lower().endswith(".xnb"):
                full_path = os.path.join(root, file)
                try:
                    stat = os.stat(full_path)
                    hasher.update(f"{file}:{stat.st_size}:{stat.st_mtime}".encode("utf-8"))
                    found_files += 1
                except OSError:
                    continue

    if found_files == 0:
        logger.debug(f"[AssetExtractor] No .xnb files found at {content_path}")
        return "unknown"

    return hasher.hexdigest()


def compute_target_metadata_hash(target_dir: str) -> str:
    """Compute fast target hash using directory file names and sizes without opening images."""
    if not os.path.exists(target_dir):
        return "missing"

    try:
        entries = sorted(os.scandir(target_dir), key=lambda e: e.name)
        if not entries:
            return "empty"

        hasher = hashlib.md5()
        for entry in entries:
            if entry.is_file():
                stat = entry.stat()
                hasher.update(f"{entry.name}:{stat.st_size}".encode("utf-8"))

        return hasher.hexdigest()
    except Exception as e:
        logger.warning(f"[AssetExtractor] Error hashing cache target metadata: {e}")
        return "error"


def is_cache_valid() -> bool:
    """Verify that both source content hash and target cache metadata hash match the saved marker."""
    if not os.path.exists(MARKER_FILE):
        logger.debug("[AssetExtractor] Cache marker file missing.")
        return False

    current_source_hash = compute_source_hash(CONTENT_DIR)
    if current_source_hash == "unknown":
        return False

    current_target_hash = compute_target_metadata_hash(OUTPUT_IMG_DIR)
    if current_target_hash in ("missing", "empty", "error"):
        logger.debug(f"[AssetExtractor] Cache directory invalid state: {current_target_hash}")
        return False

    try:
        with open(MARKER_FILE, "r") as f:
            marker_data = f.read().strip()

        if ":" not in marker_data:
            logger.debug("[AssetExtractor] Legacy or invalid marker format found.")
            return False

        saved_source_hash, saved_target_hash = marker_data.split(":", 1)

        source_valid = current_source_hash == saved_source_hash
        target_valid = current_target_hash == saved_target_hash

        is_valid = source_valid and target_valid
        logger.debug(
            f"[AssetExtractor] Cache validity: {is_valid} "
            f"(Source match: {source_valid}, Target match: {target_valid})"
        )
        return is_valid
    except Exception as e:
        logger.warning(f"[AssetExtractor] Failed reading marker file: {e}")
        return False


def save_cache_marker(source_hash: str) -> None:
    """Compute final target metadata hash and write <source_hash>:<target_hash> marker."""
    target_hash = compute_target_metadata_hash(OUTPUT_IMG_DIR)
    marker_content = f"{source_hash}:{target_hash}"
    with open(MARKER_FILE, "w") as f:
        f.write(marker_content)
    logger.debug(f"[AssetExtractor] Written marker record: {marker_content}")


def resolve_case_insensitive_path(base_dir: str, rel_path: str) -> str | None:
    """Resolve a relative file path in a case-insensitive manner."""
    exact_path = os.path.join(base_dir, rel_path)
    if os.path.exists(exact_path):
        return exact_path

    parts = rel_path.replace("\\", "/").split("/")
    curr = base_dir

    for part in parts:
        if not os.path.exists(curr) or not os.path.isdir(curr):
            return None
        entries = os.listdir(curr)
        match = next((e for e in entries if e.lower() == part.lower()), None)
        if match is None:
            return None
        curr = os.path.join(curr, match)

    return curr if os.path.exists(curr) else None


def crop_tile(sheet_img: Image.Image, sprite_index: int, tile_w: int = 16, tile_h: int = 16, tiles_per_row: int | None = None) -> Image.Image | None:
    """Crop a single tile from a spritesheet dynamically calculating tiles_per_row if not provided."""
    if tiles_per_row is None or tiles_per_row <= 0:
        tiles_per_row = sheet_img.width // tile_w

    if tiles_per_row == 0:
        return None

    col = sprite_index % tiles_per_row
    row = sprite_index // tiles_per_row

    crop_box = (col * tile_w, row * tile_h, (col + 1) * tile_w, (row + 1) * tile_h)

    if crop_box[2] > sheet_img.width or crop_box[3] > sheet_img.height:
        return None

    tile = sheet_img.crop(crop_box)
    return tile if tile.getbbox() else None


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

    # Index all unpacked PNG sheets in temp_unpacked_dir
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


def extract_quality_stars(cursors_path: str) -> bool:
    """Slice 8x8 quality star badges from unpacked Cursors.png into items cache."""
    if not os.path.exists(cursors_path):
        logger.warning(f"[AssetExtractor] Cursors.png not found for star badges: {cursors_path}")
        return False

    os.makedirs(OUTPUT_IMG_DIR, exist_ok=True)
    img = Image.open(cursors_path)

    # Box coordinates: (left, top, right, bottom) - 8x8 px
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
        required_targets = [
            ("Maps/springobjects.xnb", "springobjects.xnb"),
            ("TileSheets/Craftables.xnb", "Craftables.xnb"),
            ("TileSheets/tools.xnb", "tools.xnb"),
            ("LooseSprites/Cursors.xnb", "Cursors.xnb"),
        ]

        optional_targets = [
            ("TileSheets/Objects_2.xnb", "Objects_2.xnb"),
            ("Maps/springobjects2.xnb", "springobjects2.xnb"),
            ("TileSheets/Craftables2.xnb", "Craftables2.xnb"),
            ("LooseSprites/Cursors2.xnb", "Cursors2.xnb"),
        ]

        for src_rel, dst_name in required_targets:
            src_path = resolve_case_insensitive_path(CONTENT_DIR, src_rel)
            if src_path:
                shutil.copy(src_path, os.path.join(temp_packed, dst_name))
                logger.debug(f"[AssetExtractor] Staged required asset {src_rel} (resolved: {src_path}).")
            else:
                raise FileNotFoundError(f"[AssetExtractor] Required asset missing from content volume: {src_rel}")

        for src_rel, dst_name in optional_targets:
            src_path = resolve_case_insensitive_path(CONTENT_DIR, src_rel)
            if src_path:
                shutil.copy(src_path, os.path.join(temp_packed, dst_name))
                logger.debug(f"[AssetExtractor] Staged 1.6 optional asset {src_rel} (resolved: {src_path}).")

        cmd = [XNBCLI_BIN, "unpack", temp_packed, temp_unpacked]
        logger.debug(f"[AssetExtractor] Executing xnbcli: {' '.join(cmd)}")
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.debug(f"[AssetExtractor] xnbcli output: {res.stdout.strip()}")

        # 1. Manifest-driven extraction for standard & 1.6 objects (outputs O_{key}.png)
        extract_objects_from_catalog(temp_unpacked)

        # 2. Grid-based slicing for non-object spritesheets
        craft_png = os.path.join(temp_unpacked, "Craftables.png")
        tools_png = os.path.join(temp_unpacked, "tools.png")
        cursors_png = os.path.join(temp_unpacked, "Cursors.png")

        slice_spritesheet(craft_png, "BC", 16, 32, 8)
        slice_spritesheet(tools_png, "T", 16, 16, 21)
        extract_quality_stars(cursors_png)

        craft2_png = os.path.join(temp_unpacked, "Craftables2.png")
        if os.path.exists(craft2_png):
            slice_spritesheet(craft2_png, "BC2", 16, 32, 8)

        # Calculate source content hash & target cache metadata hash, then write marker
        current_source_hash = compute_source_hash(CONTENT_DIR)
        save_cache_marker(current_source_hash)

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
    