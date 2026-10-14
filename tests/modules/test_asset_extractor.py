"""Compatibility test for src.core.asset_extractor legacy wrapper."""
from src.core.asset_extractor import extract_all_assets, is_cache_valid


def test_legacy_wrapper_imports():
    assert callable(extract_all_assets)
    assert callable(is_cache_valid)
