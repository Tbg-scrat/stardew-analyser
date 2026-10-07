import hashlib
import os
import tempfile
from unittest.mock import patch
from PIL import Image
import pytest

from src.core.asset_extractor import (
    compute_content_hash,
    is_cache_valid,
    slice_spritesheet,
    extract_all_assets,
)


@pytest.fixture
def temp_extractor_dirs():
    """Provides isolated temporary content and cache directories."""
    with tempfile.TemporaryDirectory() as tmp_content, tempfile.TemporaryDirectory() as tmp_cache:
        yield tmp_content, tmp_cache


def test_compute_content_hash(temp_extractor_dirs):
    tmp_content, _ = temp_extractor_dirs

    # Missing ContentHashes.json returns 'unknown'
    assert compute_content_hash(tmp_content) == "unknown"

    # Valid ContentHashes.json returns MD5 hash
    hash_file = os.path.join(tmp_content, "ContentHashes.json")
    payload = b"content_hash_test_payload"
    with open(hash_file, "wb") as f:
        f.write(payload)

    expected_md5 = hashlib.md5(payload).hexdigest()
    assert compute_content_hash(tmp_content) == expected_md5


def test_is_cache_valid(temp_extractor_dirs):
    tmp_content, tmp_cache = temp_extractor_dirs
    marker_file = os.path.join(tmp_cache, ".extracted_marker")

    with patch("src.core.asset_extractor.CONTENT_DIR", tmp_content), patch(
        "src.core.asset_extractor.MARKER_FILE", marker_file
    ):
        # Missing marker file -> Invalid
        assert not is_cache_valid()

        # Valid marker file matching current content -> Valid
        current_hash = compute_content_hash(tmp_content)
        with open(marker_file, "w") as f:
            f.write(current_hash)

        assert is_cache_valid()

        # Outdated marker file -> Invalid
        with open(marker_file, "w") as f:
            f.write("outdated_hash_value")

        assert not is_cache_valid()


def test_slice_spritesheet(temp_extractor_dirs):
    _, tmp_cache = temp_extractor_dirs
    out_dir = os.path.join(tmp_cache, "img", "items")
    sheet_path = os.path.join(tmp_cache, "test_sheet.png")

    # Create a 32x16 sheet with 2 tiles: Tile 0 filled (red), Tile 1 empty (transparent)
    img = Image.new("RGBA", (32, 16), (0, 0, 0, 0))
    for x in range(16):
        for y in range(16):
            img.putpixel((x, y), (255, 0, 0, 255))
    img.save(sheet_path)

    with patch("src.core.asset_extractor.OUTPUT_IMG_DIR", out_dir):
        sliced_count = slice_spritesheet(
            sheet_path=sheet_path,
            prefix="O",
            tile_w=16,
            tile_h=16,
            tiles_per_row=2,
        )

        # Asserts only the non-transparent tile is saved
        assert sliced_count == 1
        assert os.path.exists(os.path.join(out_dir, "O_0.png"))
        assert not os.path.exists(os.path.join(out_dir, "O_1.png"))


def test_slice_spritesheet_missing_file():
    assert slice_spritesheet("non_existent_sheet.png", "O", 16, 16, 24) == 0


@patch("src.core.asset_extractor.is_cache_valid")
def test_extract_all_assets_skips_when_valid(mock_is_valid):
    mock_is_valid.return_value = True
    assert extract_all_assets() is True


@patch("src.core.asset_extractor.is_cache_valid", return_value=False)
def test_extract_all_assets_missing_content_dir(mock_is_valid, temp_extractor_dirs):
    _, tmp_cache = temp_extractor_dirs
    missing_content_dir = os.path.join(tmp_cache, "non_existent_content")

    with patch("src.core.asset_extractor.CONTENT_DIR", missing_content_dir):
        assert extract_all_assets() is False
