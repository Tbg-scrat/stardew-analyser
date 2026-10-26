# tests/core/extractor/test_router.py

import pytest
from unittest.mock import patch, MagicMock, mock_open
import os
import json

from src.core.extractor.router import extract_assets, get_domain_configs


@patch("src.core.extractor.router.glob")
def test_get_domain_configs(mock_glob):
    """Verifies that the router correctly parses JSON files for _meta blocks."""
    mock_glob.return_value = ["data/mock1.json", "data/mock2.json", "data/bad.json"]
    
    mock_file_data = {
        "data/mock1.json": '{"_meta": {"processor": "grid"}}',
        "data/mock2.json": '{"some_key": "some_value"}',
        "data/bad.json": 'invalid-json'
    }
    
    def side_effect(filename, *args, **kwargs):
        return mock_open(read_data=mock_file_data.get(filename, "{}"))()

    with patch("builtins.open", side_effect=side_effect):
        configs = get_domain_configs()
        
    assert len(configs) == 1
    assert configs[0]["file_path"] == "data/mock1.json"
    assert configs[0]["meta"]["processor"] == "grid"


@patch("src.core.extractor.router.is_cache_valid")
def test_extract_assets_cache_valid(mock_is_valid):
    """Verifies that extraction is skipped if the cache is already valid."""
    mock_is_valid.return_value = True
    assert extract_assets() is True


@patch("src.core.extractor.router.is_cache_valid")
@patch("src.core.extractor.router.os.path.exists")
def test_extract_assets_missing_content(mock_exists, mock_is_valid):
    """Verifies the graceful fallback when the /content directory is missing."""
    mock_is_valid.return_value = False
    mock_exists.return_value = False  # Simulates missing /content volume
    assert extract_assets() is True


@patch("src.core.extractor.router.is_cache_valid", return_value=False)
@patch("src.core.extractor.router.os.path.exists", return_value=True)
@patch("src.core.extractor.router.os.makedirs")
@patch("src.core.extractor.router.shutil.copy")
@patch("src.core.extractor.router.shutil.rmtree")
@patch("src.core.extractor.router.subprocess.run")
@patch("src.core.extractor.router.save_cache_manifest")
@patch("src.core.extractor.router.get_domain_configs")
@patch("src.core.extractor.router.process_catalog")
@patch("src.core.extractor.router.resolve_case_insensitive_path")
def test_extract_assets_full_run(
    mock_resolve_path, mock_process_catalog, mock_get_configs, mock_save_manifest,
    mock_run, mock_rmtree, mock_copy, mock_makedirs,
    mock_exists, mock_is_valid
):
    """Verifies a full successful extraction dispatch loop with catalog and directory processors."""
    mock_get_configs.return_value = [
        {
            "file_path": "data/mock.json",
            "meta": {
                "extract_images": True,
                "processor": "catalog",
                "default_texture": "Maps/springobjects.xnb",
                "source_dir": "Portraits"
            }
        },
        {
            "file_path": "data/unknown.json",
            "meta": {
                "extract_images": True,
                "processor": "unknown_processor"
            }
        }
    ]
    
    mock_resolve_path.return_value = "/content/Maps/springobjects.xnb"
    mock_run.return_value = MagicMock(returncode=0)

    catalog_json = '{"items": {"1": {"Texture": "custom_tex"}, "2": {}}}_'
    with patch("builtins.open", mock_open(read_data=catalog_json)), \
         patch("src.core.extractor.router.os.listdir", return_value=["Abigail.xnb"]), \
         patch("src.core.extractor.router.os.path.isdir", return_value=True):
        result = extract_assets()

    assert result is True
    mock_run.assert_called_once()
    mock_process_catalog.assert_called_once()
    mock_save_manifest.assert_called_once()


@patch("src.core.extractor.router.is_cache_valid", return_value=False)
@patch("src.core.extractor.router.os.path.exists", return_value=True)
@patch("src.core.extractor.router.os.makedirs")
@patch("src.core.extractor.router.get_domain_configs", side_effect=Exception("Disk error"))
def test_extract_assets_exception_handling(mock_makedirs, mock_get_configs, mock_exists, mock_is_valid):
    """Verifies extraction workflow catches exceptions gracefully and returns False."""
    result = extract_assets()
    assert result is False
    