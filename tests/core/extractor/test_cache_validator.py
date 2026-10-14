import os
from unittest.mock import patch
import pytest

from src.core.extractor.cache_validator import (
    compute_source_hash,
    compute_target_metadata_hash,
    is_cache_valid,
    save_cache_marker,
)


@pytest.fixture
def temp_cache_dirs(tmp_path):
    content_dir = tmp_path / "content"
    cache_dir = tmp_path / "cache"
    img_dir = cache_dir / "img" / "items"
    content_dir.mkdir(parents=True)
    img_dir.mkdir(parents=True)
    return str(content_dir), str(cache_dir), str(img_dir)


def test_compute_source_hash_with_content_hashes(temp_cache_dirs):
    content_dir, _, _ = temp_cache_dirs
    hash_file = os.path.join(content_dir, "ContentHashes.json")
    with open(hash_file, "wb") as f:
        f.write(b"dummy content hash")

    result = compute_source_hash(content_dir)
    assert len(result) == 32  # Valid MD5 hex string


def test_compute_source_hash_fallback(temp_cache_dirs):
    content_dir, _, _ = temp_cache_dirs
    xnb_file = os.path.join(content_dir, "test.xnb")
    with open(xnb_file, "w") as f:
        f.write("xnb data")

    result = compute_source_hash(content_dir)
    assert len(result) == 32


def test_compute_source_hash_no_files(temp_cache_dirs):
    content_dir, _, _ = temp_cache_dirs
    assert compute_source_hash(content_dir) == "unknown"


def test_compute_target_metadata_hash(temp_cache_dirs):
    _, _, img_dir = temp_cache_dirs
    assert compute_target_metadata_hash(img_dir) == "empty"

    dummy_file = os.path.join(img_dir, "item1.png")
    with open(dummy_file, "w") as f:
        f.write("img data")

    res = compute_target_metadata_hash(img_dir)
    assert len(res) == 32


def test_compute_target_metadata_hash_missing():
    assert compute_target_metadata_hash("/non_existent_path") == "missing"


def test_is_cache_valid_and_save_marker(temp_cache_dirs):
    content_dir, cache_dir, img_dir = temp_cache_dirs
    marker_file = os.path.join(cache_dir, ".extracted_marker")

    # Create dummy xnb and cached img
    with open(os.path.join(content_dir, "file.xnb"), "w") as f:
        f.write("data")
    with open(os.path.join(img_dir, "O_1.png"), "w") as f:
        f.write("img")

    with patch("src.core.extractor.cache_validator.CONTENT_DIR", content_dir), \
         patch("src.core.extractor.cache_validator.CACHE_DIR", cache_dir), \
         patch("src.core.extractor.cache_validator.OUTPUT_IMG_DIR", img_dir), \
         patch("src.core.extractor.cache_validator.MARKER_FILE", marker_file):

        assert is_cache_valid() is False

        src_hash = compute_source_hash(content_dir)
        save_cache_marker(src_hash)

        assert is_cache_valid() is True


def test_is_cache_valid_exception_handling(temp_cache_dirs):
    content_dir, cache_dir, img_dir = temp_cache_dirs
    marker_file = os.path.join(cache_dir, ".extracted_marker")
    with open(marker_file, "w") as f:
        f.write("invalid_marker_no_colon")

    with patch("src.core.extractor.cache_validator.CONTENT_DIR", content_dir), \
         patch("src.core.extractor.cache_validator.OUTPUT_IMG_DIR", img_dir), \
         patch("src.core.extractor.cache_validator.MARKER_FILE", marker_file):
        assert is_cache_valid() is False
