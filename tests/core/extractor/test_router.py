# tests/core/extractor/test_router.py

import pytest
from unittest.mock import patch, MagicMock, mock_open
import os
import json

from src.core.extractor.router import extract_assets, get_domain_configs


@patch("src.core.extractor.router.glob")
def test_get_domain_configs(mock_glob):
    """Verifies that the router correctly parses JSON files for _meta blocks."""
    mock_glob.return_value = ["data/mock1.json", "data/mock2.json"]
    
    # mock1 has a valid _meta block, mock2 is just random data
    mock_file_data = {
        "data/mock1.json": '{"_meta": {"processor": "grid"}}',
        "data/mock2.json": '{"some_key": "some_value"}'
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
    
    # Should bypass gracefully and return True without throwing an error
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
    """Verifies a full successful extraction dispatch loop."""
    # Setup mock configs to trigger the catalog processor
    mock_get_configs.return_value = [
        {
            "file_path": "data/mock.json",
            "meta": {
                "extract_images": True,
                "processor": "catalog",
                "default_texture": "Maps/springobjects.xnb"
            }
        }
    ]
    
    # Simulate finding the source asset on disk
    mock_resolve_path.return_value = "/content/Maps/springobjects.xnb"
    
    # Mock subprocess success for xnbcli
    mock_run.return_value = MagicMock(returncode=0)

    # We have to mock open() to prevent the router from trying to peek inside our fake mock.json
    with patch("builtins.open", mock_open(read_data='{"items": {}}')):
        result = extract_assets()

    # Verify the workflow completed successfully
    assert result is True
    
    # Verify the xnbcli unpack subprocess was called
    mock_run.assert_called_once()
    
    # Verify it dynamically routed to the correct processor based on the _meta block
    mock_process_catalog.assert_called_once()
    
    # Verify it saved the manifest
    mock_save_manifest.assert_called_once()
    
    # Verify cleanup occurred
    assert mock_rmtree.call_count == 2
