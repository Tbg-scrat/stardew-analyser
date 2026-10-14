import os
import subprocess
from unittest.mock import patch
from PIL import Image

from src.core.extractor.orchestrator import extract_all_assets


@patch("src.core.extractor.orchestrator.is_cache_valid", return_value=True)
def test_extract_all_assets_skips_when_valid(mock_is_valid):
    assert extract_all_assets() is True


@patch("src.core.extractor.orchestrator.is_cache_valid", return_value=False)
def test_extract_all_assets_missing_content_dir(mock_is_valid, tmp_path):
    missing_dir = str(tmp_path / "non_existent")
    with patch("src.core.extractor.orchestrator.CONTENT_DIR", missing_dir):
        assert extract_all_assets() is False


@patch("src.core.extractor.orchestrator.is_cache_valid", return_value=False)
def test_extract_all_assets_success_flow(mock_is_valid, tmp_path):
    content_dir = tmp_path / "content"
    cache_dir = tmp_path / "cache"
    out_dir = str(cache_dir / "img" / "items")

    required_targets = [
        "Maps/springobjects.xnb",
        "TileSheets/Craftables.xnb",
        "TileSheets/tools.xnb",
        "LooseSprites/Cursors.xnb",
    ]
    for rel in required_targets:
        full = content_dir / rel
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text("xnb content")

    def mock_subprocess_run(cmd, capture_output, text, check):
        temp_unpacked = cmd[3]
        for sheet in ["springobjects.png", "Craftables.png", "tools.png", "Cursors.png"]:
            img = Image.new("RGBA", (32, 32), (255, 0, 0, 255))
            img.save(os.path.join(temp_unpacked, sheet))
        return subprocess.CompletedProcess(cmd, 0, stdout="Unpacked")

    with patch("src.core.extractor.orchestrator.CONTENT_DIR", str(content_dir)), \
         patch("src.core.extractor.orchestrator.CACHE_DIR", str(cache_dir)), \
         patch("src.core.extractor.processors.items.OUTPUT_IMG_DIR", out_dir), \
         patch("src.core.extractor.processors.spritesheets.OUTPUT_IMG_DIR", out_dir), \
         patch("src.core.extractor.orchestrator.save_cache_marker"), \
         patch("subprocess.run", side_effect=mock_subprocess_run):

        res = extract_all_assets()
        assert res is True
