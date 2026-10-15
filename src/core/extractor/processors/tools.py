import json
import logging
import os
from PIL import Image
from ..image_utils import crop_tile

logger = logging.getLogger(__name__)

CACHE_DIR = os.getenv("CACHE_DIR", "/cache")
OUTPUT_IMG_DIR = os.path.join(CACHE_DIR, "img", "tools")
TOOLS_JSON_PATH = os.path.join("data", "tools.json")


def extract_tools_from_catalog(temp_unpacked_dir: str) -> int:
    """Parse tools.json manifest and extract tool icons using MenuSpriteIndex/SpriteIndex."""
    json_path = TOOLS_JSON_PATH
    if not os.path.exists(json_path):
        alt_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "tools.json")
        if os.path.exists(alt_path):
            json_path = alt_path
        else:
            logger.warning(f"[AssetExtractor] Tools manifest missing at {TOOLS_JSON_PATH}.")
            return 0

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            tools_data = json.load(f)
    except Exception as e:
        logger.error(f"[AssetExtractor] Failed reading {json_path}: {e}")
        return 0

    tools_sheet_path = os.path.join(temp_unpacked_dir, "TileSheets", "tools.png")
    if not os.path.exists(tools_sheet_path):
        tools_sheet_path = os.path.join(temp_unpacked_dir, "tools.png")

    if not os.path.exists(tools_sheet_path):
        logger.warning(f"[AssetExtractor] tools.png missing in unpacked files at {temp_unpacked_dir}")
        return 0

    try:
        tools_sheet = Image.open(tools_sheet_path)
    except Exception as e:
        logger.error(f"[AssetExtractor] Failed opening tools sheet {tools_sheet_path}: {e}")
        return 0

    out_dir = globals().get("OUTPUT_IMG_DIR")
    if not out_dir or out_dir == os.path.join("/cache", "img", "tools"):
        cache_dir = os.getenv("CACHE_DIR")
        if (not cache_dir or cache_dir == "/cache") and os.path.basename(temp_unpacked_dir) == "_tmp_unpacked":
            cache_dir = os.path.dirname(temp_unpacked_dir)
        else:
            cache_dir = cache_dir or "/cache"
        out_dir = os.path.join(cache_dir, "img", "tools")

    os.makedirs(out_dir, exist_ok=True)
    count = 0

    for tool_key, tool_data in tools_data.items():
        if not isinstance(tool_data, dict):
            continue

        menu_idx = tool_data.get("MenuSpriteIndex", -1)
        sprite_idx = tool_data.get("SpriteIndex", -1)

        target_idx = menu_idx if menu_idx >= 0 else sprite_idx
        if target_idx < 0:
            continue

        tile = crop_tile(tools_sheet, target_idx, tile_w=16, tile_h=16)
        if tile:
            out_filename = f"{tool_key}.png"
            tile.save(os.path.join(out_dir, out_filename))
            count += 1

    logger.info(f"[AssetExtractor] Extracted {count} tool icons into {out_dir}")
    return count
