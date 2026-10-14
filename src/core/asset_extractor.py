"""Backward-compatibility wrapper for src.core.extractor package."""
from src.core.extractor import extract_all_assets
from src.core.extractor.cache_validator import (
    compute_source_hash,
    compute_source_hash as compute_content_hash,
    compute_target_metadata_hash,
    is_cache_valid,
    save_cache_marker,
)
from src.core.extractor.image_utils import crop_tile, resolve_case_insensitive_path
from src.core.extractor.processors.items import extract_objects_from_catalog
from src.core.extractor.processors.spritesheets import extract_quality_stars, slice_spritesheet

__all__ = [
    "extract_all_assets",
    "compute_source_hash",
    "compute_content_hash",
    "compute_target_metadata_hash",
    "is_cache_valid",
    "save_cache_marker",
    "resolve_case_insensitive_path",
    "crop_tile",
    "extract_objects_from_catalog",
    "slice_spritesheet",
    "extract_quality_stars",
]

if __name__ == "__main__":
    extract_all_assets()
