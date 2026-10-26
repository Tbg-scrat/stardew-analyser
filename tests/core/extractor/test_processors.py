# tests/core/extractor/test_processors.py

import pytest
from unittest.mock import patch, MagicMock, mock_open
import os

from src.core.extractor.processors.catalog import process_catalog
from src.core.extractor.processors.grid import process_grid
from src.core.extractor.processors.free_crop import process_free_crop
from src.core.extractor.processors.furniture import process_furniture
from src.core.extractor.processors.directory import process_directory


def create_mock_image(width=64, height=64):
    """Helper to generate a mocked Pillow Image with necessary attributes and context manager support."""
    img = MagicMock()
    img.width = width
    img.height = height
    img.size = (width, height)
    img.crop.return_value = MagicMock()
    # Support 'with Image.open(...) as img:' context manager pattern
    img.__enter__.return_value = img
    img.__exit__.return_value = None
    return img


# ---------------------------------------------------------
# Catalog Processor Tests
# ---------------------------------------------------------
@patch("src.core.extractor.processors.catalog.os.path.exists", return_value=True)
@patch("src.core.extractor.processors.catalog.os.makedirs")
@patch("src.core.extractor.processors.catalog.crop_tile")
@patch("src.core.extractor.processors.catalog.Image.open")
def test_process_catalog_success(mock_img_open, mock_crop_tile, mock_makedirs, mock_exists):
    """Verifies catalog processor reads JSON, prioritizes MenuSpriteIndex, and handles custom textures."""
    mock_img_open.return_value = create_mock_image(32, 32)
    mock_tile = MagicMock()
    mock_crop_tile.return_value = mock_tile

    config = {
        "file_path": "data/catalog.json",
        "meta": {
            "prefix": "O",
            "tile_width": 16,
            "tile_height": 16,
            "default_texture": "Maps/springobjects.xnb"
        }
    }

    mock_json_data = """
    {
        "items": {
            "1": {"MenuSpriteIndex": 0},
            "2": {"SpriteIndex": 1, "Texture": "custom_sheet"}
        }
    }
    """

    with patch("builtins.open", mock_open(read_data=mock_json_data)):
        count = process_catalog("/tmp_unpacked", config, "/cache")

    assert count == 2
    assert mock_img_open.call_count == 2
    assert mock_crop_tile.call_count == 2
    assert mock_tile.save.call_count == 2


@patch("src.core.extractor.processors.catalog.os.path.exists", return_value=True)
def test_process_catalog_missing_file(mock_exists):
    """Verifies catalog processor aborts safely if the JSON file is missing."""
    config = {"file_path": "missing.json", "meta": {}}
    
    with patch("builtins.open", side_effect=FileNotFoundError):
        count = process_catalog("/tmp_unpacked", config, "/cache")
        
    assert count == 0


@patch("src.core.extractor.processors.catalog.os.path.exists", return_value=True)
def test_process_catalog_empty_items(mock_exists):
    """Verifies catalog processor handles empty items dictionary."""
    config = {"file_path": "catalog.json", "meta": {}}
    with patch("builtins.open", mock_open(read_data='{"items": {}}')):
        count = process_catalog("/tmp_unpacked", config, "/cache")
    assert count == 0


# ---------------------------------------------------------
# Grid Processor Tests
# ---------------------------------------------------------
@patch("src.core.extractor.processors.grid.os.path.exists", return_value=True)
@patch("src.core.extractor.processors.grid.os.makedirs")
@patch("src.core.extractor.processors.grid.crop_tile")
@patch("src.core.extractor.processors.grid.Image.open")
def test_process_grid_success(mock_img_open, mock_crop_tile, mock_makedirs, mock_exists):
    """Verifies grid processor dynamically calculates columns and rows and extracts tiles."""
    mock_img_open.return_value = create_mock_image(32, 32)
    
    mock_tile = MagicMock()
    mock_tile.crop.return_value = mock_tile
    mock_crop_tile.return_value = mock_tile

    config = {
        "meta": {
            "source_xnb": "sheet.xnb",
            "prefix": "IMG",
            "tile_width": 16,
            "tile_height": 16,
            "crop_width": 14,
            "crop_height": 14
        }
    }

    count = process_grid("/tmp_unpacked", config, "/cache")

    assert count == 4
    assert mock_crop_tile.call_count == 4
    assert mock_tile.crop.call_count == 4
    assert mock_tile.save.call_count == 4


@patch("src.core.extractor.processors.grid.os.path.exists", return_value=False)
def test_process_grid_missing_sheet(mock_exists):
    """Verifies grid processor handles missing source spritesheet gracefully."""
    config = {"meta": {"source_xnb": "missing.xnb"}}
    count = process_grid("/tmp_unpacked", config, "/cache")
    assert count == 0


@patch("src.core.extractor.processors.grid.os.path.exists", return_value=True)
@patch("src.core.extractor.processors.grid.os.makedirs")
@patch("src.core.extractor.processors.grid.Image.open")
def test_process_grid_invalid_columns(mock_img_open, mock_makedirs, mock_exists):
    """Verifies grid processor handles zero or negative column calculations safely."""
    mock_img_open.return_value = create_mock_image(0, 32)
    config = {"meta": {"source_xnb": "sheet.xnb", "tile_width": 16}}
    
    count = process_grid("/tmp_unpacked", config, "/cache")
    assert count == 0


# ---------------------------------------------------------
# Free Crop Processor Tests
# ---------------------------------------------------------
@patch("src.core.extractor.processors.free_crop.os.path.exists", return_value=True)
@patch("src.core.extractor.processors.free_crop.os.makedirs")
@patch("src.core.extractor.processors.free_crop.Image.open")
def test_process_free_crop_success(mock_img_open, mock_makedirs, mock_exists):
    """Verifies free crop processor extracts elements using exact bounding boxes."""
    mock_img = create_mock_image(64, 64)
    mock_img_open.return_value = mock_img

    config = {
        "file_path": "elements.json",
        "meta": {
            "prefix": "CROP",
            "source_xnb": "ui.xnb"
        }
    }

    mock_json_data = '{"elements": {"elem1": [0, 0, 16, 16], "elem2": [16, 16, 32, 32]}}'

    with patch("builtins.open", mock_open(read_data=mock_json_data)):
        count = process_free_crop("/tmp_unpacked", config, "/cache")

    assert count == 2
    assert mock_img.crop.call_count == 2


@patch("src.core.extractor.processors.free_crop.os.path.exists", return_value=False)
def test_process_free_crop_missing_sheet(mock_exists):
    """Verifies free crop handles missing spritesheet."""
    config = {"file_path": "elements.json", "meta": {"source_xnb": "missing.xnb"}}
    count = process_free_crop("/tmp_unpacked", config, "/cache")
    assert count == 0


# ---------------------------------------------------------
# Furniture Processor Tests
# ---------------------------------------------------------
@patch("src.core.extractor.processors.furniture.os.path.exists", return_value=True)
@patch("src.core.extractor.processors.furniture.os.makedirs")
@patch("src.core.extractor.processors.furniture.Image.open")
def test_process_furniture_success(mock_img_open, mock_makedirs, mock_exists):
    """Verifies furniture processor handles flat and upright items with proper dimensions."""
    mock_img = create_mock_image(64, 64)
    mock_img_open.return_value = mock_img

    config = {
        "file_path": "furniture.json",
        "meta": {
            "prefix": "F",
            "source_xnb": "TileSheets/furniture.xnb"
        }
    }

    mock_json_data = """
    {
        "items": {
            "100": {"SpriteIndex": 0, "Width": 1, "Height": 1, "Type": "chair"},
            "101": {"SpriteIndex": 1, "Width": 2, "Height": 2, "Type": "rug"}
        }
    }
    """

    with patch("builtins.open", mock_open(read_data=mock_json_data)):
        count = process_furniture("/tmp_unpacked", config, "/cache")

    assert count == 2
    assert mock_img.crop.call_count == 2


@patch("src.core.extractor.processors.furniture.os.path.exists", return_value=False)
def test_process_furniture_missing_sheet(mock_exists):
    """Verifies furniture processor handles missing sheet."""
    config = {"file_path": "furniture.json", "meta": {"source_xnb": "missing.xnb"}}
    count = process_furniture("/tmp_unpacked", config, "/cache")
    assert count == 0


# ---------------------------------------------------------
# Directory Processor Tests
# ---------------------------------------------------------
@patch("src.core.extractor.processors.directory.os.path.exists")
@patch("src.core.extractor.processors.directory.os.makedirs")
@patch("src.core.extractor.processors.directory.Image.open")
def test_process_directory_success(mock_img_open, mock_makedirs, mock_exists):
    """Verifies directory processor extracts and crops individual files like portraits."""
    mock_exists.side_effect = lambda path: True
    mock_img = create_mock_image(64, 64)
    mock_img_open.return_value = mock_img

    config = {
        "file_path": "villagers.json",
        "meta": {
            "prefix": "portraits",
            "source_dir": "Portraits",
            "crop": [0, 0, 32, 32]
        }
    }

    mock_json_data = '{"villagers": {"Abigail": {}, "Sebastian": {}}}'

    with patch("builtins.open", mock_open(read_data=mock_json_data)):
        count = process_directory("/tmp_unpacked", config, "/cache")

    assert count == 2
    assert mock_img.crop.call_count == 2


@patch("src.core.extractor.processors.directory.os.path.exists", return_value=False)
def test_process_directory_missing_file(mock_exists):
    """Verifies directory processor handles missing meta prefix or files."""
    config = {"file_path": "villagers.json", "meta": {}}
    count = process_directory("/tmp_unpacked", config, "/cache")
    assert count == 0
    