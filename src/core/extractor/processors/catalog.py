import json
import logging
import os
from PIL import Image
from ..image_utils import crop_tile

logger = logging.getLogger(__name__)

def process_catalog(temp_unpacked_dir: str, config: dict, cache_dir: str) -> int:
    """Extracts item icons based on a JSON catalog mapping."""
    file_path = config["file_path"]
    meta = config["meta"]
    
    prefix = meta.get("prefix", "O")
    tile_w = meta.get("tile_width", 16)
    tile_h = meta.get("tile_height", 16)
    default_texture_xnb = meta.get("default_texture", "Maps/springobjects.xnb")

    # 1. Load the full JSON to access the items dictionary
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"[CatalogProcessor] Failed to read {file_path}: {e}")
        return 0

    items = data.get("items", {})
    if not items:
        logger.warning(f"[CatalogProcessor] No items found in {file_path}")
        return 0

    # 2. Lazy-load sheet caching mechanism
    loaded_sheets = {}
    
    # Resolve the default texture path properly against the nested structure
    default_texture_rel = default_texture_xnb.replace(".xnb", ".png").replace("\\", "/")
    default_sheet_path = os.path.join(temp_unpacked_dir, default_texture_rel)
    
    try:
        default_sheet = Image.open(default_sheet_path)
        loaded_sheets[default_texture_rel.lower()] = default_sheet
    except Exception as e:
        logger.warning(f"[CatalogProcessor] Default texture '{default_texture_rel}' missing in unpacked files: {e}")
        return 0

    # 3. Setup output directory
    out_dir = os.path.join(cache_dir, "img", prefix)
    os.makedirs(out_dir, exist_ok=True)
    
    count = 0
    missing_sheets_warned = set()

    # 4. Iterate and extract
    for item_key, item_data in items.items():
        if not isinstance(item_data, dict):
            continue
        
        sprite_index = item_data.get("SpriteIndex")
        if sprite_index is None or sprite_index < 0:
            continue

        # Handle custom texture overrides if they exist using lazy loading
        texture_path = item_data.get("Texture")
        if not texture_path:
            sheet_img = default_sheet
            sheet_name_for_log = default_texture_rel
        else:
            # Resolve the relative path and normalize it for dictionary caching
            tex_rel = texture_path.replace(".xnb", ".png").replace("\\", "/")
            
            # Catch extension-less texture references from the JSON
            if not tex_rel.lower().endswith(".png"):
                tex_rel += ".png"
                
            tex_key = tex_rel.lower()
            
            # Load custom sheet into cache if not already present
            if tex_key not in loaded_sheets:
                tex_path_full = os.path.join(temp_unpacked_dir, tex_rel)
                if os.path.exists(tex_path_full):
                    try:
                        loaded_sheets[tex_key] = Image.open(tex_path_full)
                    except Exception as e:
                        logger.error(f"[CatalogProcessor] Failed to open {tex_rel}: {e}")
            
            sheet_img = loaded_sheets.get(tex_key)
            if not sheet_img:
                if tex_rel not in missing_sheets_warned:
                    logger.warning(f"[CatalogProcessor] Required texture '{tex_rel}' not found. Falling back to default.")
                    missing_sheets_warned.add(tex_rel)
                sheet_img = default_sheet
                sheet_name_for_log = default_texture_rel
            else:
                sheet_name_for_log = tex_rel

        # Boundary Guarding: Prevent out-of-bounds crop calculations prior to extraction
        tiles_per_row = sheet_img.width // tile_w
        if tiles_per_row > 0:
            required_height = ((sprite_index // tiles_per_row) + 1) * tile_h
            if required_height > sheet_img.height:
                logger.warning(f"[CatalogProcessor] Skipping {item_key}: SpriteIndex {sprite_index} exceeds {sheet_name_for_log} boundaries.")
                continue

        # Crop and save
        tile = crop_tile(sheet_img, sprite_index, tile_w=tile_w, tile_h=tile_h)
        if tile:
            sprite_target = str(item_key)
            
            # Sanitize colons, slashes, and spaces for safe file saving on all platforms
            sprite_target = sprite_target.replace(":", "_").replace("/", "_").replace(" ", "_")

            out_filename = f"{prefix}_{sprite_target}.png"
            tile.save(os.path.join(out_dir, out_filename))
            count += 1

    logger.info(f"[CatalogProcessor] Extracted {count} items from {os.path.basename(file_path)} into {prefix}/ subfolder.")
    return count
    