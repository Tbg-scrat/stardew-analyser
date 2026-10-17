import json
import logging
import os
import shutil
import subprocess
from glob import glob

from src.core.logger import setup_logging
from .cache_validator import compute_source_hash, is_cache_valid, save_cache_marker
from .image_utils import resolve_case_insensitive_path
from .processors.grid import process_grid

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
                if isinstance(data, dict) and "_meta" in data:
                    configs.append({
                        "file_path": file_path,
                        "meta": data["_meta"]
                    })
        except Exception as e:
            logger.warning(f"[Router] Failed to parse JSON config at {file_path}: {e}")
    return configs

def extract_assets() -> bool:
    """Main extraction routine driven by JSON domain configurations."""
    if is_cache_valid():
        logger.info("[Router] Asset cache is up to date. Skipping extraction.")
        return True

    if not os.path.exists(CONTENT_DIR):
        logger.warning(f"[Router] Content directory '{CONTENT_DIR}' not found.")
        return False

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
                
            src_rel = meta.get("source_xnb")
            if not src_rel or src_rel in staged_files:
                continue
                
            dst_name = os.path.basename(src_rel)
            src_path = resolve_case_insensitive_path(CONTENT_DIR, src_rel)
            if src_path:
                shutil.copy(src_path, os.path.join(temp_packed, dst_name))
                staged_files.add(src_rel)
                logger.debug(f"[Router] Staged asset: {src_rel}")
            else:
                logger.warning(f"[Router] Required asset missing from content volume: {src_rel}")

        if not staged_files:
            logger.info("[Router] No assets required staging based on domain configs. Exiting.")
            return True

        # 2. Unpack Phase
        cmd = [XNBCLI_BIN, "unpack", temp_packed, temp_unpacked]
        logger.debug(f"[Router] Executing xnbcli: {' '.join(cmd)}")
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.debug(f"[Router] xnbcli unpacked successfully.")

        # 3. Processing Dispatch Phase
        for config in domain_configs:
            meta = config["meta"]
            if not meta.get("extract_images"):
                continue

            processor_type = meta.get("processor")
            if processor_type == "grid":
                process_grid(temp_unpacked, meta, CACHE_DIR)
            elif processor_type == "catalog":
                logger.info(f"[Router] Catalog processor placeholder reached for {config['file_path']}")
            else:
                logger.warning(f"[Router] Unknown processor type '{processor_type}' in {config['file_path']}")

        # Validate cache completion
        current_source_hash = compute_source_hash(CONTENT_DIR)
        save_cache_marker(current_source_hash)

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
    