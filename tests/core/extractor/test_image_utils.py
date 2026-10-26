from PIL import Image

from src.core.extractor.image_utils import crop_tile, resolve_case_insensitive_path


def test_resolve_case_insensitive_path(tmp_path):
    base_dir = tmp_path / "Content"
    target_dir = base_dir / "TileSheets"
    target_dir.mkdir(parents=True)
    target_file = target_dir / "Tools.xnb"
    target_file.write_text("dummy")

    # Exact match
    res = resolve_case_insensitive_path(str(base_dir), "TileSheets/Tools.xnb")
    assert res == str(target_file)

    # Case insensitive match
    res_lower = resolve_case_insensitive_path(str(base_dir), "tilesheets/tools.xnb")
    assert res_lower == str(target_file)

    # Non-existent match
    res_none = resolve_case_insensitive_path(str(base_dir), "tilesheets/missing.xnb")
    assert res_none is None


def test_crop_tile():
    # 32x16 sheet -> 2 tiles of 16x16
    img = Image.new("RGBA", (32, 16), (255, 0, 0, 255))

    # Valid tile index 0
    tile0 = crop_tile(img, sprite_index=0, tile_w=16, tile_h=16)
    assert tile0 is not None
    assert tile0.size == (16, 16)

    # Valid tile index 1
    tile1 = crop_tile(img, sprite_index=1, tile_w=16, tile_h=16)
    assert tile1 is not None

    # Out-of-bounds tile index 2
    tile_oob = crop_tile(img, sprite_index=2, tile_w=16, tile_h=16)
    assert tile_oob is None
