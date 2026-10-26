# src/core/extractor/cache_validator.py
import json
import logging
import os

logger = logging.getLogger(__name__)

CACHE_DIR = os.getenv("CACHE_DIR", "/cache")
MANIFEST_FILE = os.path.join(CACHE_DIR, "extraction_manifest.json")
OUTPUT_IMG_DIR = os.path.join(CACHE_DIR, "img")


def is_cache_valid() -> bool:
    """Fast check: verifies manifest exists and all listed target files exist on disk."""
    if not os.path.exists(MANIFEST_FILE):
        logger.debug("[CacheValidator] Manifest file missing. Cache invalid.")
        return False

    if not os.path.exists(OUTPUT_IMG_DIR):
        logger.debug("[CacheValidator] Target image directory missing. Cache invalid.")
        return False

    try:
        with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        expected_files = manifest.get("files", [])
        if not expected_files:
            logger.debug("[CacheValidator] Manifest contains no files.")
            return False

        missing_count = 0
        for rel_path in expected_files:
            full_path = os.path.join(CACHE_DIR, rel_path)
            if not os.path.exists(full_path):
                missing_count += 1
                if missing_count > 5:  # Stop early if multiple files are missing
                    break

        if missing_count > 0:
            logger.debug(f"[CacheValidator] Cache invalid: {missing_count} expected files missing.")
            return False

        logger.info("[CacheValidator] Cache manifest verified. All target files present.")
        return True

    except Exception as e:
        logger.warning(f"[CacheValidator] Failed reading manifest: {e}")
        return False


def save_cache_manifest() -> None:
    """Walks /cache/img after extraction and writes a manifest of all generated files."""
    expected_files = []

    if os.path.exists(OUTPUT_IMG_DIR):
        for root, _, files in os.walk(OUTPUT_IMG_DIR):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, CACHE_DIR)
                expected_files.append(rel_path.replace("\\", "/"))

    manifest_data = {"files": expected_files, "total_files": len(expected_files)}

    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)

    logger.info(f"[CacheValidator] Saved extraction manifest with {len(expected_files)} files.")
