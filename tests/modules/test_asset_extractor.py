import hashlib
import os
import subprocess
import tempfile
from unittest.mock import patch
from PIL import Image
import pytest

from src.core.asset_extractor import (
    compute_content_hash,
    extract_all_assets,
    extract_quality_stars,
    is_cache_valid,
    resolve_case_insensitive_path,
    slice_spritesheet,
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


def test_is_cache_valid_exception_handling(temp_extractor_dirs):
    tmp_content, tmp_cache = temp_extractor_dirs
    marker_file = os.path.join(tmp_cache, ".extracted_marker")

    # Create marker file
    with open(marker_file, "w") as f:
        f.write("test_hash")

    with patch("src.core.asset_extractor.CONTENT_DIR", tmp_content), patch(
        "src.core.asset_extractor.MARKER_FILE", marker_file
    ), patch("builtins.open", side_effect=PermissionError("Access denied")):
        # Exception while reading marker file -> Invalid (False)
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


def test_extract_quality_stars(temp_extractor_dirs):
    _, tmp_cache = temp_extractor_dirs
    out_dir = os.path.join(tmp_cache, "img", "items")
    cursors_path = os.path.join(tmp_cache, "Cursors.png")

    # Create dummy 500x500 Cursors.png image
    img = Image.new("RGBA", (500, 500), (0, 255, 0, 255))
    img.save(cursors_path)

    with patch("src.core.asset_extractor.OUTPUT_IMG_DIR", out_dir):
        assert extract_quality_stars(cursors_path) is True
        assert os.path.exists(os.path.join(out_dir, "silver_star.png"))
        assert os.path.exists(os.path.join(out_dir, "gold_star.png"))
        assert os.path.exists(os.path.join(out_dir, "iridium_star.png"))


def test_extract_quality_stars_missing_file():
    with pytest.raises(FileNotFoundError):
        extract_quality_stars("non_existent_cursors.png")


def test_resolve_case_insensitive_path(temp_extractor_dirs):
    tmp_content, _ = temp_extractor_dirs

    # Setup directories and files with mixed casing
    maps_dir = os.path.join(tmp_content, "maps")
    os.makedirs(maps_dir, exist_ok=True)
    target_file = os.path.join(maps_dir, "SPRINGOBJECTS.XNB")
    with open(target_file, "w") as f:
        f.write("dummy_xnb")

    # Exact match resolution
    exact_res = resolve_case_insensitive_path(tmp_content, "maps/SPRINGOBJECTS.XNB")
    assert exact_res == target_file

    # Case-insensitive resolution
    case_res = resolve_case_insensitive_path(tmp_content, "Maps/springobjects.xnb")
    assert case_res == target_file

    # Non-existent path returns None
    assert resolve_case_insensitive_path(tmp_content, "TileSheets/missing.xnb") is None


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


@patch("src.core.asset_extractor.is_cache_valid", return_value=False)
def test_extract_all_assets_success_flow(mock_is_valid, temp_extractor_dirs):
    tmp_content, tmp_cache = temp_extractor_dirs
    marker_file = os.path.join(tmp_cache, ".extracted_marker")
    out_dir = os.path.join(tmp_cache, "img", "items")

    # Create dummy source targets in content volume
    targets = [
        "Maps/springobjects.xnb",
        "TileSheets/Craftables.xnb",
        "TileSheets/tools.xnb",
        "LooseSprites/Cursors.xnb",
    ]
    for target in targets:
        full_path = os.path.join(tmp_content, target)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f:
            f.write("xnb_data")

    # Side-effect function simulating xnbcli creating unpacked PNGs in _tmp_unpacked
    def mock_subprocess_run(cmd, capture_output, text, check):
        temp_unpacked = cmd[3]
        for sheet_name in ["springobjects.png", "Craftables.png", "tools.png", "Cursors.png"]:
            img = Image.new("RGBA", (32, 32), (255, 0, 0, 255))
            img.save(os.path.join(temp_unpacked, sheet_name))
        return subprocess.CompletedProcess(cmd, 0, stdout="Unpacked successfully")

    with patch("src.core.asset_extractor.CONTENT_DIR", tmp_content), patch(
        "src.core.asset_extractor.CACHE_DIR", tmp_cache
    ), patch("src.core.asset_extractor.MARKER_FILE", marker_file), patch(
        "src.core.asset_extractor.OUTPUT_IMG_DIR", out_dir
    ), patch(
        "subprocess.run", side_effect=mock_subprocess_run
    ):
        assert extract_all_assets() is True
        assert os.path.exists(marker_file)


@patch("src.core.asset_extractor.is_cache_valid", return_value=False)
def test_extract_all_assets_missing_required_target(mock_is_valid, temp_extractor_dirs):
    tmp_content, tmp_cache = temp_extractor_dirs

    # Only create one of the targets (missing the rest)
    full_path = os.path.join(tmp_content, "Maps/springobjects.xnb")
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write("xnb_data")

    with patch("src.core.asset_extractor.CONTENT_DIR", tmp_content), patch(
        "src.core.asset_extractor.CACHE_DIR", tmp_cache
    ):
        assert extract_all_assets() is False
        