import hashlib
import logging
import os

logger = logging.getLogger(__name__)

CACHE_DIR = os.getenv("CACHE_DIR", "/cache")
CONTENT_DIR = os.getenv("CONTENT_DIR", "/content")
MARKER_FILE = os.path.join(CACHE_DIR, ".extracted_marker")
OUTPUT_IMG_DIR = os.path.join(CACHE_DIR, "img", "items")


def compute_source_hash(content_path: str = CONTENT_DIR) -> str:
    """Compute MD5 hash for source content using ContentHashes.json or fallback file metadata."""
    hash_file = os.path.join(content_path, "ContentHashes.json")
    if os.path.exists(hash_file):
        try:
            with open(hash_file, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f"[AssetExtractor] Failed reading ContentHashes.json: {e}")

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


def compute_target_metadata_hash(target_dir: str = OUTPUT_IMG_DIR) -> str:
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
