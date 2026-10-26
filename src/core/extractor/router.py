# src/core/extractor/router.py

import json
import logging
import os
import shutil
import subprocess
from glob import glob

from src.core.logger import setup_logging
from .cache_validator import is_cache_valid, save_cache_manifest
from .image_utils import resolve_case_insensitive_path
from .processors.grid import process_grid
from .processors.catalog import process_catalog
from .processors.free_crop import process_free_crop
from .processors.furniture import process_furniture
from .processors.directory import process_directory


setup_logging()
logger = logging.getLogger(__name__)

XNBCLI_BIN = os.getenv("XNBCLI_BIN", "/app/bin/xnbcli/xnbcli")
CONTENT_DIR = os.getenv("CONTENT_DIR", "/content")
CACHE_DIR = os.getenv("CACHE_DIR", "/cache")
DATA_DIR = os.getenv("DATA_DIR", "data")


def get_domain_configs() -> list[dict]:
    """Scans the data directory for JSON files containing extraction _meta blocks."""
    configs = []
    json_files = glob(os.path.join(DATA_DIR, "*.json"))
    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and data.get("_meta") is not None:
                    configs.append({"file_path": file_path, "meta": data["_meta"]})
        except Exception as e:
            logger.warning(f"[Router] Failed to parse JSON config at {file_path}: {e}")
    return configs


def extract_assets() -> bool:
    """Main extraction routine driven by JSON domain configurations."""
    if is_cache_valid():
        logger.info("[Router] Asset cache is up to date. Skipping extraction.")
        return True

    if not os.path.exists(CONTENT_DIR):
        logger.warning(f"[Router] Content directory '{CONTENT_DIR}' not found. Serving placeholders.")
        # Graceful fallback: continue without extracting or saving manifest
        return True

    logger.info("[Router] Starting dynamic asset extraction...")
    temp_packed = os.path.join(CACHE_DIR, "_tmp_packed")
    temp_unpacked = os.path.join(CACHE_DIR, "_tmp_unpacked")

    os.makedirs(temp_packed, exist_ok=True)
    os.makedirs(temp_unpacked, exist_ok=True)

    try:
        domain_configs = get_domain_configs()

        # 1. Dynamic Staging Phase
        staged_files = set()
        for config in domain_configs:
            meta = config["meta"]
            if not meta.get("extract_images"):
                continue

            textures_to_stage = set()

            default_tex = meta.get("source_xnb") or meta.get("default_texture")
            if default_tex:
                textures_to_stage.add(default_tex)

            source_dir = meta.get("source_dir")
            if source_dir:
                full_source_dir = resolve_case_insensitive_path(
                    CONTENT_DIR, source_dir
                ) or os.path.join(CONTENT_DIR, source_dir)
                if os.path.isdir(full_source_dir):
                    for file in os.listdir(full_source_dir):
                        if file.lower().endswith(".xnb"):
                            textures_to_stage.add(
                                os.path.join(source_dir, file).replace("\\", "/")
                            )

            if meta.get("processor") == "catalog":
                try:
                    with open(config["file_path"], "r", encoding="utf-8") as f:
                        data = json.load(f)
                        items = data.get("items", {})
                        if not items:
                            items = {k: v for k, v in data.items() if k != "_meta"}

                        for item in items.values():
                            if isinstance(item, dict) and item.get("Texture"):
                                tex_path = item["Texture"]
                                if not tex_path.lower().endswith(".xnb"):
                                    tex_path += ".xnb"
                                textures_to_stage.add(tex_path)
                except Exception as e:
                    logger.warning(
                        f"[Router] Failed to peek textures in {config['file_path']}: {e}"
                    )

            for src_rel in textures_to_stage:
                src_rel_clean = src_rel.replace("\\", "/")
                if src_rel_clean in staged_files:
                    continue

                src_path = resolve_case_insensitive_path(CONTENT_DIR, src_rel_clean)
                if src_path:
                    relative_dir = os.path.dirname(src_rel_clean)
                    target_dir = os.path.join(temp_packed, relative_dir)
                    os.makedirs(target_dir, exist_ok=True)

                    target_file = os.path.join(temp_packed, src_rel_clean)
                    shutil.copy(src_path, target_file)
                    staged_files.add(src_rel_clean)
                    logger.debug(f"[Router] Staged asset: {src_rel_clean}")
                else:
                    logger.warning(
                        f"[Router] Required asset missing from content volume: {src_rel_clean}"
                    )

        if not staged_files:
            logger.info(
                "[Router] No assets required staging based on domain configs. Exiting."
            )
            return True

        # 2. Unpack Phase
        cmd = [XNBCLI_BIN, "unpack", temp_packed, temp_unpacked]
        logger.debug(f"[Router] Executing xnbcli: {' '.join(cmd)}")
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.debug(f"[Router] xnbcli unpacked successfully.")

        # 3. Processing Dispatch Phase
        for config in domain_configs:
            logger.debug(f"[Router] Dispatching config {config['file_path']} to processor '{config['meta'].get('processor')}'")
            meta = config["meta"]
            if not meta.get("extract_images"):
                continue

            processor_type = meta.get("processor")
            if processor_type == "grid":
                process_grid(temp_unpacked, config, CACHE_DIR)
            elif processor_type == "catalog":
                process_catalog(temp_unpacked, config, CACHE_DIR)
            elif processor_type == "free_crop":
                process_free_crop(temp_unpacked, config, CACHE_DIR)
            elif processor_type == "furniture":
                process_furniture(temp_unpacked, config, CACHE_DIR)
            elif processor_type == "directory":
                process_directory(temp_unpacked, config, CACHE_DIR)
            else:
                logger.warning(
                    f"[Router] Unknown processor type '{processor_type}' in {config['file_path']}"
                )

        save_cache_manifest()
        logger.info("[Router] Dynamic extraction completed successfully.")
        return True

    except Exception as e:
        logger.error(f"[Router] Extraction workflow failed: {e}", exc_info=True)
        return False
    finally:
        shutil.rmtree(temp_packed, ignore_errors=True)
        shutil.rmtree(temp_unpacked, ignore_errors=True)


if __name__ == "__main__":
    extract_assets()
    