import json
import os
from unittest.mock import patch
from PIL import Image

from src.core.extractor.processors.items import extract_objects_from_catalog
from src.core.extractor.processors.spritesheets import extract_quality_stars, slice_spritesheet


def test_slice_spritesheet(tmp_path):
    cache_dir = tmp_path / "cache"
    out_dir = cache_dir / "img" / "items"
    out_dir.mkdir(parents=True)

    sheet_path = tmp_path / "test_sheet.png"
    img = Image.new("RGBA", (32, 16), (255, 0, 0, 255))
    img.save(sheet_path)

    with patch("src.core.extractor.processors.spritesheets.OUTPUT_IMG_DIR", str(out_dir)):
        count = slice_spritesheet(str(sheet_path), prefix="T", tile_w=16, tile_h=16, tiles_per_row=2)
        assert count == 2
        assert os.path.exists(os.path.join(out_dir, "T_0.png"))
        assert os.path.exists(os.path.join(out_dir, "T_1.png"))


def test_extract_quality_stars(tmp_path):
    out_dir = tmp_path / "img" / "items"
    out_dir.mkdir(parents=True)
    cursors_path = tmp_path / "Cursors.png"

    img = Image.new("RGBA", (500, 500), (0, 255, 0, 255))
    img.save(cursors_path)

    with patch("src.core.extractor.processors.spritesheets.OUTPUT_IMG_DIR", str(out_dir)):
        res = extract_quality_stars(str(cursors_path))
        assert res is True
        assert os.path.exists(os.path.join(out_dir, "silver_star.png"))
        assert os.path.exists(os.path.join(out_dir, "gold_star.png"))
        assert os.path.exists(os.path.join(out_dir, "iridium_star.png"))


def test_extract_quality_stars_missing_file():
    res = extract_quality_stars("non_existent_cursors.png")
    assert res is False


def test_extract_objects_from_catalog(tmp_path):
    unpacked_dir = tmp_path / "unpacked"
    unpacked_dir.mkdir()
    out_dir = tmp_path / "img" / "items"
    out_dir.mkdir(parents=True)

    objects_data = {
        "StardropTea": {
            "Name": "Stardrop Tea",
            "Texture": "TileSheets\\Objects_2",
            "SpriteIndex": 0
        }
    }
    json_path = tmp_path / "objects.json"
    json_path.write_text(json.dumps(objects_data), encoding="utf-8")

    # Create default springobjects and Objects_2 pngs
    default_sheet = Image.new("RGBA", (16, 16), (255, 0, 0, 255))
    default_sheet.save(unpacked_dir / "springobjects.png")

    objects2_sheet = Image.new("RGBA", (16, 16), (0, 255, 0, 255))
    objects2_sheet.save(unpacked_dir / "objects_2.png")

    with patch("src.core.extractor.processors.items.OUTPUT_IMG_DIR", str(out_dir)), \
         patch("src.core.extractor.processors.items.OBJECTS_JSON_PATH", str(json_path)):
        count = extract_objects_from_catalog(str(unpacked_dir))
        assert count == 1
        assert os.path.exists(os.path.join(out_dir, "O_StardropTea.png"))
