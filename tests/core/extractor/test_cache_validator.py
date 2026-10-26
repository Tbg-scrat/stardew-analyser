# tests/core/extractor/test_cache_validator.py

import json
from unittest.mock import mock_open, patch

from src.core.extractor.cache_validator import is_cache_valid, save_cache_manifest


@patch("src.core.extractor.cache_validator.os.path.exists")
def test_is_cache_valid_no_manifest(mock_exists):
    """Verifies cache is invalid if manifest file is missing."""
    # Return False only for the manifest file
    mock_exists.side_effect = lambda path: False if "extraction_manifest.json" in path else True
    assert is_cache_valid() is False


@patch("src.core.extractor.cache_validator.os.path.exists")
def test_is_cache_valid_no_img_dir(mock_exists):
    """Verifies cache is invalid if the target img directory is missing."""
    # Return True for manifest, False for the img directory
    mock_exists.side_effect = lambda path: False if path.endswith("img") else True
    assert is_cache_valid() is False


@patch("src.core.extractor.cache_validator.os.path.exists", return_value=True)
def test_is_cache_valid_empty_manifest(mock_exists):
    """Verifies cache is invalid if the manifest contains an empty files list."""
    manifest_data = '{"files": []}'
    with patch("builtins.open", mock_open(read_data=manifest_data)):
        assert is_cache_valid() is False


@patch("src.core.extractor.cache_validator.os.path.exists")
def test_is_cache_valid_missing_files(mock_exists):
    """Verifies cache is invalid if expected files from the manifest are missing on disk."""

    # Manifest and img dir exist, but the physical images do not
    def exists_side_effect(path):
        if path.endswith("extraction_manifest.json") or path.endswith("img"):
            return True
        return False

    mock_exists.side_effect = exists_side_effect

    manifest_data = '{"files": ["img/missing1.png", "img/missing2.png"]}'
    with patch("builtins.open", mock_open(read_data=manifest_data)):
        assert is_cache_valid() is False


@patch("src.core.extractor.cache_validator.os.path.exists", return_value=True)
def test_is_cache_valid_success(mock_exists):
    """Verifies cache is valid when manifest and all files exist."""
    manifest_data = '{"files": ["img/test1.png", "img/test2.png"]}'
    with patch("builtins.open", mock_open(read_data=manifest_data)):
        assert is_cache_valid() is True


@patch("src.core.extractor.cache_validator.os.path.exists", return_value=True)
def test_is_cache_valid_exception(mock_exists):
    """Verifies cache falls back to invalid if manifest reading throws an error."""
    with patch("builtins.open", side_effect=IOError("Permission denied")):
        assert is_cache_valid() is False


@patch("src.core.extractor.cache_validator.os.path.exists", return_value=True)
@patch("src.core.extractor.cache_validator.os.walk")
def test_save_cache_manifest(mock_walk, mock_exists):
    """Verifies the manifest generator correctly traverses the directory and writes JSON."""
    # Simulate finding directories and files during os.walk
    mock_walk.return_value = [
        ("/cache/img/objects", ("folders",), ("O_1.png", "O_2.png")),
        ("/cache/img/tools", (), ("axe.png",)),
    ]

    mock_file = mock_open()
    with patch("builtins.open", mock_file):
        save_cache_manifest()

    # Verify file was opened for writing
    mock_file.assert_called_once()
    handle = mock_file()

    # Capture what was dumped into the file
    written_data = "".join(call.args[0] for call in handle.write.call_args_list)
    saved_json = json.loads(written_data)

    assert "files" in saved_json
    assert saved_json["total_files"] == 3
