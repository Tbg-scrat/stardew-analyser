import logging
import os
from PIL import Image

logger = logging.getLogger(__name__)


def resolve_case_insensitive_path(base_dir: str, rel_path: str) -> str | None:
    """Resolve a relative file path in a case-insensitive manner."""
    exact_path = os.path.join(base_dir, rel_path)
    if os.path.exists(exact_path):
        return exact_path

    # Filter out empty strings to prevent failure on consecutive/trailing slashes
    parts = [p for p in rel_path.replace("\\", "/").split("/") if p]
    curr = base_dir

    for part in parts:
        if not os.path.exists(curr) or not os.path.isdir(curr):
            return None
        entries = os.listdir(curr)
        match = next((e for e in entries if e.lower() == part.lower()), None)
        if match is None:
            return None
        curr = os.path.join(curr, match)

    return curr if os.path.exists(curr) else None


def crop_tile(
    sheet_img: Image.Image,
    sprite_index: int,
    tile_w: int = 16,
    tile_h: int = 16,
    tiles_per_row: int | None = None,
) -> Image.Image | None:
    """Crop a single tile from a spritesheet dynamically calculating tiles_per_row if not provided."""
    if tiles_per_row is None or tiles_per_row <= 0:
        tiles_per_row = sheet_img.width // tile_w

    if tiles_per_row == 0:
        return None

    col = sprite_index % tiles_per_row
    row = sprite_index // tiles_per_row

    crop_box = (col * tile_w, row * tile_h, (col + 1) * tile_w, (row + 1) * tile_h)

    if crop_box[2] > sheet_img.width or crop_box[3] > sheet_img.height:
        return None

    tile = sheet_img.crop(crop_box)
    
    # Retained: Returns None if the cropped tile is fully transparent
    return tile if tile.getbbox() else None
    