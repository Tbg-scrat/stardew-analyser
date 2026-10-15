import logging
import os
import shutil
import subprocess
from src.core.logger import setup_logging

from .cache_validator import compute_source_hash, is_cache_valid, save_cache_marker
from .image_utils import resolve_case_insensitive_path
from .processors.items import extract_objects_from_catalog
from .processors.tools import extract_tools_from_catalog
from .processors.social import extract_portraits
from .processors.spritesheets import extract_quality_stars, slice_spritesheet

setup_logging()
logger = logging.getLogger(__name__)

XNBCLI_BIN = os.getenv("XNBCLI_BIN", "/app/bin/xnbcli/xnbcli")
CONTENT_DIR = os.getenv("CONTENT_DIR", "/content")
CACHE_DIR = os.getenv("CACHE_DIR", "/cache")


def extract_all_assets() -> bool:
    """Main extraction routine calling xnbcli and executing domain processors."""
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

        # Stage Portraits directory if present
        portraits_src = resolve_case_insensitive_path(CONTENT_DIR, "Portraits")
        if portraits_src and os.path.isdir(portraits_src):
            portraits_dst = os.path.join(temp_packed, "Portraits")
            os.makedirs(portraits_dst, exist_ok=True)
            for file in os.listdir(portraits_src):
                if file.lower().endswith(".xnb"):
                    shutil.copy(os.path.join(portraits_src, file), os.path.join(portraits_dst, file))
            logger.debug("[AssetExtractor] Staged Portraits directory.")

        cmd = [XNBCLI_BIN, "unpack", temp_packed, temp_unpacked]
        logger.debug(f"[AssetExtractor] Executing xnbcli: {' '.join(cmd)}")
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.debug(f"[AssetExtractor] xnbcli output: {res.stdout.strip()}")

        # 1. Manifest-driven catalog extraction (outputs O_{key}.png)
        extract_objects_from_catalog(temp_unpacked)

        # 2. Grid-based slicing for non-object spritesheets
        craft_png = os.path.join(temp_unpacked, "Craftables.png")
        tools_png = os.path.join(temp_unpacked, "tools.png")
        cursors_png = os.path.join(temp_unpacked, "Cursors.png")

        slice_spritesheet(craft_png, "BC", 16, 32, 8)
        extract_tools_from_catalog(temp_unpacked)
        extract_quality_stars(cursors_png)

        craft2_png = os.path.join(temp_unpacked, "Craftables2.png")
        if os.path.exists(craft2_png):
            slice_spritesheet(craft2_png, "BC2", 16, 32, 8)

        # 3. NPC Portrait extraction
        extract_portraits(temp_unpacked)

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
